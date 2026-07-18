"""Phase 2 section 8: IndexNamespace identity + mismatch detection. Not
created in Phase 1 (see Phase 1 report's "Tests" section explaining why an
empty test file for a not-yet-built feature was refused) -- now real
because namespace() exists."""

from __future__ import annotations

from datetime import date

from app.knowledge.index import IndexNamespace, LocalEmbedding, PersistentHybridIndex, RepresentationType, namespace_mismatch
from app.knowledge.models import KnowledgeChunk


def test_fresh_index_reports_unversioned_corpus(tmp_path):
    index = PersistentHybridIndex(tmp_path / "fresh.sqlite3", provider=LocalEmbedding())
    ns = index.namespace()
    assert ns.provider_id == "local"
    assert ns.representation_type == RepresentationType.HASH_BOW_VECTOR
    assert ns.dimension == 256
    assert ns.normalization == "l2"
    assert ns.corpus_version == "unversioned"


def test_namespace_corpus_version_reflects_latest_ingest(tmp_path):
    index = PersistentHybridIndex(tmp_path / "ingested.sqlite3", provider=LocalEmbedding())
    index.upsert(
        [
            KnowledgeChunk(
                chunk_id="C1", document_id="DOC-1", document_version="1", product_id="PROD-X",
                section_path="1.1", text="von luu dong", effective_from=date(2026, 1, 1),
                effective_to=None, active=True, segments=[], access_scope={"branches": ["*"]}, content_hash="h1",
            )
        ],
        source_hash="s1", dataset_version="v2.5",
    )
    assert index.namespace().corpus_version == "v2.5"


def test_two_local_embedding_indexes_have_the_same_namespace():
    ns_a = IndexNamespace(provider_id="local", representation_type=RepresentationType.HASH_BOW_VECTOR, dimension=256, normalization="l2", corpus_version="v1")
    ns_b = IndexNamespace(provider_id="local", representation_type=RepresentationType.HASH_BOW_VECTOR, dimension=256, normalization="l2", corpus_version="v2")
    assert namespace_mismatch(ns_a, ns_b) is False


def test_different_provider_is_a_namespace_mismatch():
    local_ns = IndexNamespace(provider_id="local", representation_type=RepresentationType.HASH_BOW_VECTOR, dimension=256, normalization="l2", corpus_version="v1")
    openai_ns = IndexNamespace(provider_id="openai-text-embedding-3-small", representation_type=RepresentationType.SEMANTIC_EMBEDDING, dimension=1536, normalization="unknown", corpus_version="v1")
    assert namespace_mismatch(local_ns, openai_ns) is True


def test_same_provider_different_dimension_is_a_namespace_mismatch():
    ns_a = IndexNamespace(provider_id="local", representation_type=RepresentationType.HASH_BOW_VECTOR, dimension=256, normalization="l2", corpus_version="v1")
    ns_b = IndexNamespace(provider_id="local", representation_type=RepresentationType.HASH_BOW_VECTOR, dimension=128, normalization="l2", corpus_version="v1")
    assert namespace_mismatch(ns_a, ns_b) is True
