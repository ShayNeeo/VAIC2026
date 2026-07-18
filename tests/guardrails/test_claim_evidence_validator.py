"""Phase 2 section 12: deterministic claim-evidence validation composed
from citation_validator (structural) + evidence_validator.validate_claim
(quote re-verification, reused unchanged) + conflict/scope checks new to
Phase 2. See app/safety/claim_evidence_validator.py module docstring for
why PARTIALLY_SUPPORTED is defined but never emitted."""

from __future__ import annotations

from datetime import date, datetime, timezone

from app.knowledge.index import LocalEmbedding, PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk
from app.knowledge.retrieval_contracts import (
    AgentType, GroundingItem, MetadataRef, RetrievalChannel, RetrievalConflict, RetrievalGroundingPack,
    SourceLocator, SourceLocatorType,
)
from app.safety.claim_evidence_validator import ClaimEvidenceStatus, validate_claim_against_pack


def _index_with_chunk(tmp_path, **overrides) -> PersistentHybridIndex:
    index = PersistentHybridIndex(tmp_path / "idx.sqlite3", provider=LocalEmbedding())
    base = dict(
        chunk_id="C1", document_id="DOC-1", document_version="1.0", product_id="PROD-X",
        section_path="1.1", text="Von luu dong yeu cau ho so tai chinh day du.",
        effective_from=date(2026, 1, 1), effective_to=None, active=True, segments=[],
        access_scope={"branches": ["*"]}, content_hash="h1",
    )
    base.update(overrides)
    index.upsert([KnowledgeChunk(**base)], source_hash="s1", dataset_version="v1")
    return index


def _pack(*, conflicts=None) -> RetrievalGroundingPack:
    item = GroundingItem(
        grounding_item_id="GI-1", chunk_id="C1", source_id="DOC-1", source_version="1.0",
        content="Von luu dong yeu cau ho so tai chinh day du.", retrieval_channel=RetrievalChannel.HYBRID,
        fused_score=0.5, source_locator=SourceLocator(type=SourceLocatorType.DOCUMENT_SPAN, section="1.1"),
    )
    return RetrievalGroundingPack(
        grounding_pack_id="GP-1", retrieval_run_id="RUN-1", agent_type=AgentType.LEGAL_POLICY,
        request_ref=MetadataRef(entity_type="retrieval_request", entity_id="r1"),
        items=[item], conflicts=conflicts or [], content_hash="abc", created_at=datetime.now(timezone.utc),
    )


def test_quote_that_genuinely_appears_in_source_is_supported(tmp_path):
    index = _index_with_chunk(tmp_path)
    result = validate_claim_against_pack(
        claim_id="CLAIM-1", chunk_id="C1", quote="Von luu dong yeu cau ho so tai chinh day du.",
        pinned_pack=_pack(), index=index,
    )
    assert result.status == ClaimEvidenceStatus.SUPPORTED
    assert result.usable_for_readiness_or_approval is True


def test_fabricated_quote_is_unsupported(tmp_path):
    index = _index_with_chunk(tmp_path)
    result = validate_claim_against_pack(
        claim_id="CLAIM-2", chunk_id="C1", quote="cau noi hoan toan bia dat",
        pinned_pack=_pack(), index=index,
    )
    assert result.status == ClaimEvidenceStatus.UNSUPPORTED
    assert result.usable_for_readiness_or_approval is False


def test_chunk_not_in_pinned_pack_is_source_unavailable(tmp_path):
    index = _index_with_chunk(tmp_path)
    result = validate_claim_against_pack(
        claim_id="CLAIM-3", chunk_id="C-NOT-IN-PACK", quote="whatever",
        pinned_pack=_pack(), index=index,
    )
    assert result.status == ClaimEvidenceStatus.SOURCE_UNAVAILABLE


def test_chunk_flagged_in_pack_conflicts_is_conflicted_even_with_a_valid_quote(tmp_path):
    index = _index_with_chunk(tmp_path)
    conflict = RetrievalConflict(conflict_id="CONFLICT-1", chunk_id_a="C1", chunk_id_b="C2", reason="disagreeing content")
    result = validate_claim_against_pack(
        claim_id="CLAIM-4", chunk_id="C1", quote="Von luu dong yeu cau ho so tai chinh day du.",
        pinned_pack=_pack(conflicts=[conflict]), index=index,
    )
    assert result.status == ClaimEvidenceStatus.CONFLICTED
    assert result.usable_for_readiness_or_approval is False


def test_expired_source_is_stale(tmp_path):
    index = _index_with_chunk(tmp_path, effective_to=date(2026, 1, 15))
    result = validate_claim_against_pack(
        claim_id="CLAIM-5", chunk_id="C1", quote="Von luu dong yeu cau ho so tai chinh day du.",
        pinned_pack=_pack(), index=index, as_of=date(2026, 6, 1),
    )
    assert result.status == ClaimEvidenceStatus.STALE_SOURCE


def test_wrong_customer_scope_is_rejected(tmp_path):
    index = _index_with_chunk(tmp_path, customer_id="COMP-ABC")
    result = validate_claim_against_pack(
        claim_id="CLAIM-6", chunk_id="C1", quote="Von luu dong yeu cau ho so tai chinh day du.",
        pinned_pack=_pack(), index=index, expected_customer_id="COMP-XYZ",
    )
    assert result.status == ClaimEvidenceStatus.WRONG_SCOPE
