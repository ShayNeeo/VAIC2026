"""Map changed artifacts to earliest safe resume nodes."""

from __future__ import annotations

from typing import Iterable, List


FULL = ["collect_context", "extract_intent", "resolve_slots", "retrieve_products", "evaluate_eligibility", "validate_evidence", "prepare_operations"]
DOWNSTREAM_ELIGIBILITY = ["evaluate_eligibility", "validate_evidence", "prepare_operations"]


def impacted_nodes(changes: Iterable[str]) -> List[str]:
    normalized = {str(item).lower() for item in changes}
    if any(
        token in item
        for item in normalized
        for token in (
            "customer.attributes.employees_count",
            "customer.attributes.annual_revenue",
            "customer.attributes.cash_flow_status",
            "customer.attributes.account_or_unit_count",
        )
    ):
        return FULL[3:]
    if any("customer" in item for item in normalized):
        return FULL
    if any("request" in item or "goal" in item for item in normalized):
        return FULL[1:]
    if any("product_catalog" in item or "product_version" in item for item in normalized):
        return FULL[3:]
    if any(token in item for item in normalized for token in ("ubo", "financial", "bctc", "business_registration", "document")):
        return DOWNSTREAM_ELIGIBILITY
    if any("email" in item or "draft" in item for item in normalized):
        return ["prepare_operations"]
    return DOWNSTREAM_ELIGIBILITY
