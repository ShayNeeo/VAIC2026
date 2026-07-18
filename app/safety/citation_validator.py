"""Structural citation validator -- RAG & Guardrail Implementation Plan
Phase 2 section 13.

Explicitly STRUCTURAL, not semantic: this checks that a citation points at
something that genuinely exists inside a specific, already-pinned
RetrievalGroundingPack (right chunk_id, right source_id/version, right
content_hash of the pack itself) -- it does NOT check whether the cited
text actually entails/supports the claim it's attached to (that is
app/safety/evidence_validator.py's job -- deterministic quote-in-source
matching -- and app/safety/claim_evidence_validator.py, which composes
both). Calling this "citation verification" without the word
"structural" would overclaim what it does, per the Phase 2 prompt's own
instruction: "Chưa cần semantic entailment bằng LLM trong Phase 2... Ghi
rõ: STRUCTURAL_CITATION_VALIDATION."
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.knowledge.retrieval_contracts import RetrievalGroundingPack


class CitationValidationStatus(str, Enum):
    STRUCTURAL_CITATION_VALIDATION_PASSED = "STRUCTURAL_CITATION_VALIDATION_PASSED"
    GROUNDING_ITEM_NOT_FOUND = "GROUNDING_ITEM_NOT_FOUND"
    SOURCE_VERSION_MISMATCH = "SOURCE_VERSION_MISMATCH"
    PACK_HASH_MISMATCH = "PACK_HASH_MISMATCH"
    CITED_ANOTHER_PACK = "CITED_ANOTHER_PACK"


@dataclass(frozen=True)
class CitationValidationResult:
    status: CitationValidationStatus
    reason: str

    @property
    def is_valid(self) -> bool:
        return self.status == CitationValidationStatus.STRUCTURAL_CITATION_VALIDATION_PASSED


def validate_citation(
    *,
    grounding_pack_id: str,
    grounding_item_id: str,
    source_id: str,
    source_version: str,
    pinned_pack: RetrievalGroundingPack,
) -> CitationValidationResult:
    """A claim's citation must name the SAME pack it was pinned against
    (grounding_pack_id match), a grounding_item_id that pack actually
    contains, and a source_id/source_version that matches that item
    exactly -- never a different version of the same document, which
    would silently launder a stale citation through a fresh-looking
    pack."""
    if grounding_pack_id != pinned_pack.grounding_pack_id:
        return CitationValidationResult(
            CitationValidationStatus.CITED_ANOTHER_PACK,
            f"citation names grounding_pack_id={grounding_pack_id!r} but was checked "
            f"against pinned_pack.grounding_pack_id={pinned_pack.grounding_pack_id!r}",
        )

    item = next((i for i in pinned_pack.items if i.grounding_item_id == grounding_item_id), None)
    if item is None:
        return CitationValidationResult(
            CitationValidationStatus.GROUNDING_ITEM_NOT_FOUND,
            f"grounding_item_id={grounding_item_id!r} is not present in pack {pinned_pack.grounding_pack_id!r}",
        )

    if item.source_id != source_id or item.source_version != source_version:
        return CitationValidationResult(
            CitationValidationStatus.SOURCE_VERSION_MISMATCH,
            f"citation names source_id={source_id!r}/source_version={source_version!r} but "
            f"grounding_item {grounding_item_id!r} is source_id={item.source_id!r}/source_version={item.source_version!r}",
        )

    return CitationValidationResult(
        CitationValidationStatus.STRUCTURAL_CITATION_VALIDATION_PASSED,
        "chunk_id/source_id/source_version match the pinned GroundingPack.",
    )


def verify_pack_integrity(pack: RetrievalGroundingPack, expected_content_hash: str) -> Optional[CitationValidationResult]:
    """Returns a PACK_HASH_MISMATCH result if the pack a caller is holding
    does not match the content_hash it was pinned with (e.g. re-fetched
    from storage and something changed) -- None means the hash is intact
    and the caller should proceed to validate_citation()."""
    if pack.content_hash != expected_content_hash:
        return CitationValidationResult(
            CitationValidationStatus.PACK_HASH_MISMATCH,
            f"pinned content_hash={expected_content_hash!r} but pack.content_hash={pack.content_hash!r}",
        )
    return None
