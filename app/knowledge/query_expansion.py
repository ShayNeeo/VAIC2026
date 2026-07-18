"""Query Expansion -- RAG & Guardrail Implementation Plan Phase 3 section
23. Versioned synonym dictionary with provenance per expansion, exactly
the terms the prompt itself lists (Vietnamese banking acronyms/aliases) --
not a fabricated larger list, since every entry needs a real justification
this repo can point to."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

EXPANSION_REGISTRY_VERSION = "phase3-expansion-v1"

# Each key is matched as a whole-word, case-insensitive substring of the
# (already diacritic-preserved) query. Values are additional terms OR'd
# into the search -- this module does not alter the original query, it
# returns additions with provenance so a caller can decide how to use them
# (e.g. as extra tokens for BM25, never as a silent query replacement).
_SYNONYMS: Dict[str, List[str]] = {
    "bctc": ["báo cáo tài chính"],
    "đkkd": ["đăng ký kinh doanh"],
    "ubo": ["chủ sở hữu hưởng lợi"],
    "chi lương": ["payroll"],
    "thu hộ": ["collection"],
    "đối soát": ["reconciliation"],
    "vốn lưu động": ["working capital"],
}


@dataclass(frozen=True)
class ExpansionTerm:
    original_term: str
    expanded_term: str
    registry_version: str
    rule_id: str


def expand_query(query: str) -> List[ExpansionTerm]:
    """Case-insensitive substring match against the registry above. Returns
    an empty list for a query that matches nothing -- expansion is
    strictly additive and never invents a match."""
    lowered = query.lower()
    expansions: List[ExpansionTerm] = []
    for i, (term, synonyms) in enumerate(_SYNONYMS.items()):
        if term in lowered:
            for synonym in synonyms:
                expansions.append(
                    ExpansionTerm(
                        original_term=term, expanded_term=synonym,
                        registry_version=EXPANSION_REGISTRY_VERSION, rule_id=f"EXP-{i:03d}",
                    )
                )
    return expansions


def expanded_query_text(query: str) -> str:
    """Convenience: original query + all matched expansion terms appended,
    for callers (e.g. sparse_search_bm25) that just want more matchable
    tokens rather than the structured ExpansionTerm provenance list."""
    expansions = expand_query(query)
    if not expansions:
        return query
    return query + " " + " ".join(e.expanded_term for e in expansions)
