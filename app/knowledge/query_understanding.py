"""Query Understanding -- RAG & Guardrail Implementation Plan Phase 3
section 21.

Deterministic, no LLM: this repo has no LLM entity-extraction call site
wired anywhere in the retrieval path, and the prompt's own constraint
("LLM có thể hỗ trợ entity extraction nhưng: quyền truy cập deterministic;
không cho LLM mở rộng permission") means an LLM layer would only ever be
allowed to ADD candidate entities, never decide access -- since no such
LLM integration exists in this codebase today, this module implements the
deterministic layer only and documents the LLM-assist layer as
NOT_IMPLEMENTED rather than stubbing a fake one.
"""

from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

_VIETNAMESE_DIACRITIC_RE = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", re.IGNORECASE
)

# Known ID prefixes this repo's real corpus uses (see
# data/synthetic/v2/{eligibility_rules,products}.json,
# data/synthetic/v3/{products,operations}/*.json) -- an exact match here
# means "the caller already knows the exact entity", which should route to
# exact lookup, not semantic scoring. Kept as prefixes, not full patterns,
# so a new product ID under an existing prefix scheme is recognized without
# a code change (still versioned/documented, not silently permissive: a
# non-matching ID is simply NOT flagged as an exact-entity candidate, it
# just falls through to semantic/sparse search).
_ID_PREFIXES = ("SYNTH-PROD-", "PROD-", "SYNTH-RULE-", "RULE-", "SYNTH-SOP-", "SYNTH-DOC-")

_TASK_TYPE_KEYWORDS = {
    "eligibility_check": ["dieu kien", "du dieu kien", "eligibility", "yeu cau", "quy dinh"],
    "product_discovery": ["san pham", "giai phap", "dich vu", "product"],
    "process_lookup": ["buoc", "quy trinh", "sop", "step", "workflow"],
    "document_lookup": ["ho so", "tai lieu", "document", "chung tu"],
}

_MULTI_HOP_MARKERS = ["va", "cung voi", "ke ca", "lan luot", "sau do"]


class DetectedEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: str
    entity_id: str
    matched_text: str


class QueryUnderstandingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    normalized_query: str
    language: str
    task_type: str

    entities: List[DetectedEntity] = Field(default_factory=list)
    product_ids: List[str] = Field(default_factory=list)
    policy_ids: List[str] = Field(default_factory=list)
    process_ids: List[str] = Field(default_factory=list)
    requirement_codes: List[str] = Field(default_factory=list)

    exact_lookup_required: bool = False
    semantic_lookup_required: bool = True
    multi_hop: bool = False
    source_types_required: List[str] = Field(default_factory=list)

    ambiguity: List[str] = Field(default_factory=list)
    security_flags: List[str] = Field(default_factory=list)


def _detect_language(query: str) -> str:
    return "vi" if _VIETNAMESE_DIACRITIC_RE.search(query) else "vi_unaccented_or_en"


def _detect_task_type(normalized: str) -> str:
    for task_type, keywords in _TASK_TYPE_KEYWORDS.items():
        if any(kw in normalized for kw in keywords):
            return task_type
    return "general_search"


def _detect_entities(query: str) -> List[DetectedEntity]:
    entities: List[DetectedEntity] = []
    for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]{2,}", query):
        upper = token.upper()
        if any(upper.startswith(prefix) for prefix in _ID_PREFIXES):
            entities.append(DetectedEntity(entity_type="known_id_prefix", entity_id=upper, matched_text=token))
    return entities


def understand_query(raw_query: str) -> QueryUnderstandingResult:
    normalized = " ".join(raw_query.strip().lower().split())
    language = _detect_language(raw_query)
    task_type = _detect_task_type(normalized)
    entities = _detect_entities(raw_query)

    product_ids = [e.entity_id for e in entities if "PROD" in e.entity_id]
    policy_ids = [e.entity_id for e in entities if "RULE" in e.entity_id]
    process_ids = [e.entity_id for e in entities if "SOP" in e.entity_id]

    exact_lookup_required = bool(entities)
    multi_hop = any(marker in normalized for marker in _MULTI_HOP_MARKERS) and len(product_ids) > 1

    ambiguity: List[str] = []
    if not normalized:
        ambiguity.append("empty_query")
    elif len(normalized) < 3:
        ambiguity.append("query_too_short")

    return QueryUnderstandingResult(
        normalized_query=normalized,
        language=language,
        task_type=task_type,
        entities=entities,
        product_ids=product_ids,
        policy_ids=policy_ids,
        process_ids=process_ids,
        exact_lookup_required=exact_lookup_required,
        semantic_lookup_required=not normalized == "" ,
        multi_hop=multi_hop,
        ambiguity=ambiguity,
    )
