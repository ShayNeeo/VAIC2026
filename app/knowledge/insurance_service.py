"""Insurance-policy retrieval with a dedicated identity/profile, mirroring
app/knowledge/credit_service.py::CreditKnowledgeService. Backs the
independent InsuranceExpert (app/agents/insurance_expert.py) -- retrieval
explains policy text; it never decides coverage adequacy itself.
"""

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
from app.knowledge.models import KnowledgeChunk
from app.knowledge.retrieval_contracts import AuthorityTier, VerificationStatus


DEFAULT_INSURANCE_POLICY = ROOT / "data" / "legal" / "policies" / "shb_insurance_policy_manual.json"
DEFAULT_INSURANCE_SOURCE_CARD = ROOT / "data" / "catalog" / "source_cards" / "synthetic_insurance_reference_pack.json"


class InsuranceKnowledgeService(LegalKnowledgeService):
    def __init__(
        self,
        index_path: str | Path | None = None,
        *,
        provider: Optional[EmbeddingProvider] = None,
    ) -> None:
        path = index_path or (Path(settings.VECTOR_DB_DIR) / "v2_insurance.sqlite3")
        super().__init__(path, provider=provider or LocalEmbedding())

    def ingest(
        self,
        rules_path: str | Path = DEFAULT_INSURANCE_POLICY,
        source_card_path: str | Path = DEFAULT_INSURANCE_SOURCE_CARD,
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
                        chunk_id=f"insurance:{payload['document_id']}:{article_id}",
                        document_id=str(payload["document_id"]),
                        document_version=str(payload["version"]),
                        product_id="PROD-INSURANCE-GENERAL",
                        section_path=f"{chapter.get('chapter_id')} / {article_id}",
                        chunk_type="insurance_policy_article",
                        text=text,
                        effective_from=effective_from,
                        effective_to=effective_to,
                        active=str(payload.get("status", "active")) == "active",
                        segments=["SME", "CORPORATE"],
                        access_scope={"branches": ["*"]},
                        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        source_type="insurance_policy",
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
