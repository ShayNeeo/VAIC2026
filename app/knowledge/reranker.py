"""Reranker -- RAG & Guardrail Implementation Plan Phase 3 section 27.

Only HEURISTIC mode is implemented (deterministic, no dependency). Modes
CROSS_ENCODER and LLM_RERANKER_EXPERIMENTAL are defined in the enum for
API completeness but NOT_IMPLEMENTED: this repo has no cross-encoder
model dependency installed and no LLM call site wired into retrieval --
adding either would be a fabricated integration, not a real one. Selecting
those modes raises NotImplementedError rather than silently falling back,
so a caller cannot mistake "requested but unavailable" for "ran and
returned no change".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List, Optional, Protocol

from app.knowledge.fusion import FusedCandidate
from app.knowledge.retrieval_contracts import AuthorityTier, VerificationStatus


class RerankerMode(str, Enum):
    NONE = "NONE"
    HEURISTIC = "HEURISTIC"
    CROSS_ENCODER = "CROSS_ENCODER"
    LLM_RERANKER_EXPERIMENTAL = "LLM_RERANKER_EXPERIMENTAL"


@dataclass(frozen=True)
class RerankedCandidate:
    fused: FusedCandidate
    rerank_score: float
    features: dict


class RerankerPort(Protocol):
    def rerank(
        self, *, query_tokens: set, candidates: List[FusedCandidate], top_n: int,
        customer_id: Optional[str] = None, case_id: Optional[str] = None, as_of: Optional[date] = None,
    ) -> List[RerankedCandidate]: ...


_AUTHORITY_SCORE = {
    AuthorityTier.TIER_1_AUTHORITATIVE: 1.0, AuthorityTier.TIER_2_VERIFIED_INTERNAL: 0.8,
    AuthorityTier.TIER_3_CUSTOMER_PROVIDED_UNVERIFIED: 0.5, AuthorityTier.TIER_4_MODEL_INFERENCE: 0.2,
    AuthorityTier.TIER_5_UNSUPPORTED: 0.0, None: 0.3,
}
_VERIFICATION_SCORE = {
    VerificationStatus.VERIFIED: 1.0, VerificationStatus.PENDING: 0.5,
    VerificationStatus.UNVERIFIED: 0.3, VerificationStatus.REJECTED: 0.0, None: 0.3,
}


class HeuristicReranker:
    """Deterministic feature-based rerank -- Phase 3 section 27's required
    "bắt buộc có heuristic deterministic" mode. Weighted sum of features
    that are cheap to compute from data already on KnowledgeChunk/
    FusedCandidate; no network call, no model load."""

    def __init__(
        self,
        *,
        w_fusion: float = 0.35,
        w_exact_match: float = 0.15,
        w_authority: float = 0.15,
        w_verification: float = 0.15,
        w_freshness: float = 0.1,
        w_scope_match: float = 0.1,
    ) -> None:
        self.weights = dict(
            fusion=w_fusion, exact_match=w_exact_match, authority=w_authority,
            verification=w_verification, freshness=w_freshness, scope_match=w_scope_match,
        )

    def rerank(
        self, *, query_tokens: set, candidates: List[FusedCandidate], top_n: int,
        customer_id: Optional[str] = None, case_id: Optional[str] = None, as_of: Optional[date] = None,
    ) -> List[RerankedCandidate]:
        today = as_of or date.today()
        max_fusion = max((c.fused_score for c in candidates), default=1.0) or 1.0
        reranked: List[RerankedCandidate] = []
        for candidate in candidates:
            chunk = candidate.chunk
            chunk_text_lower = chunk.text.lower()
            # >= 3 (not > 3): short but meaningful acronyms like "UBO" are
            # exactly 3 characters -- an earlier threshold of len > 3
            # silently excluded them from the exact_match feature, found
            # by manual verification against a real Legal query ("UBO xac
            # minh") where it caused the correct UBO rule to lose ranking
            # after reranking. Still excludes 1-2 char tokens (Vietnamese
            # prepositions/particles too short to be a meaningful match).
            exact_match = 1.0 if any(tok in chunk_text_lower for tok in query_tokens if len(tok) >= 3) else 0.0
            authority = _AUTHORITY_SCORE.get(chunk.authority_tier, 0.3)
            verification = _VERIFICATION_SCORE.get(chunk.verification_status, 0.3)
            days_old = max(0, (today - chunk.effective_from).days)
            freshness = max(0.0, 1.0 - min(days_old, 1825) / 1825)
            scope_match = 1.0
            if customer_id is not None and chunk.customer_id is not None:
                scope_match = 1.0 if chunk.customer_id == customer_id else 0.0
            if case_id is not None and chunk.case_id is not None:
                scope_match = min(scope_match, 1.0 if chunk.case_id == case_id else 0.0)

            features = {
                "fusion": candidate.fused_score / max_fusion, "exact_match": exact_match,
                "authority": authority, "verification": verification, "freshness": freshness,
                "scope_match": scope_match,
            }
            score = sum(self.weights[k] * v for k, v in features.items())
            reranked.append(RerankedCandidate(fused=candidate, rerank_score=score, features=features))

        reranked.sort(key=lambda r: (-r.rerank_score, r.fused.chunk.chunk_id))
        return reranked[:top_n]
