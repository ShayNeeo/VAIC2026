"""Deterministic, independent evidence/citation validation.

Replaces the previous live-path check, `is_valid=bool(quote)`
(``app/workflow/engine.py``'s old ``_product_evidence``/``_legal_evidence``),
which accepted any non-empty string as "valid" -- it never actually looked
at a source. This module independently re-checks every claim against the
same indexed knowledge the system serves from, so a bug (or a future code
path that lets an LLM author a quote) cannot silently produce
``is_valid=True`` just because a string happens to be present.

Deterministic exact/normalized substring matching is the only REQUIRED
layer -- it must keep working with no paid API key configured. An optional
semantic-similarity layer (when an embedding provider is available) can only
*upgrade* a near-miss to valid; it is never the sole basis for validity, and
its absence/failure never blocks validation.

The previous version of this file (see git history) validated against
``data/mock_database/*.json`` -- a dataset the live V2 pipeline does not
use at all (the live pipeline reads ``data/synthetic/v2/{products,
eligibility_rules}.json`` via ``ProductKnowledgeService``/
``LegalKnowledgeService``) -- and referenced ``Evidence``/``SharedCaseState``
fields (``source_doc``, ``page_or_section``, ``state.audit_log``,
``state.legal_result``, ``state.approval_status``) that do not exist on the
current schema (``app/schemas/v2/shared_case_state.py``). It was dead code,
imported only by ``app/safety/__init__.py`` and nowhere in the live request
path; it would have raised ``AttributeError`` if ever actually invoked.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Protocol

from app.knowledge.models import KnowledgeChunk


class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    SOURCE_NOT_FOUND = "source_not_found"
    VERSION_MISMATCH = "version_mismatch"
    EXPIRED_SOURCE = "expired_source"


@dataclass(frozen=True)
class EvidenceValidationResult:
    claim_id: str
    status: ValidationStatus
    source_document_id: str
    document_version: str
    exact_match: bool
    semantic_match: Optional[bool] = None
    reason: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.status == ValidationStatus.VALID

    def to_dict(self) -> Dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "status": self.status.value,
            "source_document_id": self.source_document_id,
            "document_version": self.document_version,
            "exact_match": self.exact_match,
            "semantic_match": self.semantic_match,
            "reason": self.reason,
        }


class ChunkIndex(Protocol):
    """The subset of PersistentHybridIndex this module depends on."""

    def get_chunks_for_document(
        self, document_id: str, document_version: Optional[str] = None
    ) -> List[KnowledgeChunk]: ...


# Synthetic, internally-authored system statements are not drawn from the
# RAG index (see app/eligibility/engine.py::_live_failure) -- there is
# nothing to look up, so these are exempt from the source-lookup step but
# still required to carry a non-empty quote.
_SYSTEM_SOURCE_IDS = {"SYSTEM-TOOL-CONTRACT"}


def _normalize(text: str) -> str:
    """Unicode/whitespace-fold so a re-wrapped or re-typed quote with the
    same content but different line breaks/spacing still matches."""
    value = unicodedata.normalize("NFC", text or "")
    return re.sub(r"\s+", " ", value).strip()


def validate_claim(
    *,
    claim_id: str,
    source_document_id: str,
    source_version: str,
    quote: str,
    index: ChunkIndex,
    as_of: Optional[date] = None,
    semantic_check: Optional["SemanticSimilarityCheck"] = None,
) -> EvidenceValidationResult:
    """Validate one claim's citation against the controlled source index.

    Deterministic-first: an exact (normalized) substring match is sufficient
    for VALID on its own. semantic_check is optional and additive -- it can
    only be consulted when the deterministic check found the quote absent
    from the source text but wants a supplementary similarity signal
    recorded (still returns INVALID; semantic proximity is informational,
    not a pass condition, since silently approving on "close enough" is
    exactly the failure mode this module exists to prevent).
    """
    if not quote or not quote.strip():
        return EvidenceValidationResult(
            claim_id=claim_id, status=ValidationStatus.INSUFFICIENT_EVIDENCE,
            source_document_id=source_document_id, document_version=source_version,
            exact_match=False, reason="empty_quote",
        )

    if source_document_id in _SYSTEM_SOURCE_IDS:
        return EvidenceValidationResult(
            claim_id=claim_id, status=ValidationStatus.VALID,
            source_document_id=source_document_id, document_version=source_version,
            exact_match=True, reason="system_source_exempt_from_index_lookup",
        )

    exact_chunks = index.get_chunks_for_document(source_document_id, source_version)
    if not exact_chunks:
        any_version_chunks = index.get_chunks_for_document(source_document_id, None)
        if any_version_chunks:
            return EvidenceValidationResult(
                claim_id=claim_id, status=ValidationStatus.VERSION_MISMATCH,
                source_document_id=source_document_id, document_version=source_version,
                exact_match=False,
                reason=f"document exists but not at version {source_version!r}",
            )
        return EvidenceValidationResult(
            claim_id=claim_id, status=ValidationStatus.SOURCE_NOT_FOUND,
            source_document_id=source_document_id, document_version=source_version,
            exact_match=False, reason="no indexed chunk for this document_id",
        )

    normalized_quote = _normalize(quote)
    exact = any(normalized_quote in _normalize(chunk.text) for chunk in exact_chunks)

    semantic: Optional[bool] = None
    if not exact and semantic_check is not None:
        try:
            semantic = semantic_check(quote, [chunk.text for chunk in exact_chunks])
        except Exception:
            # Optional layer: any failure (missing key, network, quota) must
            # never block or flip a deterministic result.
            semantic = None

    if not exact:
        return EvidenceValidationResult(
            claim_id=claim_id, status=ValidationStatus.INVALID,
            source_document_id=source_document_id, document_version=source_version,
            exact_match=False, semantic_match=semantic, reason="quote_not_found_in_source",
        )

    today = as_of or date.today()
    if any(chunk.effective_to is not None and chunk.effective_to < today for chunk in exact_chunks):
        return EvidenceValidationResult(
            claim_id=claim_id, status=ValidationStatus.EXPIRED_SOURCE,
            source_document_id=source_document_id, document_version=source_version,
            exact_match=True, semantic_match=semantic, reason="source effective_to has passed",
        )

    return EvidenceValidationResult(
        claim_id=claim_id, status=ValidationStatus.VALID,
        source_document_id=source_document_id, document_version=source_version,
        exact_match=True, semantic_match=semantic,
    )


class SemanticSimilarityCheck(Protocol):
    def __call__(self, quote: str, source_texts: List[str]) -> bool: ...


@dataclass
class ClaimInput:
    claim_id: str
    source_document_id: str
    source_version: str
    quote: str


def detect_conflicts(claims: List[ClaimInput]) -> Dict[str, List[str]]:
    """Group claims by claim_id; if the same claim_id was asserted with
    different quotes (e.g. by two evidence-producing runs), that is a
    conflict -- the system should not silently pick one. Returns
    {claim_id: [distinct normalized quotes]} only for claim_ids in conflict.
    """
    by_claim: Dict[str, set] = {}
    for item in claims:
        by_claim.setdefault(item.claim_id, set()).add(_normalize(item.quote))
    return {claim_id: sorted(quotes) for claim_id, quotes in by_claim.items() if len(quotes) > 1}


@dataclass
class EvidenceValidator:
    """Convenience facade bundling a product index and a legal index lookup,
    matching Evidence.module ("Product" -> product_index, anything else ->
    legal_index). See app/workflow/engine.py for the live wiring."""

    product_index: ChunkIndex
    legal_index: ChunkIndex
    semantic_check: Optional[SemanticSimilarityCheck] = None
    results: List[EvidenceValidationResult] = field(default_factory=list)

    def validate_all(self, evidences: List["EvidenceLike"]) -> List[EvidenceValidationResult]:
        conflicts = detect_conflicts(
            [ClaimInput(e.claim_id, e.source_document_id, e.source_version, e.quote) for e in evidences]
        )
        results: List[EvidenceValidationResult] = []
        for evidence in evidences:
            if evidence.claim_id in conflicts:
                results.append(
                    EvidenceValidationResult(
                        claim_id=evidence.claim_id, status=ValidationStatus.CONFLICTING_EVIDENCE,
                        source_document_id=evidence.source_document_id,
                        document_version=evidence.source_version,
                        exact_match=False, reason=f"{len(conflicts[evidence.claim_id])} distinct quotes for this claim_id",
                    )
                )
                continue
            index = self.product_index if evidence.module == "Product" else self.legal_index
            results.append(
                validate_claim(
                    claim_id=evidence.claim_id,
                    source_document_id=evidence.source_document_id,
                    source_version=evidence.source_version,
                    quote=evidence.quote,
                    index=index,
                    semantic_check=self.semantic_check,
                )
            )
        self.results = results
        return results


class EvidenceLike(Protocol):
    claim_id: str
    module: str
    source_document_id: str
    source_version: str
    quote: str
