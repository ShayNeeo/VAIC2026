"""Exact-payload, evidence-gated and idempotent mock executor."""

from __future__ import annotations

import hashlib
from typing import Any, Dict

from app.approval.service import ApprovalServiceV2, payload_hash
from app.schemas.v2.shared_case_state import CaseStatus, SharedCaseState
from app.storage.repository import V2Repository


class ExecutionDenied(PermissionError):
    pass


class ActionExecutorV2:
    def __init__(self, repository: V2Repository, approval: ApprovalServiceV2) -> None:
        self.repository = repository
        self.approval = approval

    def execute(
        self,
        state: SharedCaseState,
        *,
        approver_id: str,
        token: str,
        idempotency_key: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        replay = self.repository.get_idempotent_result(idempotency_key)
        if replay is not None:
            return {**replay, "idempotent_replay": True}
        if state.status != CaseStatus.PENDING_APPROVAL:
            raise ExecutionDenied("case is not pending approval")
        if (state.eligibility_result or {}).get("overall_status") != "passed":
            raise ExecutionDenied("blocking or pending eligibility result")
        if not state.evidences or not all(item.is_valid for item in state.evidences):
            raise ExecutionDenied("evidence validation failed")
        expected = (state.operations_result or {}).get("action_payload") or (state.operations_result or {}).get("crm_case_draft")
        if payload != expected:
            raise ExecutionDenied("execution payload is not the latest frozen draft")
        self.approval.verify_and_consume(
            token,
            case_id=state.case_id,
            approver_id=approver_id,
            payload=payload,
            permission="create_crm_case",
        )
        suffix = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()[:10].upper()
        result = {
            "crm_case_id": f"SHB-CRM-{suffix}",
            "task_id": f"SHB-TASK-{suffix}",
            "opportunity_id": f"SHB-OPP-{suffix}",
            "task_ids": [f"SHB-TASK-{suffix}"],
            "draft_ids": [f"SHB-EMAIL-{suffix}", f"SHB-PROPOSAL-{suffix}"],
            "payload_hash": payload_hash(payload),
            "adapter": "enterprise_crm",
            "idempotent_replay": False,
        }
        return self.repository.save_idempotent_result(
            idempotency_key, "create_crm_case", payload_hash(payload), result
        )
