"""Phase 2 section 5/6: is_superseded/is_quarantined must actually reject a
chunk before scoring, now that KnowledgeChunk carries the fields (Phase 1
could not test this -- the fields did not exist yet)."""

from __future__ import annotations

from datetime import date

from app.knowledge.index import LocalEmbedding, PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk


def _chunk(chunk_id: str, **overrides) -> KnowledgeChunk:
    base = dict(
        chunk_id=chunk_id, document_id=f"DOC-{chunk_id}", document_version="1", product_id="PROD-X",
        section_path="1.1", text="von luu dong dieu kien ho so",
        effective_from=date(2026, 1, 1), effective_to=None, active=True, segments=[],
        access_scope={"branches": ["*"]}, content_hash=f"hash-{chunk_id}",
    )
    base.update(overrides)
    return KnowledgeChunk(**base)


def test_superseded_chunk_is_excluded_from_sparse_and_dense_channels(tmp_path):
    index = PersistentHybridIndex(tmp_path / "sup.sqlite3", provider=LocalEmbedding())
    index.upsert([_chunk("C1", is_superseded=True)], source_hash="s1", dataset_version="v1")
    assert index.sparse_search_bm25("von luu dong") == []
    assert index.dense_search("von luu dong") == []


def test_quarantined_chunk_is_excluded_from_sparse_and_dense_channels(tmp_path):
    index = PersistentHybridIndex(tmp_path / "quar.sqlite3", provider=LocalEmbedding())
    index.upsert([_chunk("C1", is_quarantined=True)], source_hash="s1", dataset_version="v1")
    assert index.sparse_search_bm25("von luu dong") == []
    assert index.dense_search("von luu dong") == []


def test_lifecycle_filters_are_reported_in_filtered_reasons(tmp_path):
    index = PersistentHybridIndex(tmp_path / "reasons.sqlite3", provider=LocalEmbedding())
    total, eligible, reasons = index.eligibility_diagnostics()
    assert (total, eligible, reasons) == (0, 0, {})

    index.upsert(
        [_chunk("C1", is_superseded=True), _chunk("C2", is_quarantined=True), _chunk("C3")],
        source_hash="s1", dataset_version="v1",
    )
    total, eligible, reasons = index.eligibility_diagnostics()
    assert total == 3
    assert eligible == 1
    assert reasons == {"SOURCE_SUPERSEDED": 1, "SOURCE_QUARANTINED": 1}


def test_non_superseded_non_quarantined_chunk_is_unaffected(tmp_path):
    index = PersistentHybridIndex(tmp_path / "clean.sqlite3", provider=LocalEmbedding())
    index.upsert([_chunk("C1")], source_hash="s1", dataset_version="v1")
    assert len(index.sparse_search_bm25("von luu dong")) == 1
    assert len(index.dense_search("von luu dong")) == 1


def test_security_classification_allow_list_rejects_disallowed_chunk(tmp_path):
    index = PersistentHybridIndex(tmp_path / "secclass.sqlite3", provider=LocalEmbedding())
    index.upsert(
        [_chunk("C1", security_classification="RESTRICTED")], source_hash="s1", dataset_version="v1",
    )
    assert index.sparse_search_bm25("von luu dong", allowed_security_classifications=["INTERNAL"]) == []
    assert len(index.sparse_search_bm25("von luu dong", allowed_security_classifications=["INTERNAL", "RESTRICTED"])) == 1


def test_security_classification_not_enforced_when_caller_omits_it(tmp_path):
    index = PersistentHybridIndex(tmp_path / "secclass2.sqlite3", provider=LocalEmbedding())
    index.upsert(
        [_chunk("C1", security_classification="RESTRICTED")], source_hash="s1", dataset_version="v1",
    )
    assert len(index.sparse_search_bm25("von luu dong")) == 1
