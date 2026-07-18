"""Standalone reference-document library -- deliberately NOT a subclass of
LegalKnowledgeService/ProductKnowledgeService and NOT registered on any
AgentToolGateway. Content here (auto-generated example outputs, illustrative
templates) must never be citable as grounded product/credit/insurance/
eligibility evidence -- see the source card's prohibited_uses. This service
only supports manual search/browse for RM/specialist workspace tooling."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.data_catalog.registry import require_serving_approval
from app.knowledge.index import EmbeddingProvider, LocalEmbedding, PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk, RetrievalHit
from app.knowledge.parsers import parse_document
from app.knowledge.retrieval_contracts import AuthorityTier, VerificationStatus

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_CARD = ROOT / "data" / "catalog" / "source_cards" / "synthetic_credit_proposal_reference.json"


class ReferenceLibraryService:
    def __init__(
        self,
        index_path: str | Path | None = None,
        *,
        provider: Optional[EmbeddingProvider] = None,
    ) -> None:
        path = index_path or (Path(settings.VECTOR_DB_DIR) / "v2_reference_library.sqlite3")
        self.index = PersistentHybridIndex(path, provider=provider or LocalEmbedding())

    def ingest_docx(
        self,
        document_path: str | Path,
        *,
        document_id: str,
        source_card_path: str | Path = DEFAULT_SOURCE_CARD,
    ) -> int:
        require_serving_approval(source_card_path)
        source = Path(document_path)
        raw = source.read_bytes()
        sections = parse_document(source)
        chunks: List[KnowledgeChunk] = []
        for position, section in enumerate(sections, start=1):
            text = section.text.strip()
            if not text:
                continue
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"ref:{document_id}:{position}",
                    document_id=document_id,
                    document_version="1",
                    product_id="REF-CREDIT-PROPOSAL",
                    section_path=section.location or f"section-{position}",
                    chunk_type="reference_example_output",
                    text=text,
                    effective_from=__import__("datetime").date(2026, 1, 1),
                    effective_to=None,
                    active=True,
                    segments=["SME", "CORPORATE"],
                    access_scope={"branches": ["*"]},
                    content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    source_type="reference_example",
                    authority_tier=AuthorityTier.TIER_5_UNSUPPORTED,
                    verification_status=VerificationStatus.UNVERIFIED,
                    security_classification="RESTRICTED",
                )
            )
        return self.index.upsert(
            chunks,
            source_hash=hashlib.sha256(raw).hexdigest(),
            dataset_version="2026.07-demo-v1",
        )

    def search(self, query: str, *, top_k: int = 5) -> List[RetrievalHit]:
        return self.index.search(query, top_k=top_k)

    def list_chunks(self) -> List[KnowledgeChunk]:
        return self.index.list_chunks()
