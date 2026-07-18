"""Phase 1 section 6: real BM25 sparse retrieval, not the pre-existing
naive token-overlap ratio. bm25_scores() is tested standalone against
hand-verifiable properties first (pure function, no I/O), then
sparse_search_bm25() is tested as the PersistentHybridIndex-integrated
channel -- additive, does not change search()/search_with_diagnostics().
"""

from __future__ import annotations

from datetime import date

from app.knowledge.index import PersistentHybridIndex, bm25_scores, token_list
from app.knowledge.models import KnowledgeChunk


def test_bm25_scores_a_document_with_no_matching_terms_as_zero():
    scores = bm25_scores(["von", "luu", "dong"], [["thanh", "toan", "quoc", "te"]])
    assert scores == [0.0]


def test_bm25_scores_higher_term_frequency_higher_within_saturation():
    """BM25's term-frequency component saturates (diminishing returns),
    but a document repeating the query term must still never score lower
    than one that doesn't repeat it at all."""
    scores = bm25_scores(
        ["von"],
        [["von", "luu", "dong"], ["von", "von", "von", "von", "luu", "dong"]],
    )
    assert scores[1] > scores[0]


def test_bm25_scores_are_empty_list_length_matched_for_empty_query():
    scores = bm25_scores([], [["a", "b"], ["c", "d"]])
    assert scores == [0.0, 0.0]


def test_bm25_rewards_a_rare_term_over_a_common_term_via_idf():
    """A term appearing in only 1 of 10 documents (rare, high IDF) must
    score its matching document higher than a term appearing in 9 of 10
    documents (common, low IDF) would, all else equal -- this is the
    exact property naive token-overlap cannot express (it treats every
    matching token identically regardless of corpus frequency)."""
    common_term_docs = [["common", "x"] for _ in range(9)] + [["rare", "x"]]
    rare_query_scores = bm25_scores(["rare"], common_term_docs)
    common_query_scores = bm25_scores(["common"], common_term_docs)
    assert rare_query_scores[9] > common_query_scores[0]


def test_token_list_preserves_repeats_unlike_tokens_set():
    assert token_list("vốn vốn lưu động") == ["von", "von", "luu", "dong"]


def _chunk(chunk_id: str, text: str, *, product_id: str = "SYNTH-PROD-WORKING-CAPITAL") -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=chunk_id, document_id=f"DOC-{chunk_id}", document_version="1",
        product_id=product_id, section_path="1.1", text=text,
        effective_from=date(2026, 1, 1), effective_to=None, active=True,
        segments=[], access_scope={"branches": ["*"]}, content_hash=f"hash-{chunk_id}",
    )


def test_sparse_search_bm25_ranks_the_more_relevant_chunk_first(tmp_path):
    index = PersistentHybridIndex(tmp_path / "bm25.sqlite3")
    index.upsert(
        [
            _chunk("RELEVANT", "vốn lưu động điều kiện hồ sơ UBO báo cáo tài chính"),
            _chunk("IRRELEVANT", "thẻ tín dụng doanh nghiệp chi tiêu công tác"),
        ],
        source_hash="s1", dataset_version="v1",
    )
    hits = index.sparse_search_bm25("vốn lưu động UBO")
    assert hits, "expected at least one BM25 hit"
    assert hits[0].chunk.chunk_id == "RELEVANT"


def test_sparse_search_bm25_still_respects_branch_and_product_scope(tmp_path):
    index = PersistentHybridIndex(tmp_path / "bm25_scope.sqlite3")
    out_of_scope = KnowledgeChunk(
        chunk_id="SCOPED", document_id="DOC-SCOPED", document_version="1",
        product_id="SYNTH-PROD-WORKING-CAPITAL", section_path="1.1",
        text="vốn lưu động điều kiện hồ sơ",
        effective_from=date(2026, 1, 1), effective_to=None, active=True,
        segments=[], access_scope={"branches": ["OTHER-BRANCH"]}, content_hash="hash-scoped",
    )
    index.upsert([out_of_scope], source_hash="s2", dataset_version="v1")
    assert index.sparse_search_bm25("vốn lưu động điều kiện", branch="MY-BRANCH") == []


def test_sparse_search_bm25_does_not_affect_legacy_search(tmp_path):
    """Additive channel -- must not change search()'s existing token-
    overlap-based sparse component or its results."""
    index = PersistentHybridIndex(tmp_path / "bm25_no_side_effect.sqlite3")
    index.upsert([_chunk("C1", "vốn lưu động điều kiện hồ sơ")], source_hash="s3", dataset_version="v1")
    before = index.search("vốn lưu động", threshold=0.01)
    index.sparse_search_bm25("vốn lưu động")
    after = index.search("vốn lưu động", threshold=0.01)
    assert before == after
