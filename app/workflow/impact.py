"""Map changed artifacts to earliest safe resume nodes."""

from __future__ import annotations

from typing import Dict, Iterable, List


FULL = ["collect_context", "extract_intent", "resolve_slots", "retrieve_products", "evaluate_eligibility", "validate_evidence", "prepare_operations"]
DOWNSTREAM_ELIGIBILITY = ["evaluate_eligibility", "validate_evidence", "prepare_operations"]
DOWNSTREAM_PRODUCT_MATCH = FULL[3:]

CONTEXT_CORRECTION_POLICIES: Dict[str, List[str]] = {
    "employees_count": DOWNSTREAM_PRODUCT_MATCH,
    "annual_revenue": DOWNSTREAM_PRODUCT_MATCH,
    "cash_flow_status": DOWNSTREAM_PRODUCT_MATCH,
    "account_or_unit_count": DOWNSTREAM_PRODUCT_MATCH,
    "operating_years": DOWNSTREAM_ELIGIBILITY,
    "has_bad_debt_12m": DOWNSTREAM_ELIGIBILITY,
    "ubo_status": DOWNSTREAM_ELIGIBILITY,
    "name": DOWNSTREAM_ELIGIBILITY,
}


def impacted_nodes(changes: Iterable[str]) -> List[str]:
    normalized = {str(item).lower() for item in changes}
    for item in normalized:
        if item.startswith("customer.attributes."):
            field_name = item[len("customer.attributes."):]
            policy = CONTEXT_CORRECTION_POLICIES.get(field_name)
            if policy is not None:
                return policy
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
