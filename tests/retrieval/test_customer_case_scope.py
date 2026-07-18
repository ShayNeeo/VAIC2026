"""Phase 2 section 6: real customer_id/case_id fields on KnowledgeChunk
(superseding Phase 1's branch-scope PROXY test, see
tests/retrieval/test_cross_customer_filtering.py's own docstring
explaining that proxy). A customer-specific chunk must only be visible to
a request naming that exact customer_id; a chunk with no customer_id
(generic product/policy/SOP) must never be filtered on this dimension."""

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


def test_customer_specific_chunk_is_hidden_from_a_different_customer(tmp_path):
    index = PersistentHybridIndex(tmp_path / "cust.sqlite3", provider=LocalEmbedding())
    index.upsert([_chunk("C1", customer_id="COMP-ABC")], source_hash="s1", dataset_version="v1")
    assert index.sparse_search_bm25("von luu dong", customer_id="COMP-XYZ") == []
    assert len(index.sparse_search_bm25("von luu dong", customer_id="COMP-ABC")) == 1


def test_customer_specific_chunk_is_visible_when_no_customer_id_is_requested(tmp_path):
    """Not passing customer_id= at all means 'do not filter on this
    dimension' -- every pre-Phase-2 caller."""
    index = PersistentHybridIndex(tmp_path / "cust2.sqlite3", provider=LocalEmbedding())
    index.upsert([_chunk("C1", customer_id="COMP-ABC")], source_hash="s1", dataset_version="v1")
    assert len(index.sparse_search_bm25("von luu dong")) == 1


def test_generic_chunk_with_no_customer_id_is_never_rejected_on_customer_scope(tmp_path):
    index = PersistentHybridIndex(tmp_path / "generic.sqlite3", provider=LocalEmbedding())
    index.upsert([_chunk("C1", customer_id=None)], source_hash="s1", dataset_version="v1")
    assert len(index.sparse_search_bm25("von luu dong", customer_id="COMP-XYZ")) == 1


def test_case_scope_follows_the_same_rule_as_customer_scope(tmp_path):
    index = PersistentHybridIndex(tmp_path / "case.sqlite3", provider=LocalEmbedding())
    index.upsert([_chunk("C1", case_id="CASE-001")], source_hash="s1", dataset_version="v1")
    assert index.dense_search("von luu dong", case_id="CASE-999") == []
    assert len(index.dense_search("von luu dong", case_id="CASE-001")) == 1
