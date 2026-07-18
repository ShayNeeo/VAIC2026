"""Phase 1 section 5: metadata filtering is a hard security boundary and
must run before ranking, with a reason code recorded for every excluded
candidate -- not just a bare filtered_count."""

from __future__ import annotations

from datetime import date

from app.knowledge.index import MetadataFilterReason, PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk


def _chunk(chunk_id: str, **overrides) -> KnowledgeChunk:
    base = dict(
        chunk_id=chunk_id, document_id=f"DOC-{chunk_id}", document_version="1",
        product_id="SYNTH-PROD-WORKING-CAPITAL", section_path="1.1", text="vốn lưu động điều kiện",
        effective_from=date(2026, 1, 1), effective_to=None, active=True,
        segments=["SME"], access_scope={"branches": ["*"]}, content_hash=f"hash-{chunk_id}",
    )
    base.update(overrides)
    return KnowledgeChunk(**base)


def test_expired_chunk_is_reported_as_source_not_effective(tmp_path):
    index = PersistentHybridIndex(tmp_path / "meta1.sqlite3")
    index.upsert(
        [_chunk("EXPIRED", effective_to=date(2025, 1, 1)), _chunk("FRESH")],
        source_hash="s1", dataset_version="v1",
    )
    hits, diagnostics = index.search_with_diagnostics("vốn lưu động", branch="*", threshold=0.01)
    assert len(hits) == 1
    assert diagnostics.filtered_reasons.get(MetadataFilterReason.SOURCE_NOT_EFFECTIVE.value) == 1


def test_out_of_branch_chunk_is_reported_as_source_scope_mismatch(tmp_path):
    index = PersistentHybridIndex(tmp_path / "meta2.sqlite3")
    index.upsert(
        [_chunk("OUT_OF_BRANCH", access_scope={"branches": ["HCM01-ONLY"]}), _chunk("IN_BRANCH")],
        source_hash="s2", dataset_version="v1",
    )
    hits, diagnostics = index.search_with_diagnostics("vốn lưu động", branch="HN01", threshold=0.01)
    assert {h.chunk.chunk_id for h in hits} == {"IN_BRANCH"}
    assert diagnostics.filtered_reasons.get(MetadataFilterReason.SOURCE_SCOPE_MISMATCH.value) == 1


def test_wrong_product_scope_is_reported_as_agent_source_not_allowed(tmp_path):
    index = PersistentHybridIndex(tmp_path / "meta3.sqlite3")
    index.upsert(
        [_chunk("OTHER_PRODUCT", product_id="SYNTH-PROD-PAYROLL"), _chunk("TARGET_PRODUCT")],
        source_hash="s3", dataset_version="v1",
    )
    hits, diagnostics = index.search_with_diagnostics(
        "vốn lưu động", product_ids=["SYNTH-PROD-WORKING-CAPITAL"], threshold=0.01,
    )
    assert {h.chunk.chunk_id for h in hits} == {"TARGET_PRODUCT"}
    assert diagnostics.filtered_reasons.get(MetadataFilterReason.AGENT_SOURCE_NOT_ALLOWED.value) == 1


def test_multiple_exclusion_reasons_are_all_counted_independently(tmp_path):
    index = PersistentHybridIndex(tmp_path / "meta4.sqlite3")
    index.upsert(
        [
            _chunk("EXPIRED_1", effective_to=date(2025, 1, 1)),
            _chunk("EXPIRED_2", effective_to=date(2025, 1, 1)),
            _chunk("SCOPED", access_scope={"branches": ["OTHER-BRANCH"]}),
            _chunk("OK"),
        ],
        source_hash="s4", dataset_version="v1",
    )
    hits, diagnostics = index.search_with_diagnostics("vốn lưu động", branch="HN01", threshold=0.01)
    assert len(hits) == 1
    assert diagnostics.filtered_reasons[MetadataFilterReason.SOURCE_NOT_EFFECTIVE.value] == 2
    assert diagnostics.filtered_reasons[MetadataFilterReason.SOURCE_SCOPE_MISMATCH.value] == 1
    assert sum(diagnostics.filtered_reasons.values()) == diagnostics.filtered_count
