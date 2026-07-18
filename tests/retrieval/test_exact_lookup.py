"""Phase 1 section 4: Exact Structured Lookup. A request that already names
a specific chunk_id or product_id must be answered by a direct key lookup
(or a filtered-but-unscored scan for product_id), never by running it back
through semantic/sparse scoring to "guess" the intended entity."""

from __future__ import annotations

from datetime import date

import pytest

from app.knowledge.index import PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk


def _chunk(chunk_id: str, product_id: str, *, branches=("*",), text: str = "nội dung") -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=chunk_id, document_id=f"DOC-{chunk_id}", document_version="1",
        product_id=product_id, section_path="1.1", text=text,
        effective_from=date(2026, 1, 1), effective_to=None, active=True,
        segments=[], access_scope={"branches": list(branches)}, content_hash=f"hash-{chunk_id}",
    )


@pytest.fixture()
def index(tmp_path) -> PersistentHybridIndex:
    idx = PersistentHybridIndex(tmp_path / "exact.sqlite3")
    idx.upsert(
        [_chunk("C1", "SYNTH-PROD-PAYROLL"), _chunk("C2", "SYNTH-PROD-PAYROLL"), _chunk("C3", "SYNTH-PROD-WORKING-CAPITAL")],
        source_hash="s1", dataset_version="v1",
    )
    return idx


def test_exact_lookup_by_chunk_id_returns_the_named_chunk_not_a_semantic_match(index):
    chunk = index.exact_lookup_by_chunk_id("C1")
    assert chunk is not None
    assert chunk.chunk_id == "C1"


def test_exact_lookup_by_chunk_id_returns_none_not_an_empty_semantic_scan(index):
    """An unknown chunk_id must be a clean None (EXACT_ENTITY_NOT_FOUND at
    the caller level), not silently fall through to sparse/dense search."""
    assert index.exact_lookup_by_chunk_id("DOES-NOT-EXIST") is None


def test_exact_lookup_by_product_id_returns_every_matching_chunk_unscored(index):
    chunks = index.exact_lookup_by_product_id("SYNTH-PROD-PAYROLL")
    assert {c.chunk_id for c in chunks} == {"C1", "C2"}


def test_exact_lookup_by_product_id_does_not_return_a_different_product(index):
    chunks = index.exact_lookup_by_product_id("SYNTH-PROD-WORKING-CAPITAL")
    assert {c.chunk_id for c in chunks} == {"C3"}


def test_exact_lookup_by_product_id_still_enforces_branch_scope(tmp_path):
    """An exact ID does not bypass access control -- see docstring on
    exact_lookup_by_product_id."""
    idx = PersistentHybridIndex(tmp_path / "exact_scope.sqlite3")
    idx.upsert([_chunk("SCOPED", "SYNTH-PROD-PAYROLL", branches=("HN01-ONLY",))], source_hash="s2", dataset_version="v1")
    assert idx.exact_lookup_by_product_id("SYNTH-PROD-PAYROLL", branch="HCM01") == []
    assert len(idx.exact_lookup_by_product_id("SYNTH-PROD-PAYROLL", branch="HN01-ONLY")) == 1


def test_exact_lookup_by_product_id_excludes_expired_chunks(tmp_path):
    idx = PersistentHybridIndex(tmp_path / "exact_expiry.sqlite3")
    expired = KnowledgeChunk(
        chunk_id="EXPIRED", document_id="DOC-EXPIRED", document_version="1",
        product_id="SYNTH-PROD-PAYROLL", section_path="1.1", text="cũ",
        effective_from=date(2020, 1, 1), effective_to=date(2021, 1, 1), active=True,
        segments=[], access_scope={"branches": ["*"]}, content_hash="hash-expired",
    )
    idx.upsert([expired], source_hash="s3", dataset_version="v1")
    assert idx.exact_lookup_by_product_id("SYNTH-PROD-PAYROLL", as_of=date(2026, 1, 1)) == []
