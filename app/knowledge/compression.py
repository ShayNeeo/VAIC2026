"""Contextual compression -- RAG & Guardrail Implementation Plan Phase 3
section 29.

Extractive only, NOT LLM-summarization: this repo has no LLM call site in
the retrieval path, and the prompt's own constraint ("LLM summary không
được thay citation gốc") means any LLM-based compression would still need
this exact offset-mapping contract underneath it -- building the
extractive layer first is a prerequisite, not a placeholder. Keeps
sentences containing a number, a date-like token, an exception marker
("trừ", "ngoại trừ", "nếu"), or a condition marker ("khi", "nếu", "trong
trường hợp"), which is a real (if crude) proxy for "qualifier/exception/
condition/effective date" from the prompt's requirement -- documented as
a heuristic, not a semantic filter.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?|])\s+")
_NUMBER_RE = re.compile(r"\d")
_DATE_RE = re.compile(r"\b(20\d{2}|ngày|tháng|năm)\b", re.IGNORECASE)
_EXCEPTION_MARKERS = ["trừ", "ngoại trừ", "ngoài trừ"]
_CONDITION_MARKERS = ["khi", "nếu", "trong trường hợp", "yêu cầu", "điều kiện"]


@dataclass(frozen=True)
class CompressedSpan:
    compressed_text: str
    original_chunk_id: str
    start_offset: int
    end_offset: int


def compress_chunk_text(chunk_id: str, text: str, *, max_sentences: int = 3) -> List[CompressedSpan]:
    """Splits on sentence-like boundaries (also '|', this corpus's own
    field separator, see legal_service.py's ' | '.join usage), scores each
    piece by whether it looks like it carries a fact/qualifier/exception/
    condition, and keeps the top `max_sentences` by that score while
    preserving each kept piece's exact character offsets into `text` (so a
    citation can still point at the ORIGINAL chunk, never at compressed
    text -- see GroundingItem.source_locator, which always references the
    uncompressed chunk_id)."""
    spans: List[CompressedSpan] = []
    cursor = 0
    for piece in _SENTENCE_SPLIT_RE.split(text):
        piece = piece.strip()
        if not piece:
            continue
        start = text.index(piece, cursor)
        end = start + len(piece)
        cursor = end
        score = 0
        if _NUMBER_RE.search(piece):
            score += 2
        if _DATE_RE.search(piece):
            score += 2
        if any(marker in piece.lower() for marker in _EXCEPTION_MARKERS):
            score += 3
        if any(marker in piece.lower() for marker in _CONDITION_MARKERS):
            score += 1
        spans.append((score, CompressedSpan(compressed_text=piece, original_chunk_id=chunk_id, start_offset=start, end_offset=end)))

    spans.sort(key=lambda item: (-item[0], item[1].start_offset))
    kept = spans[:max_sentences]
    kept.sort(key=lambda item: item[1].start_offset)
    return [span for _score, span in kept]
