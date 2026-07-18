"""MMR diversity selection -- RAG & Guardrail Implementation Plan Phase 3
section 28.

Similarity proxy is token-set Jaccard overlap between chunk texts (no
extra embedding call needed -- this repo's dense vectors are not always
semantic, see app/knowledge/index.py RepresentationType, so re-using them
for a diversity proxy would silently inherit the same hash-collision
noise the rest of Phase 0-2 went to lengths to label honestly. Token
overlap is a cruder but transparent proxy).

Hard invariant enforced here: chunks passed in `protected_chunk_ids`
(absolute blockers, latest verified evidence, current policy, conflict
sources) are NEVER dropped by diversity selection -- they are always
included in the result, with MMR applied only to the remaining slots.
"""

from __future__ import annotations

from typing import List, Sequence, Set

from app.knowledge.reranker import RerankedCandidate


def _tokenize(text: str) -> Set[str]:
    return set(text.lower().split())


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def mmr_select(
    candidates: List[RerankedCandidate],
    *,
    top_k: int,
    lambda_relevance: float = 0.7,
    protected_chunk_ids: Sequence[str] = (),
) -> List[RerankedCandidate]:
    """lambda_relevance closer to 1.0 favors relevance, closer to 0.0
    favors novelty. protected candidates are always kept and never count
    against the diversity budget's need to justify novelty."""
    if not candidates:
        return []

    protected = [c for c in candidates if c.fused.chunk.chunk_id in protected_chunk_ids]
    remaining = [c for c in candidates if c.fused.chunk.chunk_id not in protected_chunk_ids]

    selected: List[RerankedCandidate] = list(protected)
    selected_tokens = [_tokenize(c.fused.chunk.text) for c in selected]

    remaining_pool = list(remaining)
    while remaining_pool and len(selected) < top_k:
        best_candidate = None
        best_score = float("-inf")
        for candidate in remaining_pool:
            candidate_tokens = _tokenize(candidate.fused.chunk.text)
            max_sim = max((_jaccard(candidate_tokens, s) for s in selected_tokens), default=0.0)
            mmr_score = lambda_relevance * candidate.rerank_score - (1 - lambda_relevance) * max_sim
            if mmr_score > best_score:
                best_score = mmr_score
                best_candidate = candidate
        selected.append(best_candidate)
        selected_tokens.append(_tokenize(best_candidate.fused.chunk.text))
        remaining_pool.remove(best_candidate)

    # Protected candidates are never truncated, even if their count alone
    # exceeds top_k (in that case the while loop above never ran, so
    # `selected` is exactly `protected`) -- only the MMR-selected
    # (non-protected) tail is capped to stay within budget.
    return selected if len(protected) >= top_k else selected[:top_k]
