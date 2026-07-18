"""Prompt injection scanner for RETRIEVED DOCUMENT content -- RAG &
Guardrail Implementation Plan Phase 4 section 34.

Distinct from app/safety/input_guardrails_v2.py::screen_input (which
screens live USER input, 5 patterns, already wired into the request
path). This module scans indexed KNOWLEDGE CHUNK text -- every document
in the corpus is untrusted data that could contain an attempted
injection, not just live user messages. Reuses the same detection
philosophy (regex, deterministic, no LLM) but with the wider pattern set
the prompt's own section 34 lists, and adds span-level separation
(business_content vs untrusted_instruction_spans) so a chunk with ONE
suspicious sentence buried in otherwise-legitimate content is not
discarded wholesale.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from app.knowledge.index import fold

# Patterns are matched against fold()-normalized text (diacritics
# stripped, lowercased -- same normalization app.knowledge.index uses for
# retrieval tokenization), so each Vietnamese pattern below is written in
# its ALREADY-FOLDED form (e.g. "đánh dấu" -> "danh dau"). This makes
# detection robust to documents typed/OCR'd without full diacritics,
# which is common for real Vietnamese business text.
_INJECTION_PATTERNS = (
    r"ignore (all |previous )?instructions",
    r"bo qua (moi|tat ca|cac) (chi dan|huong dan)",
    r"reveal (the )?system prompt",
    r"tiet lo (system )?prompt",
    r"system prompt",
    r"developer message",
    r"approve this customer",
    r"phe duyet (khach hang|ho so) nay",
    r"mark (as )?verified",
    r"danh dau (da )?xac minh",
    r"call\s+\w*\.?\w*\s*tool",
    r"goi\s+cong cu",
    r"send (this )?data",
    r"gui du lieu",
    r"use another customer",
    r"dung (thong tin|ho so) khach hang khac",
    r"override policy",
    r"ghi de chinh sach",
    r"do not cite",
    r"khong (duoc )?trich dan",
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?|])\s+")


@dataclass(frozen=True)
class InjectionSpan:
    text: str
    start_offset: int
    end_offset: int
    matched_pattern: str


@dataclass(frozen=True)
class DocumentScanResult:
    chunk_id: str
    is_quarantined: bool
    manual_review_required: bool
    business_content: List[str]
    untrusted_instruction_spans: List[InjectionSpan]


def scan_chunk_text(chunk_id: str, text: str) -> DocumentScanResult:
    """Splits on sentence-like boundaries (same convention as
    app/knowledge/compression.py -- '.', '!', '?', '|'), classifies each
    piece as business content or a suspected injection span, and flags
    the whole chunk for quarantine/manual review if ANY span matches --
    a single injected sentence taints the chunk even if most of it is
    legitimate (fail-closed, not "average it away")."""
    business_content: List[str] = []
    untrusted_spans: List[InjectionSpan] = []
    cursor = 0
    for piece in _SENTENCE_SPLIT_RE.split(text):
        piece_stripped = piece.strip()
        if not piece_stripped:
            continue
        start = text.index(piece_stripped, cursor)
        end = start + len(piece_stripped)
        cursor = end

        folded_piece = fold(piece_stripped)
        matched = None
        for pattern in _INJECTION_PATTERNS:
            if re.search(pattern, folded_piece, re.IGNORECASE):
                matched = pattern
                break

        if matched:
            untrusted_spans.append(InjectionSpan(text=piece_stripped, start_offset=start, end_offset=end, matched_pattern=matched))
        else:
            business_content.append(piece_stripped)

    is_flagged = bool(untrusted_spans)
    return DocumentScanResult(
        chunk_id=chunk_id, is_quarantined=is_flagged, manual_review_required=is_flagged,
        business_content=business_content, untrusted_instruction_spans=untrusted_spans,
    )
