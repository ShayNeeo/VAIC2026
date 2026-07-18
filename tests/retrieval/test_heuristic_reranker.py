"""Phase 3 section 27: deterministic heuristic reranker."""

from __future__ import annotations

from datetime import date

from app.knowledge.fusion import FusedCandidate
from app.knowledge.models import KnowledgeChunk
from app.knowledge.reranker import HeuristicReranker
from app.knowledge.retrieval_contracts import AuthorityTier, VerificationStatus


def _candidate(chunk_id: str, *, text: str, fused_score: float = 0.5, **overrides) -> FusedCandidate:
    base = dict(
        chunk_id=chunk_id, document_id=f"DOC-{chunk_id}", document_version="1", product_id="PROD-X",
        section_path="1.1", text=text, effective_from=date(2026, 1, 1), effective_to=None,
        active=True, segments=[], access_scope={"branches": ["*"]}, content_hash=f"h-{chunk_id}",
    )
    base.update(overrides)
    chunk = KnowledgeChunk(**base)
    return FusedCandidate(chunk=chunk, fused_score=fused_score, sparse_rank=1, dense_rank=1, sparse_score=0.5, dense_score=0.5)


def test_higher_authority_and_verification_outranks_equal_fusion_score():
    reranker = HeuristicReranker()
    strong = _candidate(
        "C1", text="von luu dong dieu kien", fused_score=0.5,
        authority_tier=AuthorityTier.TIER_1_AUTHORITATIVE, verification_status=VerificationStatus.VERIFIED,
    )
    weak = _candidate(
        "C2", text="von luu dong dieu kien", fused_score=0.5,
        authority_tier=AuthorityTier.TIER_4_MODEL_INFERENCE, verification_status=VerificationStatus.UNVERIFIED,
    )
    result = reranker.rerank(query_tokens={"von", "luu", "dong"}, candidates=[weak, strong], top_n=5)
    assert result[0].fused.chunk.chunk_id == "C1"


def test_wrong_customer_scope_is_penalized():
    reranker = HeuristicReranker()
    right_scope = _candidate("C1", text="thong tin khach hang", fused_score=0.5, customer_id="COMP-ABC")
    wrong_scope = _candidate("C2", text="thong tin khach hang", fused_score=0.5, customer_id="COMP-XYZ")
    result = reranker.rerank(
        query_tokens={"thong", "tin"}, candidates=[wrong_scope, right_scope], top_n=5, customer_id="COMP-ABC",
    )
    assert result[0].fused.chunk.chunk_id == "C1"


def test_top_n_is_respected():
    reranker = HeuristicReranker()
    candidates = [_candidate(f"C{i}", text="text", fused_score=0.1 * i) for i in range(10)]
    result = reranker.rerank(query_tokens=set(), candidates=candidates, top_n=3)
    assert len(result) == 3


def test_rerank_is_deterministic_across_repeated_calls():
    reranker = HeuristicReranker()
    candidates = [_candidate("C1", text="text a", fused_score=0.5), _candidate("C2", text="text b", fused_score=0.5)]
    first = [r.fused.chunk.chunk_id for r in reranker.rerank(query_tokens=set(), candidates=candidates, top_n=5)]
    second = [r.fused.chunk.chunk_id for r in reranker.rerank(query_tokens=set(), candidates=candidates, top_n=5)]
    assert first == second
