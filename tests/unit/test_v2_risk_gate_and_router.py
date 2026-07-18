"""Unit tests for the components added to match the SHB Multi-Agent Workflow
diagram: ComplexityRouter (app/workflow/router.py) and RiskGuardrailGate
(app/workflow/risk_gate.py). Isolated from V2WorkflowEngine so failures here
point directly at routing/risk-classification logic, not retrieval/eligibility."""

from __future__ import annotations

from copy import deepcopy

from app.intent.fallback import DeterministicIntentExtractor
from app.schemas.v2.examples import FULL_CONTEXT_SNAPSHOT, MINIMAL_SHARED_CASE_STATE
from app.schemas.v2.shared_case_state import Evidence, SharedCaseState
from app.workflow.risk_gate import RiskGuardrailGate
from app.workflow.router import ComplexityRouter


def _state_with_intent(message: str) -> SharedCaseState:
    payload = deepcopy(MINIMAL_SHARED_CASE_STATE)
    payload["context"] = deepcopy(FULL_CONTEXT_SNAPSHOT)
    payload["request"]["text"] = message
    payload["request"]["message_id"] = "MSG-ROUTER-TEST"
    state = SharedCaseState.model_validate(payload)
    state.intent_result = DeterministicIntentExtractor().extract(message, "MSG-ROUTER-TEST")
    return state


def test_new_business_request_routes_complex_even_without_credit_keywords():
    """find_product is the intent for a brand-new case (e.g. payroll onboarding);
    it always leads to a drafted external action once approved, so it must
    never take the simple/single-agent-RAG shortcut straight to COMPLETED."""
    state = _state_with_intent("Doanh nghiệp muốn chi lương cho 500 nhân viên")
    assert state.intent_result.primary_intent == "find_product"
    assert ComplexityRouter.is_complex(state) is True


def test_status_lookup_on_existing_case_routes_simple():
    state = _state_with_intent("Case của tôi đang ở trạng thái nào")
    assert state.intent_result.primary_intent == "status_lookup"
    assert ComplexityRouter.is_complex(state) is False


def test_credit_keyword_always_routes_complex():
    state = _state_with_intent("So sánh hạn mức vay vốn lưu động")
    assert ComplexityRouter.is_complex(state) is True


def test_missing_intent_fails_closed_to_complex():
    payload = deepcopy(MINIMAL_SHARED_CASE_STATE)
    payload["context"] = deepcopy(FULL_CONTEXT_SNAPSHOT)
    state = SharedCaseState.model_validate(payload)
    assert state.intent_result is None
    assert ComplexityRouter.is_complex(state) is True


def _evidence(*, is_valid: bool = True, claim_id: str = "EV-1") -> Evidence:
    return Evidence(
        claim_id=claim_id,
        module="Product",
        claim="claim",
        source_document_id="DOC-1",
        source_version="1",
        location="section",
        quote="quote",
        is_valid=is_valid,
    )


def test_passed_eligibility_approves_with_no_risk():
    decision = RiskGuardrailGate.evaluate(eligibility_result={"overall_status": "passed"}, evidences=[_evidence()])
    assert decision.outcome == "approve"
    assert decision.risk_level == "none"


def test_pending_information_needs_information_with_no_risk():
    decision = RiskGuardrailGate.evaluate(
        eligibility_result={"overall_status": "pending_information"}, evidences=[_evidence()]
    )
    assert decision.outcome == "need_information"
    assert decision.risk_level == "none"


def test_hard_block_failed_eligibility_is_high_risk_review():
    eligibility_result = {
        "overall_status": "failed",
        "products": [
            {
                "product_id": "PRD-WC-001",
                "rules": [
                    {"rule_id": "RULE-CREDIT-BAD-DEBT-001", "severity": "blocking", "status": "failed"},
                    {"rule_id": "RULE-CREDIT-OPERATING-YEARS-001", "severity": "blocking", "status": "passed"},
                ],
            }
        ],
    }
    decision = RiskGuardrailGate.evaluate(eligibility_result=eligibility_result, evidences=[_evidence()])
    assert decision.outcome == "need_review"
    assert decision.risk_level == "high"
    assert decision.triggered_rules == ["RULE-CREDIT-BAD-DEBT-001"]


def test_policy_conflict_pending_review_is_high_risk():
    decision = RiskGuardrailGate.evaluate(
        eligibility_result={"overall_status": "pending_review", "products": []}, evidences=[_evidence()]
    )
    assert decision.outcome == "need_review"
    assert decision.risk_level == "high"


def test_invalid_evidence_overrides_a_passed_eligibility_as_high_risk():
    """An unsupported/fabricated claim must block approval even if the
    deterministic eligibility engine itself says passed -- evidence integrity
    is checked first, matching Evidence Validator -> Risk Gate ordering."""
    decision = RiskGuardrailGate.evaluate(
        eligibility_result={"overall_status": "passed"},
        evidences=[_evidence(is_valid=False, claim_id="EV-BAD")],
    )
    assert decision.outcome == "need_review"
    assert decision.risk_level == "high"
    assert decision.triggered_rules == ["EV-BAD"]


def test_unrecognized_eligibility_status_fails_closed_to_high_risk():
    decision = RiskGuardrailGate.evaluate(eligibility_result={"overall_status": "something_new"}, evidences=[])
    assert decision.outcome == "need_review"
    assert decision.risk_level == "high"
