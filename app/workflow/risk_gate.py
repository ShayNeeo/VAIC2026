"""Risk & Guardrail Gate: the single place that turns Evidence Validator +
Eligibility Engine output into one of three outcomes (approve / need more
information / needs human review), with an explicit risk_level.

This does not invent a new risk policy: it wires through the taxonomy already
defined in plan_v2/08_ELIGIBILITY_LEGAL.md section 5 ("passed / failed /
pending_information / pending_review") and app/eligibility/engine.py's
existing _aggregate() priority order, which V2WorkflowEngine previously
collapsed into a single generic "else -> pending_review" branch without
distinguishing a hard block (failed) or policy conflict (pending_review) --
both genuine risk -- from a missing-document case (pending_information),
and without ever flagging evidence-validation failure as a risk in its own
right. LLM never decides this outcome (fail-closed, deterministic only).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

from app.schemas.v2.shared_case_state import Evidence

GateOutcome = Literal["approve", "need_information", "need_review"]
RiskLevel = Literal["none", "high"]


@dataclass(frozen=True)
class RiskGateDecision:
    outcome: GateOutcome
    risk_level: RiskLevel
    reasons: List[str]
    triggered_rules: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome,
            "risk_level": self.risk_level,
            "reasons": self.reasons,
            "triggered_rules": self.triggered_rules,
        }


class RiskGuardrailGate:
    """Runs after Evidence Validator, before the RM-facing branch."""

    @staticmethod
    def evaluate(*, eligibility_result: Dict[str, Any], evidences: List[Evidence]) -> RiskGateDecision:
        invalid_evidence = [item for item in evidences if not item.is_valid]
        if invalid_evidence:
            return RiskGateDecision(
                outcome="need_review",
                risk_level="high",
                reasons=["unsupported_evidence_claim"],
                triggered_rules=[item.claim_id for item in invalid_evidence],
            )

        overall = str(eligibility_result.get("overall_status") or "")
        if overall == "passed":
            return RiskGateDecision(outcome="approve", risk_level="none", reasons=[])
        if overall == "pending_information":
            return RiskGateDecision(outcome="need_information", risk_level="none", reasons=["missing_required_information"])
        if overall == "failed":
            return RiskGateDecision(
                outcome="need_review",
                risk_level="high",
                reasons=["eligibility_hard_block"],
                triggered_rules=_blocking_rule_ids(eligibility_result, statuses={"failed"}),
            )
        if overall == "pending_review":
            return RiskGateDecision(
                outcome="need_review",
                risk_level="high",
                reasons=["eligibility_policy_conflict_or_live_check_unavailable"],
                triggered_rules=_blocking_rule_ids(eligibility_result, statuses={"pending_review"}),
            )
        # Fail-closed default: an eligibility_status this gate does not
        # recognize must never be treated as safe to auto-approve.
        return RiskGateDecision(outcome="need_review", risk_level="high", reasons=["unrecognized_eligibility_status"])


def _blocking_rule_ids(eligibility_result: Dict[str, Any], *, statuses: set[str]) -> List[str]:
    rule_ids: List[str] = []
    for product in eligibility_result.get("products", []):
        for rule in product.get("rules", []):
            if rule.get("severity") == "blocking" and rule.get("status") in statuses:
                rule_ids.append(rule.get("rule_id"))
    return rule_ids
