"""Credit-policy retrieval with a dedicated MCP identity/profile."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.data_catalog.registry import require_serving_approval
from app.knowledge.index import EmbeddingProvider, LocalEmbedding
from app.knowledge.legal_service import LegalKnowledgeService, ROOT
from app.knowledge.models import KnowledgeChunk, RetrievalHit
from app.knowledge.retrieval_contracts import AuthorityTier, VerificationStatus


DEFAULT_CREDIT_POLICY = ROOT / "data" / "legal" / "policies" / "shb_credit_policy_manual.json"
DEFAULT_CREDIT_SOURCE_CARD = ROOT / "data" / "catalog" / "source_cards" / "synthetic_credit_reference_pack.json"


class CreditKnowledgeService(LegalKnowledgeService):
    def __init__(
        self,
        index_path: str | Path | None = None,
        *,
        provider: Optional[EmbeddingProvider] = None,
    ) -> None:
        path = index_path or (Path(settings.VECTOR_DB_DIR) / "v2_credit.sqlite3")
        # Keep local fallback deterministic; MCP/hybrid routing still occurs
        # in the inherited search() implementation.
        super().__init__(path, provider=provider or LocalEmbedding())

    def ingest(
        self,
        rules_path: str | Path = DEFAULT_CREDIT_POLICY,
        source_card_path: str | Path = DEFAULT_CREDIT_SOURCE_CARD,
    ) -> int:
        require_serving_approval(source_card_path)
        source = Path(rules_path)
        raw = source.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        chunks: List[KnowledgeChunk] = []
        effective_from = date.fromisoformat(str(payload["effective_from"]))
        effective_to = date.fromisoformat(payload["effective_to"]) if payload.get("effective_to") else None
        for chapter in payload.get("chapters", []):
            for article in chapter.get("articles", []):
                article_id = str(article.get("article_id"))
                text = " | ".join(
                    str(value)
                    for value in (
                        payload.get("title"),
                        chapter.get("title"),
                        article_id,
                        article.get("title"),
                        article.get("text"),
                    )
                    if value
                )
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=f"credit:{payload['document_id']}:{article_id}",
                        document_id=str(payload["document_id"]),
                        document_version=str(payload["version"]),
                        product_id="PROD-WORKING-CAPITAL",
                        section_path=f"{chapter.get('chapter_id')} / {article_id}",
                        chunk_type="credit_policy_article",
                        text=text,
                        effective_from=effective_from,
                        effective_to=effective_to,
                        active=str(payload.get("status", "active")) == "active",
                        segments=["SME", "CORPORATE"],
                        access_scope={"branches": ["*"]},
                        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        source_type="credit_policy",
                        authority_tier=AuthorityTier.TIER_2_VERIFIED_INTERNAL,
                        verification_status=VerificationStatus.VERIFIED,
                        security_classification="RESTRICTED",
                    )
                )
        return self.index.upsert(
            chunks,
            source_hash=hashlib.sha256(raw).hexdigest(),
            dataset_version=str(payload["version"]),
        )

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

        runtime = RagMCPSettings(
            url=settings.RAG_MCP_CREDIT_URL,
            service_token=settings.RAG_MCP_CREDIT_TOKEN,
            require_auth=True,
        )
        principal = CallerPrincipal(
            employee_id="SYSTEM-CREDIT",
            branch=branch,
            agent_type="CreditExpert",
            agent_instance_id="credit-expert-runtime-v1",
            roles=["CreditExpert"],
            permissions=["knowledge:credit:read"],
        )
        request = ExpertSearchRequest(
            query=query,
            principal=principal,
            filters=ScopedSearchFilters(product_ids=["PRD-WC-001"] if product_id else []),
            top_k=top_k,
            trace_id=f"TRACE-CREDIT-{hashlib.sha256(query.encode('utf-8')).hexdigest()[:12]}",
        )
        async with RagMCPClient(runtime) as client:
            response = await client.expert_search("credit_search", request)
        return [
            RetrievalHit(
                chunk=KnowledgeChunk(
                    chunk_id=item.chunk_id,
                    document_id=item.citation.document_id,
                    document_version=item.citation.document_version,
                    product_id="PROD-WORKING-CAPITAL",
                    section_path=item.citation.section_path,
                    chunk_type=item.chunk_type,
                    text=item.text,
                    effective_from=item.effective_from,
                    effective_to=item.effective_to,
                    active=True,
                    segments=item.segments,
                    access_scope={"branches": [branch]},
                    content_hash=item.citation.content_hash,
                    source_type="credit_mcp",
                    authority_tier=AuthorityTier.TIER_2_VERIFIED_INTERNAL,
                    verification_status=VerificationStatus.VERIFIED,
                    security_classification="RESTRICTED",
                ),
                score=item.score,
                dense_score=item.dense_score,
                sparse_score=item.sparse_score,
            )
            for item in response.chunks
        ]

