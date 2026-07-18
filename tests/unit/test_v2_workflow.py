"""Workflow state, routing and partial resume tests."""

from __future__ import annotations

import asyncio
from copy import deepcopy

import pytest

from app.schemas.v2.context_snapshot import ContextSnapshot
from app.schemas.v2.examples import FULL_CONTEXT_SNAPSHOT, MINIMAL_SHARED_CASE_STATE
from app.schemas.v2.shared_case_state import CaseStatus, SharedCaseState
from app.workflow.engine import V2WorkflowEngine
from app.workflow.impact import impacted_nodes
from app.workflow.state_machine import InvalidTransitionError, transition


def workflow_state(message: str, *, with_financials: bool = False) -> SharedCaseState:
    payload = deepcopy(MINIMAL_SHARED_CASE_STATE)
    context = deepcopy(FULL_CONTEXT_SNAPSHOT)
    context["conflicts"] = []
    context["customer"]["attributes"].update(
        {"operating_years": 8, "has_bad_debt_12m": False, "ubo_status": "verified", "account_or_unit_count": 4}
    )
    if with_financials:
        context["documents"].append(
            {"document_id": "DOC-FS", "document_type": "financial_statements", "version": "1", "status": "verified", "access_scope": {"branch": "HN01"}}
        )
    payload["context"] = ContextSnapshot.model_validate(context).model_dump(mode="json")
    payload["request"]["text"] = message
    payload["request"]["message_id"] = "MSG-WF"
    return SharedCaseState.model_validate(payload)


def test_invalid_transition_is_rejected():
    with pytest.raises(InvalidTransitionError):
        transition(CaseStatus.NEW, CaseStatus.COMPLETED)


def test_workflow_reaches_pending_approval_when_all_credit_inputs_exist(tmp_path):
    engine = V2WorkflowEngine(index_path=str(tmp_path / "index.sqlite3"))
    state = asyncio.run(engine.run(workflow_state("Tìm vốn lưu động", with_financials=True)))
    assert state.status == CaseStatus.PENDING_APPROVAL
    assert state.product_result["recommendations"][0]["product_id"] == "PROD-WORKING-CAPITAL"
    assert state.eligibility_result["overall_status"] == "passed"
    assert state.operations_result["external_side_effects"] == []
    assert all(item.is_valid and item.source_version for item in state.evidences)


def test_missing_financials_stops_at_pending_information(tmp_path):
    engine = V2WorkflowEngine(index_path=str(tmp_path / "index.sqlite3"))
    state = asyncio.run(engine.run(workflow_state("Tìm vốn lưu động")))
    assert state.status == CaseStatus.PENDING_INFORMATION
    assert "financial_statements" in state.operations_result["missing_information"]
    assert state.risk_gate_result["outcome"] == "need_information"
    assert state.risk_gate_result["risk_level"] == "none"


def test_bad_debt_hard_block_is_pending_review_with_high_risk(tmp_path):
    """RiskGuardrailGate must distinguish this (a genuine credit-policy hard
    block) from the missing-financials case above: both currently land on
    CaseStatus.PENDING_REVIEW/PENDING_INFORMATION, but only this one is
    risk_level=high, matching the diagram's separate "Rui ro cao" branch."""
    engine = V2WorkflowEngine(index_path=str(tmp_path / "index.sqlite3"))
    state = workflow_state("Tìm vốn lưu động", with_financials=True)
    state.context.customer.attributes["has_bad_debt_12m"] = True
    state = asyncio.run(engine.run(state))
    assert state.status == CaseStatus.PENDING_REVIEW
    assert state.risk_gate_result["outcome"] == "need_review"
    assert state.risk_gate_result["risk_level"] == "high"
    assert "RULE-CREDIT-BAD-DEBT-001" in state.risk_gate_result["triggered_rules"]


def test_ubo_or_financial_upload_resumes_only_eligibility_downstream(tmp_path):
    engine = V2WorkflowEngine(index_path=str(tmp_path / "index.sqlite3"))
    state = asyncio.run(engine.run(workflow_state("Tìm vốn lưu động")))
    product_before = deepcopy(state.product_result)
    state.context.documents.append(
        state.context.documents[0].model_copy(
            update={"document_id": "DOC-FS", "document_type": "financial_statements"}
        )
    )
    resumed = engine.resume(state, changes=["document:financial_statements"])
    assert resumed.workflow.resume_from_nodes == ["evaluate_eligibility", "validate_evidence", "prepare_operations"]
    assert resumed.product_result == product_before
    assert resumed.operations_result["artifact_version"] == 2


def test_impact_graph_for_customer_change_is_full():
    assert impacted_nodes(["customer_id"])[0] == "collect_context"


def test_new_message_invalidates_old_results_and_reanalyzes(tmp_path):
    engine = V2WorkflowEngine(index_path=str(tmp_path / "index.sqlite3"))
    state = asyncio.run(engine.run(workflow_state("Tìm vốn lưu động")))
    rerun = asyncio.run(
        engine.rerun_with_message(
            state,
            message="Tìm giải pháp quản lý dòng tiền",
            message_id="MSG-NEW",
        )
    )
    assert rerun.request.message_id == "MSG-NEW"
    assert rerun.product_result["recommendations"][0]["product_id"] == "PROD-CASH-MGMT"
    assert any(event["action"] == "new_message_received" for event in rerun.audit_events)
