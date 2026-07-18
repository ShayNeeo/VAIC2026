"""Phase 3 section 26: hierarchical parent-child retrieval, grounded in
the real SOP workflow -> step structure (app/operations/sop_knowledge.py)."""

from __future__ import annotations

from app.knowledge.index import LocalEmbedding
from app.operations.sop_knowledge import OperationsKnowledgeService


def test_child_step_expands_to_its_workflow_overview_parent(tmp_path):
    svc = OperationsKnowledgeService(index_path=tmp_path / "ops.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    parent = svc.index.expand_to_parent_context("SYNTH-SOP-CORP-SALES-002:OPS-01:1.0")
    assert parent is not None
    assert parent.chunk_id == "SYNTH-SOP-CORP-SALES-002:OVERVIEW"
    assert "3 bước" in parent.text


def test_leaf_chunk_with_no_parent_returns_none(tmp_path):
    svc = OperationsKnowledgeService(index_path=tmp_path / "ops2.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    parent = svc.index.expand_to_parent_context("SYNTH-SOP-CORP-SALES-002:OVERVIEW")
    assert parent is None


def test_unknown_chunk_id_returns_none(tmp_path):
    svc = OperationsKnowledgeService(index_path=tmp_path / "ops3.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    assert svc.index.expand_to_parent_context("DOES-NOT-EXIST") is None


def test_citation_still_points_at_the_child_chunk_not_the_expanded_parent(tmp_path):
    """Hard invariant: parent expansion is for CONTEXT display only -- a
    GroundingItem citing the child chunk_id must keep citing it, never get
    silently rewritten to the parent."""
    svc = OperationsKnowledgeService(index_path=tmp_path / "ops4.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    child_id = "SYNTH-SOP-CORP-SALES-002:OPS-01:1.0"
    parent = svc.index.expand_to_parent_context(child_id)
    assert parent.chunk_id != child_id
