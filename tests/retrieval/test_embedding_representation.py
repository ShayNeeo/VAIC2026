"""Phase 1 section 1: every EmbeddingProvider must honestly disclose what
kind of vector it produces. Before this, nothing in the codebase asserted
that LocalEmbedding (the default, used everywhere in tests/CI) is a hash
bag-of-words vector rather than a semantic embedding."""

from __future__ import annotations

from app.knowledge.index import (
    CachedGeminiEmbedding,
    CachedOpenAIEmbedding,
    LocalEmbedding,
    RepresentationType,
    RetrievalDiagnostics,
    RetrievalOutcomeCode,
)


def test_default_local_embedding_is_labelled_hash_bow_not_semantic():
    provider = LocalEmbedding()
    assert provider.representation_type == RepresentationType.HASH_BOW_VECTOR
    assert provider.representation_type != RepresentationType.SEMANTIC_EMBEDDING


def test_gemini_and_openai_providers_are_labelled_semantic(tmp_path):
    """Constructing these providers never makes a network call (that only
    happens inside .embed()), so the representation_type CLASSIFICATION
    can be asserted here without an API key or network access."""
    gemini = CachedGeminiEmbedding(cache_file=tmp_path / "gemini_cache.json")
    openai = CachedOpenAIEmbedding(cache_file=tmp_path / "openai_cache.json")
    assert gemini.representation_type == RepresentationType.SEMANTIC_EMBEDDING
    assert openai.representation_type == RepresentationType.SEMANTIC_EMBEDDING


def test_search_diagnostics_disclose_semantic_capability_false_for_default_provider(tmp_path):
    """Explicitly pins LocalEmbedding rather than relying on the ambient
    KNOWLEDGE_EMBEDDING_PROVIDER environment setting -- this repo's .env
    sets it to "openai" for real deployments, so asserting about "the
    default" without pinning would make this test's outcome depend on
    which environment it happens to run in, which is exactly the kind of
    dishonesty about representation type this Phase 1 work exists to
    prevent."""
    from datetime import date
    from app.knowledge.index import LocalEmbedding, PersistentHybridIndex
    from app.knowledge.models import KnowledgeChunk

    index = PersistentHybridIndex(tmp_path / "repr.sqlite3", provider=LocalEmbedding())
    index.upsert(
        [
            KnowledgeChunk(
                chunk_id="C1", document_id="DOC-1", document_version="1",
                product_id="SYNTH-PROD-PAYROLL", section_path="1.1", text="vốn lưu động",
                effective_from=date(2026, 1, 1), effective_to=None, active=True,
                segments=[], access_scope={"branches": ["*"]}, content_hash="hash-1",
            )
        ],
        source_hash="s1", dataset_version="v1",
    )
    _hits, diagnostics = index.search_with_diagnostics("vốn lưu động", threshold=0.01)
    assert diagnostics.representation_type == RepresentationType.HASH_BOW_VECTOR
    assert diagnostics.semantic_capability is False


def test_retrieval_diagnostics_defaults_are_honest_not_optimistic():
    """A RetrievalDiagnostics constructed without explicitly stating the
    representation type must default to the HONEST (non-semantic) label,
    not silently claim semantic capability."""
    diag = RetrievalDiagnostics(RetrievalOutcomeCode.OK, candidate_count=1, filtered_count=0)
    assert diag.representation_type == RepresentationType.HASH_BOW_VECTOR
    assert diag.semantic_capability is False
