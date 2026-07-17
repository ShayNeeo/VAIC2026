"""Conflict detection between context sources.

plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md section 5: high-impact fields
(customer, case, recipient, product tied to an external action) must be
surfaced and require confirmation before any write; other fields can
disagree without blocking the user.
"""

from __future__ import annotations

from typing import List

from app.schemas.v2.common import DecisionImpact, ResolvedValue
from app.schemas.v2.context_snapshot import Conflict

HIGH_IMPACT_FIELDS = {"customer_id", "case_id", "recipient", "product_id"}


def decision_impact_for(field: str) -> DecisionImpact:
    return DecisionImpact.HIGH if field in HIGH_IMPACT_FIELDS else DecisionImpact.LOW


def build_conflict(field: str, candidates: List[ResolvedValue]) -> Conflict | None:
    """None if all candidates agree (or fewer than 2 candidates were given)."""
    if len(candidates) < 2:
        return None
    distinct_values = {_hashable(candidate.value) for candidate in candidates}
    if len(distinct_values) <= 1:
        return None
    impact = decision_impact_for(field)
    return Conflict(
        field=field,
        candidate_values=candidates,
        decision_impact=impact,
        requires_confirmation=impact == DecisionImpact.HIGH,
    )


def _hashable(value: object) -> object:
    if isinstance(value, (list, dict)):
        return repr(value)
    return value
