"""Customer context: CRM profile with RBAC scope check and stale-cache fallback.

plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md:
- section 3: unauthorized selected customer stops with CONTEXT_ACCESS_DENIED,
  never falls back to "closest" customer.
- section 9: "CRM timeout -> Use fresh cache; else mark stale and do not make
  eligibility decision." A cache hit is only returned as non-stale if it is
  itself still within the customer freshness policy; otherwise it is
  returned with stale=True so eligibility logic downstream must refuse to
  decide (enforced by whichever module reads Customer.stale, e.g. V2-008).
"""

from __future__ import annotations

from datetime import datetime
from threading import RLock
from typing import Dict, Optional, Tuple

from app.context.freshness import get_policy
from app.integrations.enterprise import CRMPort, CustomerProfile
from app.integrations.errors import ContextAccessDeniedError, UpstreamTimeoutError
from app.schemas.v2.context_snapshot import Customer, Employee


class CustomerContextService:
    def __init__(self, crm: CRMPort) -> None:
        self._crm = crm
        self._cache: Dict[str, Tuple[CustomerProfile, datetime]] = {}
        self._lock = RLock()

    def get(self, customer_id: Optional[str], *, employee: Employee, correlation_id: str) -> Customer:
        if customer_id is None:
            return Customer(customer_id=None, profile_version=None, attributes={}, source_observed_at=None, stale=True)

        managed_customer_ids = set(employee.access_scope.get("managed_customer_ids", []))
        if customer_id not in managed_customer_ids:
            raise ContextAccessDeniedError(correlation_id, employee_id=employee.employee_id, customer_id=customer_id)

        try:
            profile = self._crm.get_customer_profile(customer_id, correlation_id=correlation_id)
        except UpstreamTimeoutError:
            return self._from_cache_or_unknown(customer_id)

        observed_at = datetime.fromisoformat(profile["observed_at"])
        with self._lock:
            self._cache[customer_id] = (profile, observed_at)
        return Customer(
            customer_id=profile["customer_id"],
            profile_version=profile["profile_version"],
            attributes=profile["attributes"],
            source_observed_at=observed_at,
            stale=False,
        )

    def _from_cache_or_unknown(self, customer_id: str) -> Customer:
        with self._lock:
            cached = self._cache.get(customer_id)
        if cached is None:
            return Customer(customer_id=customer_id, profile_version=None, attributes={}, source_observed_at=None, stale=True)

        profile, observed_at = cached
        stale = get_policy("customer").is_stale(observed_at)
        return Customer(
            customer_id=profile["customer_id"],
            profile_version=profile["profile_version"],
            attributes=profile["attributes"],
            source_observed_at=observed_at,
            stale=stale,
        )
