"""Short-lived HMAC approval tokens and guarded mock action execution."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict

from app.config import settings
from app.schemas.state import SharedCaseState
from app.safety.guardrails import GuardrailGate
from app.services.mock_services import CRMService


class ApprovalTokenError(ValueError):
    pass


class ApprovalService:
    @staticmethod
    def issue(case_id: str, rm_id: str) -> str:
        payload = {"case_id": case_id, "rm_id": rm_id, "exp": int(time.time()) + settings.APPROVAL_TOKEN_TTL_SECONDS}
        body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
        signature = hmac.new(settings.APPROVAL_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        return f"{body}.{signature}"

    @staticmethod
    def verify(token: str, case_id: str, rm_id: str) -> Dict[str, Any]:
        try:
            body, signature = token.split(".", 1)
            expected = hmac.new(settings.APPROVAL_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise ApprovalTokenError("Chữ ký token không hợp lệ")
            padded = body + "=" * (-len(body) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        except ApprovalTokenError:
            raise
        except Exception as exc:
            raise ApprovalTokenError("Token không đúng định dạng") from exc
        if payload.get("case_id") != case_id or payload.get("rm_id") != rm_id:
            raise ApprovalTokenError("Token không thuộc case/RM này")
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ApprovalTokenError("Token đã hết hạn")
        return payload


class ActionExecutor:
    @staticmethod
    def execute(state: SharedCaseState) -> Dict[str, Any]:
        allowed, reason = GuardrailGate.can_execute(state)
        if not allowed:
            raise PermissionError(reason)
        proposed = state.operations_result.get("proposed_crm_case", {})
        case_result = CRMService.create_case(state.case_id, proposed)
        task_results = [CRMService.create_task(state.case_id, task) for task in proposed.get("tasks", [])]
        result = {"crm_case_id": case_result["crm_case_id"], "tasks": task_results}
        state.final_status = "completed"
        state.audit_log.append({"actor": "ActionExecutor", "action": "execute_approved_actions", "result": result})
        return result

