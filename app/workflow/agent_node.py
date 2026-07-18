"""Single-writer adapter from coordinator artifacts to SharedCaseState."""

from __future__ import annotations

from app.agents.coordinator import CoordinationResult
from app.schemas.v2.shared_case_state import SharedCaseState


def apply_coordination_result(state: SharedCaseState, result: CoordinationResult) -> SharedCaseState:
    state.product_result = result.product_result
    state.eligibility_result = result.eligibility_result
    state.credit_result = result.credit_result
    state.insurance_result = result.insurance_result
    state.collaboration_session = result.collaboration_session
    state.expert_findings = list(result.findings)
    state.agent_task_assignments = list(result.assignments)
    state.assistance_requests = list(result.assistance_requests)
    state.constraint_notices = list(result.constraint_notices)
    state.synthesis_result = result.synthesis_result
    return state

