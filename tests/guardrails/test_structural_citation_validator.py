"""Phase 2 section 13: STRUCTURAL_CITATION_VALIDATION -- checks a citation
points at something real inside a specific, already-pinned
RetrievalGroundingPack. Deliberately does NOT check semantic entailment
(see app/safety/citation_validator.py module docstring)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.knowledge.retrieval_contracts import (
    AgentType, GroundingItem, MetadataRef, RetrievalChannel, RetrievalGroundingPack, SourceLocator, SourceLocatorType,
)
from app.safety.citation_validator import CitationValidationStatus, validate_citation, verify_pack_integrity


def _pack() -> RetrievalGroundingPack:
    item = GroundingItem(
        grounding_item_id="GI-1", chunk_id="C1", source_id="DOC-1", source_version="1.0",
        content="noi dung that", retrieval_channel=RetrievalChannel.HYBRID, fused_score=0.5,
        source_locator=SourceLocator(type=SourceLocatorType.DOCUMENT_SPAN, section="1.1"),
    )
    return RetrievalGroundingPack(
        grounding_pack_id="GP-1", retrieval_run_id="RUN-1", agent_type=AgentType.LEGAL_POLICY,
        request_ref=MetadataRef(entity_type="retrieval_request", entity_id="r1"),
        items=[item], content_hash="abc123", created_at=datetime.now(timezone.utc),
    )


def test_valid_citation_passes():
    pack = _pack()
    result = validate_citation(
        grounding_pack_id="GP-1", grounding_item_id="GI-1", source_id="DOC-1", source_version="1.0", pinned_pack=pack,
    )
    assert result.is_valid
    assert result.status == CitationValidationStatus.STRUCTURAL_CITATION_VALIDATION_PASSED


def test_citation_naming_a_different_pack_fails():
    pack = _pack()
    result = validate_citation(
        grounding_pack_id="GP-OTHER", grounding_item_id="GI-1", source_id="DOC-1", source_version="1.0", pinned_pack=pack,
    )
    assert not result.is_valid
    assert result.status == CitationValidationStatus.CITED_ANOTHER_PACK


def test_citation_naming_an_unknown_grounding_item_fails():
    pack = _pack()
    result = validate_citation(
        grounding_pack_id="GP-1", grounding_item_id="GI-DOES-NOT-EXIST", source_id="DOC-1", source_version="1.0", pinned_pack=pack,
    )
    assert not result.is_valid
    assert result.status == CitationValidationStatus.GROUNDING_ITEM_NOT_FOUND


def test_citation_with_wrong_source_version_fails():
    pack = _pack()
    result = validate_citation(
        grounding_pack_id="GP-1", grounding_item_id="GI-1", source_id="DOC-1", source_version="2.0", pinned_pack=pack,
    )
    assert not result.is_valid
    assert result.status == CitationValidationStatus.SOURCE_VERSION_MISMATCH


def test_pack_integrity_check_detects_hash_mismatch():
    pack = _pack()
    assert verify_pack_integrity(pack, expected_content_hash="abc123") is None
    mismatch = verify_pack_integrity(pack, expected_content_hash="tampered")
    assert mismatch is not None
    assert mismatch.status == CitationValidationStatus.PACK_HASH_MISMATCH
