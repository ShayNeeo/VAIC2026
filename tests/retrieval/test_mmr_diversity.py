"""Phase 3 section 28: MMR diversity -- must reduce near-duplicates while
never dropping protected (blocker/current-policy/conflict) candidates."""

from __future__ import annotations

from datetime import date

from app.knowledge.diversity import mmr_select
from app.knowledge.fusion import FusedCandidate
from app.knowledge.models import KnowledgeChunk
from app.knowledge.reranker import RerankedCandidate


def _reranked(chunk_id: str, text: str, score: float) -> RerankedCandidate:
    chunk = KnowledgeChunk(
        chunk_id=chunk_id, document_id=f"DOC-{chunk_id}", document_version="1", product_id="PROD-X",
        section_path="1.1", text=text, effective_from=date(2026, 1, 1), effective_to=None,
        active=True, segments=[], access_scope={"branches": ["*"]}, content_hash=f"h-{chunk_id}",
    )
    fused = FusedCandidate(chunk=chunk, fused_score=score, sparse_rank=1, dense_rank=1, sparse_score=score, dense_score=score)
    return RerankedCandidate(fused=fused, rerank_score=score, features={})


def test_near_duplicate_texts_are_not_both_selected_when_budget_is_tight():
    a = _reranked("C1", "von luu dong dieu kien ho so tai chinh", 0.9)
    b = _reranked("C2", "von luu dong dieu kien ho so tai chinh chi tiet", 0.85)  # near-duplicate of a
    c = _reranked("C3", "chi luong nhan su payroll", 0.5)  # distinct topic
    selected = mmr_select([a, b, c], top_k=2, lambda_relevance=0.5)
    ids = {r.fused.chunk.chunk_id for r in selected}
    assert "C1" in ids  # highest relevance always wins the first slot
    assert "C3" in ids  # more novel than the near-duplicate C2


def test_protected_candidates_are_never_dropped_even_beyond_budget():
    blocker = _reranked("BLOCKER", "khong the phe duyet do thieu UBO", 0.1)
    a = _reranked("C1", "text a", 0.9)
    b = _reranked("C2", "text b", 0.9)
    selected = mmr_select([blocker, a, b], top_k=1, protected_chunk_ids=["BLOCKER"])
    ids = {r.fused.chunk.chunk_id for r in selected}
    assert "BLOCKER" in ids


def test_empty_candidates_returns_empty():
    assert mmr_select([], top_k=5) == []


def test_top_k_respected_when_no_protected_candidates():
    candidates = [_reranked(f"C{i}", f"text unique {i}", 1.0 - i * 0.1) for i in range(5)]
    selected = mmr_select(candidates, top_k=2)
    assert len(selected) == 2
