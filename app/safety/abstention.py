"""Abstention engine -- RAG & Guardrail Implementation Plan Phase 4
section 40. Composes signals already produced by Phase 2/3 (retrieval
diagnostics, claim-evidence validation) into one AbstentionDecision --
does not introduce a new source of truth, only a single place that maps
"what already happened" onto the prompt's required reason-code vocabulary
and required accompanying fields (missing information / next question /
required evidence / recommended reviewer / source status)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from app.knowledge.retrieval_contracts import ControlledRetrievalResult, RetrievalErrorCode, RetrievalStatus
from app.safety.claim_evidence_validator import ClaimEvidenceResult, ClaimEvidenceStatus


class AbstentionReason(str, Enum):
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    POLICY_SOURCE_NOT_FOUND = "POLICY_SOURCE_NOT_FOUND"
    CONFLICTING_SOURCES = "CONFLICTING_SOURCES"
    SOURCE_EXPIRED = "SOURCE_EXPIRED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    INVALID_DOCUMENT = "INVALID_DOCUMENT"
    UNSUPPORTED_REQUEST = "UNSUPPORTED_REQUEST"


_RETRIEVAL_ERROR_TO_ABSTENTION = {
    RetrievalErrorCode.NO_RELEVANT_RESULT: AbstentionReason.INSUFFICIENT_EVIDENCE,
    RetrievalErrorCode.INDEX_NOT_READY: AbstentionReason.PROVIDER_UNAVAILABLE,
    RetrievalErrorCode.EMPTY_QUERY: AbstentionReason.UNSUPPORTED_REQUEST,
    RetrievalErrorCode.AUTHORIZATION_DENIED: AbstentionReason.AUTHORIZATION_DENIED,
    RetrievalErrorCode.SOURCE_SCOPE_EMPTY: AbstentionReason.POLICY_SOURCE_NOT_FOUND,
    RetrievalErrorCode.QUERY_INVALID: AbstentionReason.UNSUPPORTED_REQUEST,
    RetrievalErrorCode.PROVIDER_UNAVAILABLE: AbstentionReason.PROVIDER_UNAVAILABLE,
    RetrievalErrorCode.PROVIDER_TIMEOUT: AbstentionReason.PROVIDER_UNAVAILABLE,
    RetrievalErrorCode.EMBEDDING_FAILURE: AbstentionReason.PROVIDER_UNAVAILABLE,
    RetrievalErrorCode.INDEX_VERSION_MISMATCH: AbstentionReason.PROVIDER_UNAVAILABLE,
    RetrievalErrorCode.FILTER_CONFIGURATION_INVALID: AbstentionReason.UNSUPPORTED_REQUEST,
    RetrievalErrorCode.EXACT_ENTITY_NOT_FOUND: AbstentionReason.INSUFFICIENT_EVIDENCE,
}

_CLAIM_STATUS_TO_ABSTENTION = {
    ClaimEvidenceStatus.UNSUPPORTED: AbstentionReason.INSUFFICIENT_EVIDENCE,
    ClaimEvidenceStatus.CONFLICTED: AbstentionReason.CONFLICTING_SOURCES,
    ClaimEvidenceStatus.STALE_SOURCE: AbstentionReason.SOURCE_EXPIRED,
    ClaimEvidenceStatus.WRONG_SCOPE: AbstentionReason.OUT_OF_SCOPE,
    ClaimEvidenceStatus.SOURCE_UNAVAILABLE: AbstentionReason.INVALID_DOCUMENT,
}


@dataclass(frozen=True)
class AbstentionDecision:
    must_abstain: bool
    reason: Optional[AbstentionReason]
    missing_information: List[str] = field(default_factory=list)
    next_question: Optional[str] = None
    required_evidence: List[str] = field(default_factory=list)
    recommended_reviewer: Optional[str] = None
    source_status: Optional[str] = None


def decide_from_retrieval(result: ControlledRetrievalResult) -> AbstentionDecision:
    """Phase 2's fail-closed/empty-result outcomes, translated into an
    abstention decision an Agent must act on BEFORE attempting to
    generate any claim at all."""
    if result.diagnostics.status == RetrievalStatus.OK and result.grounding_pack is not None:
        return AbstentionDecision(must_abstain=False, reason=None)

    error_code = result.diagnostics.error_code
    reason = _RETRIEVAL_ERROR_TO_ABSTENTION.get(error_code, AbstentionReason.INSUFFICIENT_EVIDENCE) if error_code else AbstentionReason.INSUFFICIENT_EVIDENCE
    return AbstentionDecision(
        must_abstain=True, reason=reason,
        missing_information=["no eligible source found for this query" if reason == AbstentionReason.INSUFFICIENT_EVIDENCE else ""],
        source_status=result.diagnostics.status.value,
    )


def decide_from_claim(claim: ClaimEvidenceResult) -> AbstentionDecision:
    """A critical claim that is not SUPPORTED must trigger abstention for
    THAT claim -- Phase 2 section 12's hard rule ("không chỉ giảm
    confidence"), now expressed as a structured decision an Agent's
    output-assembly step can act on directly."""
    if claim.usable_for_readiness_or_approval:
        return AbstentionDecision(must_abstain=False, reason=None)

    reason = _CLAIM_STATUS_TO_ABSTENTION.get(claim.status, AbstentionReason.INSUFFICIENT_EVIDENCE)
    recommended_reviewer = "Legal Specialist" if reason == AbstentionReason.CONFLICTING_SOURCES else None
    return AbstentionDecision(
        must_abstain=True, reason=reason,
        missing_information=[claim.reason],
        recommended_reviewer=recommended_reviewer,
        source_status=claim.status.value,
    )
