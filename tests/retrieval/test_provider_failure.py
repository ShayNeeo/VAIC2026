"""Phase 0 of docs/RAG_GUARDRAIL_IMPLEMENTATION_PLAN.md: PersistentHybridIndex
must distinguish *why* a search returned zero hits instead of collapsing
"corpus has nothing relevant", "index has no chunks at all", and "query had
no indexable tokens" into the same bare ``[]`` -- see
docs/RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md section 1 / prompt section 21
("Không silently chuyển: retrieval provider failure -> no results").

search() itself is asserted to be byte-for-byte unchanged in behavior (same
signature, same return type, same results) -- search_with_diagnostics() is a
strictly additive method, not a replacement.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.knowledge.index import PersistentHybridIndex, RetrievalOutcomeCode
from app.knowledge.models import KnowledgeChunk


def _chunk(chunk_id: str, *, product_id: str = "PROD-WORKING-CAPITAL", text: str = "vốn lưu động điều kiện hồ sơ") -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=chunk_id,
        document_id=f"DOC-{chunk_id}",
        document_version="1",
        product_id=product_id,
        section_path="1.1",
        text=text,
        effective_from=date(2026, 1, 1),
        effective_to=None,
        active=True,
        segments=["SME"],
        access_scope={"branches": ["*"]},
        content_hash=f"hash-{chunk_id}",
    )


@pytest.fixture()
def empty_index(tmp_path) -> PersistentHybridIndex:
    return PersistentHybridIndex(tmp_path / "empty.sqlite3")


@pytest.fixture()
def populated_index(tmp_path) -> PersistentHybridIndex:
    index = PersistentHybridIndex(tmp_path / "populated.sqlite3")
    index.upsert([_chunk("C1")], source_hash="src-1", dataset_version="v1")
    return index


def test_empty_index_reports_index_not_ready_not_bare_empty_list(empty_index):
    hits, diagnostics = empty_index.search_with_diagnostics("vốn lưu động")
    assert hits == []
    assert diagnostics.outcome == RetrievalOutcomeCode.INDEX_NOT_READY
    assert diagnostics.candidate_count == 0


def test_stopword_only_query_reports_empty_query_not_no_relevant_result(populated_index):
    """A query with zero indexable tokens (e.g. only stopwords) says
    nothing about whether the corpus covers the topic -- must not be
    reported the same way as a genuine "searched the corpus, nothing
    matched" outcome."""
    hits, diagnostics = populated_index.search_with_diagnostics("là và của")
    assert hits == []
    assert diagnostics.outcome == RetrievalOutcomeCode.EMPTY_QUERY


def test_populated_index_with_no_matching_content_reports_no_relevant_result(populated_index):
    hits, diagnostics = populated_index.search_with_diagnostics("chính sách ngoại hối quốc tế xuất khẩu")
    assert hits == []
    assert diagnostics.outcome == RetrievalOutcomeCode.NO_RELEVANT_RESULT
    assert diagnostics.candidate_count == 1


def test_successful_search_reports_ok(populated_index):
    hits, diagnostics = populated_index.search_with_diagnostics("vốn lưu động", threshold=0.01)
    assert len(hits) == 1
    assert diagnostics.outcome == RetrievalOutcomeCode.OK
    assert diagnostics.candidate_count == 1


def test_filtered_count_reflects_scope_exclusions(tmp_path):
    index = PersistentHybridIndex(tmp_path / "scoped.sqlite3")
    in_scope = _chunk("IN-SCOPE")
    out_of_scope = KnowledgeChunk(
        chunk_id="OUT-OF-SCOPE", document_id="DOC-OUT", document_version="1",
        product_id="PROD-WORKING-CAPITAL", section_path="1.1",
        text="vốn lưu động điều kiện hồ sơ", effective_from=date(2026, 1, 1),
        effective_to=None, active=True, segments=["SME"],
        access_scope={"branches": ["HN01-ONLY"]}, content_hash="hash-out",
    )
    index.upsert([in_scope, out_of_scope], source_hash="src-2", dataset_version="v1")

    hits, diagnostics = index.search_with_diagnostics("vốn lưu động", branch="HCM01", threshold=0.01)
    assert diagnostics.candidate_count == 2
    assert diagnostics.filtered_count == 1
    assert len(hits) == 1
    assert hits[0].chunk.chunk_id == "IN-SCOPE"


def test_search_behavior_is_unchanged_by_the_diagnostics_refactor(populated_index):
    """search() must remain byte-for-byte identical for the 375+ existing
    callers in this repo -- this test would fail if search_with_diagnostics
    accidentally changed scoring, filtering, or ranking behavior."""
    via_search = populated_index.search("vốn lưu động", threshold=0.01)
    via_diagnostics, _ = populated_index.search_with_diagnostics("vốn lưu động", threshold=0.01)
    assert via_search == via_diagnostics
