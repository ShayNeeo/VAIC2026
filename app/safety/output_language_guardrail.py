"""Output language guardrail -- RAG & Guardrail Implementation Plan Phase
4 section 39. Deterministic phrase-list check: an Agent's OUTPUT text must
not use overclaiming language unless the underlying claim is actually
SUPPORTED with sufficient authority -- this module only detects the
FORBIDDEN phrases; the caller must supply whether the surrounding claim
was actually supported (from app.safety.claim_evidence_validator) to
decide whether a given phrase's use is even allowed. It does not itself
know whether authority exists."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.knowledge.index import fold

_FORBIDDEN_PHRASES = (
    "chắc chắn",
    "đã được phê duyệt",
    "đủ điều kiện",
    "sẽ được cấp",
    "hạn mức được duyệt",
    "phí áp dụng là",
    "lãi suất áp dụng là",
    "không còn rủi ro",
)

_SAFE_PHRASES = (
    "đề xuất sơ bộ",
    "cơ hội tiềm năng",
    "cần xác minh thêm",
    "chưa đủ căn cứ",
    "cần specialist review",
    "cần nguồn chính thức",
)


@dataclass(frozen=True)
class LanguageGuardrailResult:
    text: str
    forbidden_phrases_found: List[str]

    @property
    def is_safe(self) -> bool:
        return not self.forbidden_phrases_found


def check_output_language(text: str) -> LanguageGuardrailResult:
    # Diacritic-folded comparison (same normalization as
    # app.knowledge.index.fold, reused rather than reimplemented) --
    # Vietnamese text is routinely typed/OCR'd without full diacritics, so
    # a phrase match that only worked on perfectly-accented text would
    # silently miss the same overclaim written "chac chan" instead of
    # "chắc chắn".
    folded = fold(text)
    found = [phrase for phrase in _FORBIDDEN_PHRASES if fold(phrase) in folded]
    return LanguageGuardrailResult(text=text, forbidden_phrases_found=found)


def suggest_safe_rewrite_markers() -> List[str]:
    """Not an auto-rewrite (no LLM call site to actually rewrite text
    safely without changing its factual content) -- returns the prompt's
    own list of safe forms an Agent's OWN generation logic should prefer,
    for a caller to surface as guidance rather than to substitute text
    automatically (auto-substitution could silently change meaning)."""
    return list(_SAFE_PHRASES)
