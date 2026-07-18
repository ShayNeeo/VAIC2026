"""Persistent legal retrieval over governed, versioned rule evidence."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.data_catalog.registry import require_serving_approval
from app.knowledge.index import PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk, RetrievalHit
from app.knowledge.rag_provider import (
    CircuitBreaker, RagProviderRouter, SearchOutcome, compute_health, make_async_bridge,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICIES = ROOT / "data" / "synthetic" / "v2" / "b2b_policies.json"
DEFAULT_SOURCE_CARD = ROOT / "data" / "catalog" / "source_cards" / "synthetic_b2b_policies.json"

_logger = logging.getLogger(__name__)


class LegalKnowledgeService:
    """Legal RAG supports evidence/explanation; it never owns eligibility outcome."""

    def __init__(self, index_path: str | Path | None = None) -> None:
        path = index_path or (Path(settings.VECTOR_DB_DIR) / "v2_legal.sqlite3")
        self.index = PersistentHybridIndex(path)
        self._circuit = CircuitBreaker(
            failure_threshold=settings.RAG_MCP_FAILURE_THRESHOLD,
            cooldown_seconds=settings.RAG_MCP_COOLDOWN_SECONDS,
            half_open_max_calls=settings.RAG_MCP_HALF_OPEN_MAX_CALLS,
        )
        self._router: RagProviderRouter[List[RetrievalHit]] = RagProviderRouter(
            name="legal",
            mode=settings.RAG_PROVIDER,
            timeout_seconds=settings.RAG_MCP_REQUEST_TIMEOUT_SECONDS,
            circuit_breaker=self._circuit,
            logger=_logger,
            warning_cooldown_seconds=settings.RAG_MCP_WARNING_COOLDOWN_SECONDS,
            metrics_prefix="rag.legal",
        )
        self.last_search_outcome: Optional[SearchOutcome[List[RetrievalHit]]] = None

    def ingest(
        self,
        rules_path: str | Path = DEFAULT_POLICIES,
        source_card_path: str | Path = DEFAULT_SOURCE_CARD,
    ) -> int:
        require_serving_approval(source_card_path)
        source = Path(rules_path)
        raw = source.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        chunks: List[KnowledgeChunk] = []
        for policy in payload["policies"]:
            if not policy["active"] or policy.get("synthetic") is not True:
                continue
            for section in policy["sections"]:
                text = " | ".join([policy["policy_id"], policy["title"], section["title"], section["summary"], f"Nội dung nguồn: {section['source_quote']}"])
                scopes = section.get("product_ids", policy["product_ids"])
                for scope in scopes:
                    chunk_id = f"{policy['policy_id']}:{policy['document_version']}:{section['section_id']}:{scope}"
                    chunks.append(
                        KnowledgeChunk(
                            chunk_id=chunk_id,
                            document_id=policy["document_id"],
                            document_version=policy["document_version"],
                            product_id=scope,
                            section_path=section["section_id"],
                            chunk_type="b2b_policy",
                            text=text,
                            effective_from=policy["effective_from"],
                            effective_to=policy["effective_to"],
                            active=True,
                            segments=[],
                            access_scope=policy["access_scope"],
                            content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        )
                    )
        source_hash = hashlib.sha256(raw).hexdigest()
        self.index.prune(
            chunk_types={"legal_rule", "b2b_policy"},
            keep_chunk_ids={chunk.chunk_id for chunk in chunks},
        )
        return self.index.upsert(
            chunks,
            source_hash=source_hash,
            dataset_version=str(payload["dataset_version"]),
        )

    def ensure_index(self) -> None:
        # Upsert is source-hash idempotent and also refreshes an existing
        # local index when the versioned policy pack changes.
        self.ingest()

    def rag_health(self) -> dict:
        health = compute_health(settings.RAG_PROVIDER, self._circuit)
        return {"status": health.status, "mode": settings.RAG_PROVIDER, "error_code": health.error_code}

    def search(
        self,
        query: str,
        *,
        branch: str,
        product_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[RetrievalHit]:
        def _local_search() -> List[RetrievalHit]:
            self.ensure_index()
            scopes = ["*", product_id] if product_id else None
            return self.index.search(
                query,
                branch=branch,
                product_ids=scopes,
                top_k=top_k,
                threshold=0.12,
            )

        mcp_search = None
        if settings.RAG_PROVIDER in {"mcp", "hybrid"}:
            mcp_search = make_async_bridge(
                lambda: self._mcp_search_coro(query, branch=branch, product_id=product_id, top_k=top_k)
            )

        outcome = self._router.search(local_search=_local_search, mcp_search=mcp_search)
        self.last_search_outcome = outcome
        return outcome.hits

    async def _mcp_search_coro(
        self,
        query: str,
        *,
        branch: str,
        product_id: Optional[str],
        top_k: int,
    ) -> List[RetrievalHit]:
        from services.rag_mcp.client import RagMCPClient
        from services.rag_mcp.config import RagMCPSettings
        from services.rag_mcp.schemas import SearchKnowledgeRequest, CallerPrincipal

        mcp_settings = RagMCPSettings(
            url=settings.RAG_MCP_LEGAL_URL,
            service_token=settings.RAG_MCP_LEGAL_TOKEN,
            require_auth=True,
        )
        async with RagMCPClient(mcp_settings) as client:
            principal = CallerPrincipal(employee_id="SYSTEM", branch=branch, roles=["LegalExpert"])
            req = SearchKnowledgeRequest(
                query=query,
                principal=principal,
                filters={"product_ids": [product_id] if product_id else []},
                top_k=top_k,
            )
            resp = await client.search(req)

            hits: List[RetrievalHit] = []
            for chunk in resp.chunks:
                hits.append(
                    RetrievalHit(
                        chunk=KnowledgeChunk(
                            chunk_id=chunk.chunk_id,
                            document_id=chunk.citation.document_id,
                            document_version=chunk.citation.document_version,
                            section_path=chunk.citation.section_path,
                            text=chunk.text,
                            product_id=chunk.product_id or "",
                            chunk_type=chunk.chunk_type,
                            active=True,
                            effective_from=chunk.effective_from,
                            effective_to=chunk.effective_to,
                            content_hash="",
                            segments=[],
                            access_scope={"branches": chunk.citation.branches or ["*"]},
                        ),
                        score=chunk.score,
                    )
                )
            return hits
