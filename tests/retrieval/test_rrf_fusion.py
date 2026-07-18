"""Phase 2 section 9: RRF fuses by RANK, not raw score -- a low-raw-score
candidate ranked #1 in both channels must outscore a high-raw-score
candidate that only appears in one channel low down. This is the
property that makes RRF meaningfully different from LinearSumFusion
(which is dominated by whichever channel has the larger raw-score scale)."""

from __future__ import annotations

from datetime import date

from app.knowledge.fusion import LinearSumFusion, ReciprocalRankFusion
from app.knowledge.models import KnowledgeChunk, RetrievalHit


def _chunk(chunk_id: str) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=chunk_id, document_id=f"DOC-{chunk_id}", document_version="1", product_id="PROD-X",
        section_path="1.1", text="text", effective_from=date(2026, 1, 1), effective_to=None,
        active=True, segments=[], access_scope={"branches": ["*"]}, content_hash=f"h-{chunk_id}",
    )


def _hit(chunk_id: str, score: float, *, dense: float = 0.0, sparse: float = 0.0) -> RetrievalHit:
    return RetrievalHit(chunk=_chunk(chunk_id), score=score, dense_score=dense, sparse_score=sparse)


def test_rrf_rewards_a_candidate_ranked_first_in_both_channels():
    sparse = [_hit("A", 0.9, sparse=0.9), _hit("B", 0.1, sparse=0.1)]
    dense = [_hit("A", 0.9, dense=0.9), _hit("B", 0.1, dense=0.1)]
    fused = ReciprocalRankFusion().fuse(sparse, dense, top_k=5)
    assert fused[0].chunk.chunk_id == "A"


def test_rrf_score_formula_matches_hand_computation():
    sparse = [_hit("A", 1.0, sparse=1.0)]
    dense = [_hit("B", 1.0, dense=1.0), _hit("A", 0.5, dense=0.5)]
    fused = ReciprocalRankFusion(rrf_k=60, sparse_weight=1.0, dense_weight=1.0).fuse(sparse, dense, top_k=5)
    by_id = {c.chunk.chunk_id: c for c in fused}
    # A: sparse rank 1 -> 1/61 ; dense rank 2 -> 1/62
    assert abs(by_id["A"].fused_score - (1 / 61 + 1 / 62)) < 1e-9
    # B: dense rank 1 only -> 1/61
    assert abs(by_id["B"].fused_score - (1 / 61)) < 1e-9


def test_rrf_per_agent_weight_biases_the_favored_channel():
    sparse = [_hit("A", 1.0, sparse=1.0)]
    dense = [_hit("B", 1.0, dense=1.0)]
    legal_like = ReciprocalRankFusion(sparse_weight=1.3, dense_weight=0.7).fuse(sparse, dense, top_k=5)
    by_id = {c.chunk.chunk_id: c for c in legal_like}
    assert by_id["A"].fused_score > by_id["B"].fused_score


def test_candidate_present_in_only_one_channel_still_gets_a_score():
    sparse = [_hit("A", 1.0, sparse=1.0)]
    dense: list[RetrievalHit] = []
    fused = ReciprocalRankFusion().fuse(sparse, dense, top_k=5)
    assert len(fused) == 1
    assert fused[0].sparse_rank == 1
    assert fused[0].dense_rank is None


def test_linear_sum_fusion_reproduces_the_060_040_legacy_formula():
    sparse = [_hit("A", 0.0, sparse=0.4)]
    dense = [_hit("A", 0.0, dense=0.8)]
    fused = LinearSumFusion(dense_weight=0.6, sparse_weight=0.4).fuse(sparse, dense, top_k=5)
    assert abs(fused[0].fused_score - (0.6 * 0.8 + 0.4 * 0.4)) < 1e-9


def test_empty_channels_produce_no_candidates():
    assert ReciprocalRankFusion().fuse([], [], top_k=5) == []
