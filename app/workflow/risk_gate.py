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
    # Which specialist RoleType value(s) (app.schemas.v2.employee.RoleType) are
    # the correct human resolver(s) for a need_review outcome. Empty for
    # approve/need_information -- only meaningful when a human must act.
    # Populated from the SAME evidence/eligibility data this gate already
    # inspects, not a separate guess -- see _required_reviewer_roles().
    required_reviewer_roles: List[str] = field(default_factory=list)
    # Whether a named specialist may clear this SPECIFIC need_review
    # decision at all, vs. it being an absolute/factual block no human
    # override should bypass (missing mandatory document, a hard numeric
    # eligibility threshold, bad-debt history, an unresolved evidence
    # citation failure, a code path this gate does not recognize). Always
    # False for approve/need_information (not applicable). For need_review,
    # derived from real policy data -- app.eligibility.models.EligibilityRule
    # .human_review_allowed -- never a blanket "any specialist can clear
    # anything" default. See app/api/v2/employee_router.py's
    # specialist-reviews endpoint, which refuses decision="cleared" whenever
    # this is False (BLOCK_NOT_OVERRIDABLE).
    human_review_allowed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome,
            "risk_level": self.risk_level,
            "reasons": self.reasons,
            "triggered_rules": self.triggered_rules,
            "required_reviewer_roles": self.required_reviewer_roles,
            "human_review_allowed": self.human_review_allowed,
        }


class RiskGuardrailGate:
    """Runs after Evidence Validator, before the RM-facing branch."""

    @staticmethod
    def evaluate(*, eligibility_result: Dict[str, Any], evidences: List[Evidence]) -> RiskGateDecision:
        invalid_evidence = [item for item in evidences if not item.is_valid]
        if invalid_evidence:
            # Evidence.human_review_allowed (set in
            # V2WorkflowEngine._product_evidence/_legal_evidence from the
            # real app.safety.evidence_validator.ValidationStatus) is True
            # only for a pure citation/grounding mismatch -- the source
            # document itself is current and exists, only the exact quote
            # was not found in it, which a specialist can independently
            # re-verify. Overridable only if EVERY invalid claim is that
            # kind -- a single expired-source/conflicting-evidence/
            # source-not-found claim in the mix vetoes the whole decision,
            # same principle as the eligibility-rule case below.
            return RiskGateDecision(
                outcome="need_review",
                risk_level="high",
                reasons=["unsupported_evidence_claim"],
                triggered_rules=[item.claim_id for item in invalid_evidence],
                required_reviewer_roles=_required_reviewer_roles(invalid_evidence=invalid_evidence),
                human_review_allowed=all(item.human_review_allowed for item in invalid_evidence),
            )

        overall = str(eligibility_result.get("overall_status") or "")
        if overall == "passed":
            return RiskGateDecision(outcome="approve", risk_level="none", reasons=[])
        if overall == "pending_information":
            return RiskGateDecision(outcome="need_information", risk_level="none", reasons=["missing_required_information"])
        if overall == "failed":
            triggered = _blocking_rule_evaluations(eligibility_result, statuses={"failed"})
            return RiskGateDecision(
                outcome="need_review",
                risk_level="high",
                reasons=["eligibility_hard_block"],
                triggered_rules=[item["rule_id"] for item in triggered],
                required_reviewer_roles=["legal_specialist"],
                # Overridable only if EVERY triggered rule was explicitly
                # policy-flagged reviewable -- one absolute rule in the mix
                # is enough to block any override of the whole decision.
                human_review_allowed=bool(triggered) and all(item.get("human_review_allowed") for item in triggered),
            )
        if overall == "pending_review":
            # A live check being unavailable, or a rule the deterministic
            # engine could not mechanically resolve, is inherently a
            # judgment-call case by construction -- always reviewable.
            return RiskGateDecision(
                outcome="need_review",
                risk_level="high",
                reasons=["eligibility_policy_conflict_or_live_check_unavailable"],
                triggered_rules=[item["rule_id"] for item in _blocking_rule_evaluations(eligibility_result, statuses={"pending_review"})],
                required_reviewer_roles=["legal_specialist"],
                human_review_allowed=True,
            )
        # Fail-closed default: an eligibility_status this gate does not
        # recognize must never be treated as safe to auto-approve, and must
        # never be human-overridable either -- nobody can meaningfully
        # review a code path the system itself does not understand.
        return RiskGateDecision(
            outcome="need_review",
            risk_level="high",
            reasons=["unrecognized_eligibility_status"],
            required_reviewer_roles=["legal_specialist"],
            human_review_allowed=False,
        )


def _blocking_rule_evaluations(eligibility_result: Dict[str, Any], *, statuses: set[str]) -> List[Dict[str, Any]]:
    """Full rule-evaluation dicts (not just IDs) for every blocking rule in
    the given status set -- needed so callers can also read
    human_review_allowed, not just rule_id."""
    triggered: List[Dict[str, Any]] = []
    for product in eligibility_result.get("products", []):
        for rule in product.get("rules", []):
            if rule.get("severity") == "blocking" and rule.get("status") in statuses:
                triggered.append(rule)
    return triggered


def _required_reviewer_roles(*, invalid_evidence: List[Evidence]) -> List[str]:
    """Evidence.module already distinguishes Product-sourced claims from
    Eligibility(legal/compliance)-sourced claims (see
    V2WorkflowEngine._product_evidence/_legal_evidence) -- reuse that
    real distinction instead of guessing which specialist should review."""
    roles: set[str] = set()
    for item in invalid_evidence:
        if item.module == "Product":
            roles.add("product_specialist")
        else:
            roles.add("legal_specialist")
    return sorted(roles) if roles else ["legal_specialist"]
