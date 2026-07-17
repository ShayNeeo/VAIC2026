"""End-to-end controlled multi-agent workflow."""

from __future__ import annotations

import uuid
from typing import Dict

from app.agents import LegalAgent, OperationsAgent, ProductAgent
from app.schemas.state import SharedCaseState
from app.safety import EvidenceValidator, GuardrailGate
from app.services.planner_agent import PlannerAgent
from app.services.complexity_router import ComplexityRouter


class CaseOrchestrator:
    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.product = ProductAgent()
        self.legal = LegalAgent()
        self.operations = OperationsAgent()
        self.validator = EvidenceValidator()
        self.guardrails = GuardrailGate()
        self.router = ComplexityRouter()

    def run(self, state: SharedCaseState) -> SharedCaseState:
        state.trace_id = state.trace_id or str(uuid.uuid4())
        request_text = self._request_text(state)
        gate = self.guardrails.inspect_input(request_text, state.documents)
        if not gate["allowed"]:
            state.final_status = "failed"
            state.risk_level = "high"
            state.audit_log.append({"actor": "GuardrailGate", "action": "prompt_injection_blocked", "result": gate["security_flags"]})
            return state

        route = self.router.route(request_text)
        state.audit_log.append({"actor": "ComplexityRouter", "action": "route", "result": route})

        # A rerun rebuilds derived state while preserving case context and audit history.
        state.execution_plan = []
        state.product_result = {}
        state.legal_result = {}
        state.operations_result = {}
        state.missing_information = []
        state.evidences = []
        state.approval_status = "pending"
        if route == "simple":
            self.product.run(state)
            validation = self.validator.validate(state)
            state.final_status = "completed" if validation["all_valid"] else "failed"
            return state
        self.planner.create_plan(state)

        self.product.run(state)
        self._complete_task(state, "Product")
        self.legal.run(state)
        self._complete_task(state, "Legal")
        validation = self.validator.validate(state)
        self._complete_task(state, "Validator")

        if not validation["all_valid"]:
            state.final_status = "failed"
            state.risk_level = "high"
            return state

        blocking = any(item.get("severity", "").lower() == "blocking" for item in state.legal_result.get("failed_checks", []))
        if blocking:
            self.planner.adapt_plan(
                state,
                legal_severity="blocking",
                missing_information=state.legal_result.get("missing_documents", []),
            )
        self.operations.run(state)
        self._complete_task(state, "Operations")
        state.final_status = "pending_information" if blocking else "pending_approval"
        return state

    @staticmethod
    def _request_text(state: SharedCaseState) -> str:
        return str(state.customer_request.get("text", "")) if isinstance(state.customer_request, dict) else str(state.customer_request)

    @staticmethod
    def _complete_task(state: SharedCaseState, owner: str) -> None:
        for task in state.execution_plan:
            if task.owner == owner and task.status != "failed":
                task.status = "completed"
