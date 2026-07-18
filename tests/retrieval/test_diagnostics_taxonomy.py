"""Phase 1 section 3: error taxonomy must distinguish "no relevant result"
from "provider failure" from "nothing allowed after security filtering" --
never collapse these to the same bare [].

Phase 0's index-level RetrievalOutcomeCode is re-verified here alongside
the Phase 1 pipeline-level RetrievalErrorCode to prove they stay
consistent (same underlying concept, two abstraction layers -- see
app/knowledge/retrieval_contracts.py module docstring)."""

from __future__ import annotations

from datetime import date

from app.knowledge.index import PersistentHybridIndex, RetrievalOutcomeCode
from app.knowledge.models import KnowledgeChunk
from app.knowledge.retrieval_contracts import RetrievalErrorCode


def test_index_not_ready_differs_from_no_relevant_result(tmp_path):
    empty = PersistentHybridIndex(tmp_path / "empty.sqlite3")
    _, empty_diag = empty.search_with_diagnostics("bất kỳ câu hỏi nào")
    assert empty_diag.outcome == RetrievalOutcomeCode.INDEX_NOT_READY

    populated = PersistentHybridIndex(tmp_path / "populated.sqlite3")
    populated.upsert(
        [
            KnowledgeChunk(
                chunk_id="C1", document_id="DOC-1", document_version="1",
                product_id="SYNTH-PROD-PAYROLL", section_path="1.1", text="chi lương nhân sự",
                effective_from=date(2026, 1, 1), effective_to=None, active=True,
                segments=[], access_scope={"branches": ["*"]}, content_hash="hash-1",
            )
        ],
        source_hash="s1", dataset_version="v1",
    )
    _, populated_diag = populated.search_with_diagnostics("chính sách ngoại hối xuất khẩu")
    assert populated_diag.outcome == RetrievalOutcomeCode.NO_RELEVANT_RESULT
    assert populated_diag.outcome != empty_diag.outcome


def test_empty_query_differs_from_both(tmp_path):
    index = PersistentHybridIndex(tmp_path / "eq.sqlite3")
    index.upsert(
        [
            KnowledgeChunk(
                chunk_id="C1", document_id="DOC-1", document_version="1",
                product_id="SYNTH-PROD-PAYROLL", section_path="1.1", text="chi lương",
                effective_from=date(2026, 1, 1), effective_to=None, active=True,
                segments=[], access_scope={"branches": ["*"]}, content_hash="hash-1",
            )
        ],
        source_hash="s1", dataset_version="v1",
    )
    _, diag = index.search_with_diagnostics("là và của")
    assert diag.outcome == RetrievalOutcomeCode.EMPTY_QUERY
    assert diag.outcome not in {RetrievalOutcomeCode.INDEX_NOT_READY, RetrievalOutcomeCode.NO_RELEVANT_RESULT}


def test_pipeline_level_error_taxonomy_is_a_strict_superset_of_phase_0_failure_codes():
    """RetrievalOutcomeCode.OK is a *success* marker, not a failure code --
    it deliberately has no counterpart in RetrievalErrorCode (an "error
    code" enum that includes OK would be a contradiction in terms; success
    is represented by RetrievalStatus.OK with error_code=None instead).
    The three genuine Phase 0 *failure* reasons must all still be present."""
    phase0_failure_values = {code.value for code in RetrievalOutcomeCode if code != RetrievalOutcomeCode.OK}
    phase1_values = {code.value for code in RetrievalErrorCode}
    assert phase0_failure_values.issubset(phase1_values)
    assert "ok" not in phase1_values
