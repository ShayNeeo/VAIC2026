"""Phase 1 section 9/11: legacy search() must remain compatible after every
Phase 1 addition (RepresentationType, MetadataFilterReason, exact lookup,
BM25 channel) -- same signature, same return type, same results for the
375+ pre-existing call sites across this repo (ProductKnowledgeService,
LegalKnowledgeService, evidence_validator, benchmarks/, etc.)."""

from __future__ import annotations

from datetime import date

from app.knowledge.index import PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk, RetrievalHit


def _chunk(chunk_id: str) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=chunk_id, document_id=f"DOC-{chunk_id}", document_version="1",
        product_id="SYNTH-PROD-WORKING-CAPITAL", section_path="1.1",
        text="vốn lưu động điều kiện hồ sơ",
        effective_from=date(2026, 1, 1), effective_to=None, active=True,
        segments=[], access_scope={"branches": ["*"]}, content_hash=f"hash-{chunk_id}",
    )


def test_search_still_returns_a_plain_list_of_retrieval_hit(tmp_path):
    index = PersistentHybridIndex(tmp_path / "legacy.sqlite3")
    index.upsert([_chunk("C1")], source_hash="s1", dataset_version="v1")
    result = index.search("vốn lưu động", threshold=0.01)
    assert isinstance(result, list)
    assert all(isinstance(item, RetrievalHit) for item in result)


def test_search_on_empty_index_still_returns_bare_empty_list_not_a_tuple(tmp_path):
    """search() (unlike search_with_diagnostics()) must keep returning a
    bare [] even for INDEX_NOT_READY -- callers that pattern-match on
    List[RetrievalHit] must not suddenly receive a tuple."""
    index = PersistentHybridIndex(tmp_path / "legacy_empty.sqlite3")
    result = index.search("bất kỳ câu hỏi")
    assert result == []
    assert not isinstance(result, tuple)


def test_search_signature_accepts_every_pre_existing_keyword_argument(tmp_path):
    """ProductKnowledgeService/LegalKnowledgeService call search() with
    branch=, segment=, as_of=, product_ids=, threshold= -- all must still
    be accepted after the Phase 1 refactor."""
    index = PersistentHybridIndex(tmp_path / "legacy_kwargs.sqlite3")
    index.upsert([_chunk("C1")], source_hash="s1", dataset_version="v1")
    result = index.search(
        "vốn lưu động", top_k=3, branch="*", segment=None, as_of=date(2026, 6, 1),
        product_ids=["SYNTH-PROD-WORKING-CAPITAL"], threshold=0.01,
    )
    assert len(result) == 1
