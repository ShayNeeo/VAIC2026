"""Persistent legal retrieval over governed, versioned rule evidence."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.data_catalog.registry import require_serving_approval
from app.knowledge.index import EmbeddingProvider, PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk, RetrievalHit
from app.knowledge.rag_provider import (
    CircuitBreaker, RagProviderRouter, SearchOutcome, compute_health, make_async_bridge,
)
from app.knowledge.retrieval_contracts import AuthorityTier, VerificationStatus


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES = ROOT / "data" / "synthetic" / "v2" / "eligibility_rules.json"
DEFAULT_SOURCE_CARD = ROOT / "data" / "catalog" / "source_cards" / "synthetic_legal_knowledge.json"

_logger = logging.getLogger(__name__)


class LegalKnowledgeService:
    """Legal RAG supports evidence/explanation; it never owns eligibility outcome."""

    def __init__(self, index_path: str | Path | None = None, *, provider: Optional[EmbeddingProvider] = None) -> None:
        # Phase 2 addition: without an explicit provider=, PersistentHybridIndex
        # falls back to create_embedding_provider() -- this repo's real .env
        # sets KNOWLEDGE_EMBEDDING_PROVIDER=openai, which makes a genuine
        # network call AND writes to the single SHARED
        # data/vector_db/openai_vector_cache.json file on every embed(),
        # regardless of index_path. Discovered when benchmarks/run_retrieval_benchmark.py
        # hit a real OSError writing that shared file (plausibly a concurrent
        # write from the other agent active in this repo during this Phase --
        # see AI_LOG.md). Tests/benchmarks that don't need real semantic
        # embeddings should pass provider=LocalEmbedding() explicitly to stay
        # deterministic, fast, and isolated from that shared file; production
        # callers that omit provider= keep today's exact behavior.
        path = index_path or (Path(settings.VECTOR_DB_DIR) / "v2_legal.sqlite3")
        self.index = PersistentHybridIndex(path, provider=provider)
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
        rules_path: str | Path = DEFAULT_RULES,
        source_card_path: str | Path = DEFAULT_SOURCE_CARD,
    ) -> int:
        require_serving_approval(source_card_path)
        source = Path(rules_path)
        raw = source.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        chunks: List[KnowledgeChunk] = []
        for rule in payload["rules"]:
            text = " | ".join(
                [
                    rule["rule_id"],
                    f"Mã lỗi: {rule['failure_code']}",
                    f"Trường kiểm tra: {rule['field']}",
                    f"Nội dung nguồn: {rule['source_quote']}",
                ]
            )
            for scope in rule["scope"]:
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=f"{rule['rule_id']}:{rule['version']}:{scope}",
                        document_id=rule["source_document_id"],
                        document_version=rule["source_version"],
                        product_id=scope,
                        section_path=rule["source_location"],
                        chunk_type="legal_rule",
                        text=text,
                        effective_from=rule["effective_from"],
                        effective_to=rule["effective_to"],
                        active=True,
                        segments=[],
                        access_scope=rule.get("access_scope", {"branches": ["*"]}),
                        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        # Phase 2: this rule set is only ever ingested after
                        # require_serving_approval() passes (see call above)
                        # against a versioned, governed source card -- that
                        # governance gate is exactly what TIER_2_VERIFIED_INTERNAL
                        # / VERIFIED mean here. Not TIER_1_AUTHORITATIVE: this
                        # repo has no distinct "regulator/legal-authored
                        # original text" tier above "internally verified and
                        # approved for serving" to draw that line against.
                        source_type="eligibility_rule",
                        authority_tier=AuthorityTier.TIER_2_VERIFIED_INTERNAL,
                        verification_status=VerificationStatus.VERIFIED,
                    )
                )
        source_hash = hashlib.sha256(raw).hexdigest()
        return self.index.upsert(
            chunks,
            source_hash=source_hash,
            dataset_version=str(payload["registry_version"]),
        )

    def ingest_v3_banking_documents(self, documents_path: str | Path) -> int:
        """Ingest V3 synthetic banking policy documents (banking_policy_documents.json).

        These documents contain the full policy text from which V3 rule source_quotes
        are drawn. EvidenceValidator.validate_claim() performs a normalized substring
        match of the source_quote against chunk text -- this ingestion path stores the
        full document text as chunks indexed under SYNTH-DOC-* document IDs, so every
        V3 rule's source_quote resolves to a real chunk during validation.

        This is the V3 analogue of the V2 ingest() path, which stores source_quote
        verbatim inside a compound chunk text. Here we store the full document text so
        a wider set of sub-phrases can be found (allowing multiple rules from the same
        document to validate against one chunk).
        """
        source = Path(documents_path)
        raw = source.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        chunks: List[KnowledgeChunk] = []
        dataset_version = str(payload.get("dataset_version", "v3"))
        for doc in payload.get("documents", []):
            from datetime import date
            eff_from = doc.get("effective_from", "2026-01-01")
            eff_from_date = date.fromisoformat(eff_from) if isinstance(eff_from, str) else eff_from
            eff_to_raw = doc.get("effective_to")
            eff_to_date = date.fromisoformat(eff_to_raw) if isinstance(eff_to_raw, str) else eff_to_raw
            text = doc["text"]
            chunk_id = f"{doc['document_id']}:{doc['document_version']}"
            chunks.append(
                KnowledgeChunk(
                    chunk_id=chunk_id,
                    document_id=doc["document_id"],
                    document_version=doc["document_version"],
                    product_id="*",  # policy docs apply across products
                    section_path=doc.get("section", "1"),
                    chunk_type="banking_policy_document",
                    text=text,
                    effective_from=eff_from_date,
                    effective_to=eff_to_date,
                    active=doc.get("active", True),
                    segments=doc.get("segments", ["CORPORATE", "SME"]),
                    access_scope=doc.get("access_scope", {"branches": ["*"]}),
                    content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    source_type="banking_policy_document",
                    authority_tier=AuthorityTier.TIER_2_VERIFIED_INTERNAL,
                    verification_status=VerificationStatus.VERIFIED,
                )
            )
        source_hash = hashlib.sha256(raw).hexdigest()
        return self.index.upsert(chunks, source_hash=source_hash, dataset_version=dataset_version)

    def ensure_index(self) -> None:
        if self.index.count() == 0:
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
        from services.rag_mcp.schemas import CallerPrincipal, ExpertSearchRequest, ScopedSearchFilters

        mcp_settings = RagMCPSettings(
            url=settings.RAG_MCP_LEGAL_URL,
            service_token=settings.RAG_MCP_LEGAL_TOKEN,
            require_auth=True,
        )
        async with RagMCPClient(mcp_settings) as client:
            principal = CallerPrincipal(
                employee_id="SYSTEM-LEGAL",
                branch=branch,
                agent_type="LegalExpert",
                agent_instance_id="legal-expert-runtime-v1",
                roles=["LegalExpert"],
                permissions=["knowledge:legal:read"],
            )
            req = ExpertSearchRequest(
                query=query,
                principal=principal,
                filters=ScopedSearchFilters(product_ids=[product_id] if product_id else []),
                top_k=top_k,
                trace_id=f"TRACE-LEGAL-{hashlib.sha256(query.encode('utf-8')).hexdigest()[:12]}",
            )
            resp = await client.expert_search("legal_search", req)

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
                            content_hash=chunk.citation.content_hash,
                            segments=[],
                            access_scope={"branches": chunk.citation.branches or ["*"]},
                        ),
                        score=chunk.score,
                        dense_score=chunk.dense_score,
                        sparse_score=chunk.sparse_score,
                    )
                )
            return hits
