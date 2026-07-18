"""Executor replay and sensitive-log tests."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest

from app.actions.executor import ActionExecutorV2, ExecutionDenied
from app.approval.service import ApprovalServiceV2
from app.observability.runtime import JsonEventLogger
from app.schemas.v2.examples import FULL_SHARED_CASE_STATE
from app.schemas.v2.shared_case_state import SharedCaseState
from app.storage.repository import V2Repository


def ready_state():
    payload = deepcopy(FULL_SHARED_CASE_STATE)
    payload["eligibility_result"] = {"overall_status": "passed"}
    payload["operations_result"] = {"crm_case_draft": {"case_id": "CASE-001", "subject": "Payroll"}}
    payload["evidences"][0]["is_valid"] = True
    return SharedCaseState.model_validate(payload)


def test_execution_requires_exact_approved_payload_and_replay_is_deduplicated(tmp_path):
    repository = V2Repository(tmp_path / "state.sqlite3")
    approval = ApprovalServiceV2(repository, secret="test-secret")
    executor = ActionExecutorV2(repository, approval)
    state = ready_state()
    payload = state.operations_result["crm_case_draft"]
    issued = approval.issue(
        case_id=state.case_id, approver_id="EMP-001", permissions=["create_crm_case"], payload=payload
    )
    first = executor.execute(
        state, approver_id="EMP-001", token=issued["token"], idempotency_key="ACTION-1", payload=payload
    )
    replay = executor.execute(
        state, approver_id="EMP-001", token="already-consumed", idempotency_key="ACTION-1", payload=payload
    )
    assert first["crm_case_id"] == replay["crm_case_id"]
    assert replay["idempotent_replay"] is True


def test_blocking_eligibility_prevents_execution(tmp_path):
    repository = V2Repository(tmp_path / "state.sqlite3")
    approval = ApprovalServiceV2(repository, secret="test-secret")
    state = ready_state()
    state.eligibility_result = {"overall_status": "failed"}
    with pytest.raises(ExecutionDenied):
        ActionExecutorV2(repository, approval).execute(
            state, approver_id="EMP-001", token="unused", idempotency_key="ACTION-2",
            payload=state.operations_result["crm_case_draft"],
        )


def test_structured_log_redacts_token(tmp_path):
    path = tmp_path / "events.jsonl"
    JsonEventLogger(path).emit("approval_test", case_id="CASE-1", approval_token="top-secret")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["approval_token"] == "[REDACTED]"
    assert "top-secret" not in path.read_text(encoding="utf-8")
