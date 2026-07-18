"""Fusion strategies for combining independent sparse/dense rankings --
RAG & Guardrail Implementation Plan Phase 2 section 9.

Two channels' raw scores are NOT comparable numbers: BM25 is an unbounded
sum of IDF-weighted term contributions, dense cosine-like similarity is
bounded [0, 1] (or a hash-BoW collision proxy for it, see
app.knowledge.index.RepresentationType). Adding them directly (as the
legacy search_with_diagnostics() linear-sum does, deliberately kept as-is
for backward compatibility -- see LINEAR_SUM_LEGACY below) conflates two
different measurement scales. Reciprocal Rank Fusion (RRF) sidesteps this
by fusing on RANK within each channel, not on raw score -- the standard
approach ("Reciprocal Rank Fusion outperforms Condorcet and individual
rank learning methods", Cormack et al. 2009) precisely because it needs no
score calibration between channels.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Protocol

from app.knowledge.models import KnowledgeChunk, RetrievalHit


class FusionMode(str, Enum):
    LINEAR_SUM_LEGACY = "LINEAR_SUM_LEGACY"
    RRF = "RRF"


@dataclass(frozen=True)
class FusedCandidate:
    chunk: KnowledgeChunk
    fused_score: float
    sparse_rank: int | None
    dense_rank: int | None
    sparse_score: float | None
    dense_score: float | None


class FusionStrategy(Protocol):
    def fuse(
        self,
        sparse_results: List[RetrievalHit],
        dense_results: List[RetrievalHit],
        *,
        top_k: int,
    ) -> List[FusedCandidate]: ...


@dataclass
class ReciprocalRankFusion:
    """score(chunk) = sum_over_channels( weight / (rrf_k + rank_in_channel) ).

    rrf_k=60 is the value used in the original TREC experiments and is
    this module's default -- not independently re-tuned for this corpus
    (Phase 2's ablation, see docs/RAG_ABLATION_REPORT.md, evaluates this
    default against the alternatives; it does not claim rrf_k=60 is
    locally optimal). sparse_weight/dense_weight let a caller (an
    AgentType's RetrievalPolicy) bias fusion toward one channel -- see
    app/knowledge/agent_retrieval_policies.py's *_weight fields, wired in
    by ControlledRetrievalOrchestrator.

    Tie-breaking is deterministic (Phase 2 section 9): equal fused_score
    resolves by (1) higher authority tier, (2) currently effective
    (is_superseded=False already guaranteed by the security pre-filter
    upstream, so this only distinguishes further by effective_from
    recency), (3) verified over unverified, (4) exact product_id match in
    chunk_id is not decidable here so is skipped, (5) chunk_id string order
    for a fully stable sort.
    """

    rrf_k: int = 60
    sparse_weight: float = 1.0
    dense_weight: float = 1.0

    def fuse(
        self,
        sparse_results: List[RetrievalHit],
        dense_results: List[RetrievalHit],
        *,
        top_k: int = 5,
    ) -> List[FusedCandidate]:
        sparse_rank: Dict[str, int] = {hit.chunk.chunk_id: i + 1 for i, hit in enumerate(sparse_results)}
        dense_rank: Dict[str, int] = {hit.chunk.chunk_id: i + 1 for i, hit in enumerate(dense_results)}
        sparse_score: Dict[str, float] = {hit.chunk.chunk_id: hit.sparse_score for hit in sparse_results}
        dense_score: Dict[str, float] = {hit.chunk.chunk_id: hit.dense_score for hit in dense_results}
        chunks: Dict[str, KnowledgeChunk] = {hit.chunk.chunk_id: hit.chunk for hit in [*sparse_results, *dense_results]}

        fused: List[FusedCandidate] = []
        for chunk_id, chunk in chunks.items():
            s_rank = sparse_rank.get(chunk_id)
            d_rank = dense_rank.get(chunk_id)
            score = 0.0
            if s_rank is not None:
                score += self.sparse_weight / (self.rrf_k + s_rank)
            if d_rank is not None:
                score += self.dense_weight / (self.rrf_k + d_rank)
            fused.append(
                FusedCandidate(
                    chunk=chunk, fused_score=score, sparse_rank=s_rank, dense_rank=d_rank,
                    sparse_score=sparse_score.get(chunk_id), dense_score=dense_score.get(chunk_id),
                )
            )

        def _tie_break_key(candidate: FusedCandidate) -> tuple:
            tier_rank = {
                None: 5, "TIER_1_AUTHORITATIVE": 0, "TIER_2_VERIFIED_INTERNAL": 1,
                "TIER_3_CUSTOMER_PROVIDED_UNVERIFIED": 2, "TIER_4_MODEL_INFERENCE": 3, "TIER_5_UNSUPPORTED": 4,
            }
            authority = candidate.chunk.authority_tier.value if candidate.chunk.authority_tier else None
            verified = 0 if (candidate.chunk.verification_status and candidate.chunk.verification_status.value == "verified") else 1
            return (
                -candidate.fused_score,
                tier_rank.get(authority, 5),
                verified,
                -candidate.chunk.effective_from.toordinal(),
                candidate.chunk.chunk_id,
            )

        fused.sort(key=_tie_break_key)
        return fused[:top_k]


@dataclass
class LinearSumFusion:
    """Standalone re-implementation of the legacy linear-sum formula
    (0.6*dense + 0.4*sparse) for ABLATION purposes only -- this is NOT
    wired into search()/search_with_diagnostics() (those keep their own
    inline implementation untouched, see app/knowledge/index.py). This
    class exists so docs/RAG_ABLATION_REPORT.md can compare "legacy
    formula, run over the same independently-ranked sparse/dense channels
    as RRF" on equal footing, rather than comparing RRF against a
    differently-shaped legacy code path (which also folds in exact_bonus
    and a token-overlap sparse proxy instead of real BM25)."""

    dense_weight: float = 0.6
    sparse_weight: float = 0.4

    def fuse(
        self,
        sparse_results: List[RetrievalHit],
        dense_results: List[RetrievalHit],
        *,
        top_k: int = 5,
    ) -> List[FusedCandidate]:
        sparse_score: Dict[str, float] = {hit.chunk.chunk_id: hit.sparse_score for hit in sparse_results}
        dense_score: Dict[str, float] = {hit.chunk.chunk_id: hit.dense_score for hit in dense_results}
        sparse_rank: Dict[str, int] = {hit.chunk.chunk_id: i + 1 for i, hit in enumerate(sparse_results)}
        dense_rank: Dict[str, int] = {hit.chunk.chunk_id: i + 1 for i, hit in enumerate(dense_results)}
        chunks: Dict[str, KnowledgeChunk] = {hit.chunk.chunk_id: hit.chunk for hit in [*sparse_results, *dense_results]}

        fused = []
        for chunk_id, chunk in chunks.items():
            s = sparse_score.get(chunk_id, 0.0)
            d = dense_score.get(chunk_id, 0.0)
            score = self.dense_weight * d + self.sparse_weight * s
            fused.append(
                FusedCandidate(
                    chunk=chunk, fused_score=score,
                    sparse_rank=sparse_rank.get(chunk_id), dense_rank=dense_rank.get(chunk_id),
                    sparse_score=sparse_score.get(chunk_id), dense_score=dense_score.get(chunk_id),
                )
            )
        fused.sort(key=lambda c: (-c.fused_score, c.chunk.chunk_id))
        return fused[:top_k]
