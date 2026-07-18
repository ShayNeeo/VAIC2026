"""Pure retrieval-quality metric calculators -- RAG & Guardrail
Implementation Plan Phase 2 section 16 (ablation). No I/O, no model calls;
each function takes plain ranked chunk_id lists and a ground-truth set, so
these are independently unit-testable without a live index."""

from __future__ import annotations

import math
from typing import List, Optional, Sequence


def recall_at_k(ranked_chunk_ids: Sequence[str], relevant: Sequence[str], k: int) -> Optional[float]:
    if not relevant:
        return None
    top_k = set(ranked_chunk_ids[:k])
    hit = len(top_k & set(relevant))
    return hit / len(set(relevant))


def reciprocal_rank(ranked_chunk_ids: Sequence[str], relevant: Sequence[str]) -> Optional[float]:
    if not relevant:
        return None
    relevant_set = set(relevant)
    for i, chunk_id in enumerate(ranked_chunk_ids):
        if chunk_id in relevant_set:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(ranked_chunk_ids: Sequence[str], relevant: Sequence[str], k: int) -> Optional[float]:
    if not relevant:
        return None
    relevant_set = set(relevant)
    dcg = 0.0
    for i, chunk_id in enumerate(ranked_chunk_ids[:k]):
        if chunk_id in relevant_set:
            dcg += 1.0 / math.log2(i + 2)
    ideal_hits = min(len(relevant_set), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
    if idcg == 0:
        return 0.0
    return dcg / idcg


def forbidden_retrieved(ranked_chunk_ids: Sequence[str], forbidden: Sequence[str], k: int) -> bool:
    if not forbidden:
        return False
    return bool(set(ranked_chunk_ids[:k]) & set(forbidden))


def no_result_correct(ranked_chunk_ids: Sequence[str], relevant: Sequence[str]) -> Optional[bool]:
    """For 'no_relevant_result'/'empty_query' ground-truth cases (relevant
    == []): correct means the system also returned nothing."""
    if relevant:
        return None
    return len(ranked_chunk_ids) == 0


def average(values: List[Optional[float]]) -> Optional[float]:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 4)


def rate(values: List[bool]) -> Optional[float]:
    if not values:
        return None
    return round(sum(1 for v in values if v) / len(values), 4)
