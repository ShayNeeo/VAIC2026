"""Facade for building and querying the V2 product knowledge index."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from app.config import settings
from app.data_catalog.registry import require_serving_approval
from app.knowledge.index import PersistentHybridIndex
from app.knowledge.ingestion import load_product_chunks
from app.knowledge.models import IngestReport, RetrievalHit
from app.knowledge.rag_provider import (
    CircuitBreaker, RagProviderRouter, SearchOutcome, compute_health, make_async_bridge,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRODUCTS = ROOT / "data" / "synthetic" / "v2" / "products.json"
DEFAULT_SOURCE_CARD = ROOT / "data" / "catalog" / "source_cards" / "synthetic_product_catalog.json"

_logger = logging.getLogger(__name__)


class ProductKnowledgeService:
    def __init__(self, index_path: str | Path | None = None) -> None:
        path = index_path or (Path(settings.VECTOR_DB_DIR) / "v2_products.sqlite3")
        self.index = PersistentHybridIndex(path)
        self._circuit = CircuitBreaker(
            failure_threshold=settings.RAG_MCP_FAILURE_THRESHOLD,
            cooldown_seconds=settings.RAG_MCP_COOLDOWN_SECONDS,
            half_open_max_calls=settings.RAG_MCP_HALF_OPEN_MAX_CALLS,
        )
        # One router (and its one executor) for the lifetime of this
        # service instance -- not recreated per search() call. See
        # RagProviderRouter.__init__ for why a per-call executor would leak.
        self._router: RagProviderRouter[List[RetrievalHit]] = RagProviderRouter(
            name="product",
            mode=settings.RAG_PROVIDER,
            timeout_seconds=settings.RAG_MCP_REQUEST_TIMEOUT_SECONDS,
            circuit_breaker=self._circuit,
            logger=_logger,
            warning_cooldown_seconds=settings.RAG_MCP_WARNING_COOLDOWN_SECONDS,
            metrics_prefix="rag.product",
        )
        # Last provider-routing outcome, for callers/tests that want to
        # inspect provider_used/fallback_used without changing the public
        # List[RetrievalHit] return type of search().
        self.last_search_outcome: Optional[SearchOutcome[List[RetrievalHit]]] = None

    def ingest(
        self,
        source_path: str | Path = DEFAULT_PRODUCTS,
        source_card_path: str | Path = DEFAULT_SOURCE_CARD,
    ) -> IngestReport:
        require_serving_approval(source_card_path)
        chunks, report = load_product_chunks(source_path)
        self.index.upsert(chunks, source_hash=report.source_hash, dataset_version=report.dataset_version)
        return report

    def ensure_index(self) -> None:
        if self.index.count() == 0:
            self.ingest()

    def rag_health(self) -> Dict[str, Any]:
        health = compute_health(settings.RAG_PROVIDER, self._circuit)
        return {"status": health.status, "mode": settings.RAG_PROVIDER, "error_code": health.error_code}

    def search(
        self,
        query: str,
        *,
        branch: str,
        segment: Optional[str] = None,
        product_ids: Optional[Sequence[str]] = None,
        top_k: int = 5,
    ) -> List[RetrievalHit]:
        def _local_search() -> List[RetrievalHit]:
            self.ensure_index()
            return self.index.search(
                query,
                branch=branch,
                segment=segment,
                product_ids=product_ids,
                top_k=top_k,
            )

        mcp_search = None
        if settings.RAG_PROVIDER in {"mcp", "hybrid"}:
            mcp_search = make_async_bridge(
                lambda: self._mcp_search_coro(query, branch=branch, product_ids=product_ids, top_k=top_k)
            )

        outcome = self._router.search(local_search=_local_search, mcp_search=mcp_search)
        self.last_search_outcome = outcome
        return outcome.hits

    async def _mcp_search_coro(
        self,
        query: str,
        *,
        branch: str,
        product_ids: Optional[Sequence[str]],
        top_k: int,
    ) -> List[RetrievalHit]:
        from services.rag_mcp.client import RagMCPClient
        from services.rag_mcp.config import RagMCPSettings
        from services.rag_mcp.schemas import SearchKnowledgeRequest, CallerPrincipal

        mcp_settings = RagMCPSettings(
            url=settings.RAG_MCP_PRODUCT_URL,
            service_token=settings.RAG_MCP_PRODUCT_TOKEN,
            require_auth=True,
        )
        async with RagMCPClient(mcp_settings) as client:
            principal = CallerPrincipal(employee_id="SYSTEM", branch=branch, roles=["ProductExpert"])
            req = SearchKnowledgeRequest(
                query=query,
                principal=principal,
                filters={"product_ids": list(product_ids) if product_ids else []},
                top_k=top_k,
            )
            resp = await client.search(req)

            from app.knowledge.models import ProductChunk

            hits: List[RetrievalHit] = []
            for chunk in resp.chunks:
                hits.append(
                    RetrievalHit(
                        chunk=ProductChunk(
                            document_id=chunk.citation.document_id,
                            document_version=chunk.citation.document_version,
                            section_path=chunk.citation.section_path,
                            text=chunk.text,
                            product_id=chunk.product_id or "",
                            chunk_type=chunk.chunk_type,
                            branches=chunk.citation.branches or [],
                        ),
                        score=chunk.score,
                    )
                )
            return hits

    def keyword_search(self, query: str, *, top_k: int = 5) -> List[RetrievalHit]:
        """Deterministic, embedding-free fallback used when vector retrieval
        yields no hits (e.g. the key-free ``local`` provider on a small corpus,
        or an empty/degraded index). Matches diacritic-folded query tokens
        against chunk text so a grounded recommendation still surfaces offline.
        """
        from app.knowledge.index import fold, tokens

        query_tokens = tokens(query)
        if not query_tokens:
            return []
        q = fold(query)
        hits: List[RetrievalHit] = []
        with self.index._connect() as connection:
            rows = connection.execute("SELECT payload FROM knowledge_chunks").fetchall()
        for row in rows:
            chunk = __import__("app.knowledge.models", fromlist=["KnowledgeChunk"]).KnowledgeChunk.model_validate_json(row["payload"])
            if not chunk.active:
                continue
            text = fold(chunk.text)
            matched = sum(1 for t in query_tokens if t in text)
            if matched == 0:
                continue
            score = matched / max(1, len(query_tokens))
            hits.append(RetrievalHit(chunk=chunk, score=max(0.21, min(0.6, score)), dense_score=0.0, sparse_score=max(0.21, min(0.6, score))))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]

    @staticmethod
    def evidence(hit: RetrievalHit) -> Dict[str, Any]:
        chunk = hit.chunk
        return {
            "claim_id": f"EVID-{chunk.chunk_id[:8]}",
            "module": "Product",
            "claim": f"Found reference for {chunk.product_id}",
            "source_document_id": chunk.document_id,
            "source_version": chunk.document_version,
            "location": chunk.section_path,
            "quote": chunk.text,
            "product_id": chunk.product_id,
            "retrieval_score": hit.score,
            "is_valid": True,
            "validation_score": round(hit.score, 4),
            "human_review_allowed": False,
        }
