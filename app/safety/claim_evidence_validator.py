"""Claim-evidence validator MVP -- RAG & Guardrail Implementation Plan
Phase 2 section 12.

Deterministic, composed from two existing pieces rather than a new
LLM-judge engine (the prompt explicitly says "Không xây LLM Judge mặc
định. Dùng deterministic validator trước."):

1. app.safety.citation_validator -- is the citation structurally real
   (right pack, right grounding_item, right source/version)?
2. app.safety.evidence_validator.validate_claim -- deterministic,
   independent quote-in-source re-verification (unchanged, reused as-is).

This module adds the two checks those two do not cover: (a) whether the
cited chunk is one of the pack's already-detected RetrievalConflicts, and
(b) whether the cited chunk's customer_id/case_id (if it has one) matches
the case this claim is being made for.

ClaimEvidenceStatus.PARTIALLY_SUPPORTED is defined (per the prompt's
status list) but this module never emits it: distinguishing "fully" vs
"partially" supported requires semantic entailment judgment (does the
quote support the WHOLE claim or only part of it?) that no deterministic
rule in this repository can make -- see the module-level NOTE below.
Emitting it without a real rule behind it would be exactly the kind of
overclaim this validator exists to prevent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

from app.knowledge.retrieval_contracts import RetrievalGroundingPack
from app.safety.citation_validator import validate_citation
from app.safety.evidence_validator import ChunkIndex, ValidationStatus, validate_claim


class ClaimEvidenceStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"  # NOTE: never emitted -- see module docstring.
    CONFLICTED = "CONFLICTED"
    STALE_SOURCE = "STALE_SOURCE"
    WRONG_SCOPE = "WRONG_SCOPE"
    UNSUPPORTED = "UNSUPPORTED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


_CAN_BE_USED_FOR_DECISIONS = {ClaimEvidenceStatus.SUPPORTED}


@dataclass(frozen=True)
class ClaimEvidenceResult:
    claim_id: str
    status: ClaimEvidenceStatus
    reason: str

    @property
    def usable_for_readiness_or_approval(self) -> bool:
        """Phase 2 hard rule: a critical claim not SUPPORTED must not be
        used for readiness, RM approval, or underwriting submission -- not
        merely have its confidence reduced (see prompt section 12)."""
        return self.status in _CAN_BE_USED_FOR_DECISIONS


def validate_claim_against_pack(
    *,
    claim_id: str,
    chunk_id: str,
    quote: str,
    pinned_pack: RetrievalGroundingPack,
    index: ChunkIndex,
    as_of: Optional[date] = None,
    expected_customer_id: Optional[str] = None,
    expected_case_id: Optional[str] = None,
) -> ClaimEvidenceResult:
    item = next((i for i in pinned_pack.items if i.chunk_id == chunk_id), None)
    if item is None:
        return ClaimEvidenceResult(
            claim_id, ClaimEvidenceStatus.SOURCE_UNAVAILABLE,
            f"chunk_id={chunk_id!r} is not present in pinned pack {pinned_pack.grounding_pack_id!r}",
        )

    citation_check = validate_citation(
        grounding_pack_id=pinned_pack.grounding_pack_id, grounding_item_id=item.grounding_item_id,
        source_id=item.source_id, source_version=item.source_version, pinned_pack=pinned_pack,
    )
    if not citation_check.is_valid:
        return ClaimEvidenceResult(claim_id, ClaimEvidenceStatus.SOURCE_UNAVAILABLE, citation_check.reason)

    if any(chunk_id in (c.chunk_id_a, c.chunk_id_b) for c in pinned_pack.conflicts):
        return ClaimEvidenceResult(
            claim_id, ClaimEvidenceStatus.CONFLICTED,
            f"chunk_id={chunk_id!r} is part of a detected RetrievalConflict in this pack -- "
            "cannot be used as sole evidence without human review.",
        )

    # get_chunks_for_document is the only lookup ChunkIndex guarantees (see
    # app/safety/evidence_validator.py's Protocol) -- reuse it rather than
    # widening the Protocol just for a scope check.
    chunks = index.get_chunks_for_document(item.source_id, item.source_version)
    matching_chunk = next((c for c in chunks if c.chunk_id == chunk_id), None)
    if matching_chunk is not None:
        if expected_customer_id is not None and matching_chunk.customer_id is not None and matching_chunk.customer_id != expected_customer_id:
            return ClaimEvidenceResult(
                claim_id, ClaimEvidenceStatus.WRONG_SCOPE,
                f"chunk customer_id={matching_chunk.customer_id!r} does not match expected {expected_customer_id!r}",
            )
        if expected_case_id is not None and matching_chunk.case_id is not None and matching_chunk.case_id != expected_case_id:
            return ClaimEvidenceResult(
                claim_id, ClaimEvidenceStatus.WRONG_SCOPE,
                f"chunk case_id={matching_chunk.case_id!r} does not match expected {expected_case_id!r}",
            )

    evidence_result = validate_claim(
        claim_id=claim_id, source_document_id=item.source_id, source_version=item.source_version,
        quote=quote, index=index, as_of=as_of,
    )

    status_map = {
        ValidationStatus.VALID: ClaimEvidenceStatus.SUPPORTED,
        ValidationStatus.EXPIRED_SOURCE: ClaimEvidenceStatus.STALE_SOURCE,
        ValidationStatus.VERSION_MISMATCH: ClaimEvidenceStatus.STALE_SOURCE,
        ValidationStatus.SOURCE_NOT_FOUND: ClaimEvidenceStatus.SOURCE_UNAVAILABLE,
        ValidationStatus.INVALID: ClaimEvidenceStatus.UNSUPPORTED,
        ValidationStatus.INSUFFICIENT_EVIDENCE: ClaimEvidenceStatus.UNSUPPORTED,
        ValidationStatus.CONFLICTING_EVIDENCE: ClaimEvidenceStatus.CONFLICTED,
    }
    return ClaimEvidenceResult(claim_id, status_map[evidence_result.status], evidence_result.reason or evidence_result.status.value)
