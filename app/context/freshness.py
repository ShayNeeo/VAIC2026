"""TTL/staleness policy per context layer.

plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md section 2 ("Freshness phai
configurable theo data owner; khong hard-code trong service") and section 9
(failure/fallback behavior per layer). Policies are data, not constants
scattered across services, so a data owner can retune one place.

Workspace, workflow and conversation are "realtime"/"session" scoped: the
context services read them live from the session/case store on every call
(there is no cache to go stale), so they intentionally have no TTL policy
here. TTL staleness only applies to layers a service may cache: employee,
permission, customer, documents, preference.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class StaleBehavior(str, Enum):
    """Matches plan_v2/contracts/data_source_card.schema.json#/properties/freshness/stale_behavior
    so context freshness and data-source freshness use the same vocabulary."""

    ALLOW_WITH_WARNING = "ALLOW_WITH_WARNING"
    BLOCK_DECISION = "BLOCK_DECISION"
    FAIL_CLOSED = "FAIL_CLOSED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass(frozen=True)
class FreshnessPolicy:
    layer: str
    max_age_seconds: int
    stale_behavior: StaleBehavior

    def is_stale(self, observed_at: datetime, *, now: datetime | None = None) -> bool:
        reference = now or datetime.now(timezone.utc)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        age_seconds = (reference - observed_at).total_seconds()
        return age_seconds > self.max_age_seconds


DEFAULT_POLICIES: dict[str, FreshnessPolicy] = {
    "employee": FreshnessPolicy("employee", 24 * 3600, StaleBehavior.ALLOW_WITH_WARNING),
    "permission": FreshnessPolicy("permission", 5 * 60, StaleBehavior.FAIL_CLOSED),
    "customer": FreshnessPolicy("customer", 5 * 60, StaleBehavior.MANUAL_REVIEW),
    "documents": FreshnessPolicy("documents", 5 * 60, StaleBehavior.BLOCK_DECISION),
    "preference": FreshnessPolicy("preference", 30 * 24 * 3600, StaleBehavior.ALLOW_WITH_WARNING),
}


def get_policy(layer: str) -> FreshnessPolicy:
    try:
        return DEFAULT_POLICIES[layer]
    except KeyError as exc:
        raise KeyError(
            f"No freshness policy for layer {layer!r}; workspace/workflow/conversation "
            "are realtime/session-scoped and intentionally have none"
        ) from exc
