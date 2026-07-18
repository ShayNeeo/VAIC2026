"""Map changed artifacts to earliest safe resume nodes."""

from __future__ import annotations

from typing import Dict, Iterable, List


FULL = ["collect_context", "extract_intent", "resolve_slots", "retrieve_products", "evaluate_eligibility", "validate_evidence", "prepare_operations"]
DOWNSTREAM_ELIGIBILITY = ["evaluate_eligibility", "validate_evidence", "prepare_operations"]
DOWNSTREAM_PRODUCT_MATCH = FULL[3:]

CUSTOMER_ATTRIBUTE_PREFIX = "customer.attributes."

# Single source of truth for which customer.attributes.* fields the RM-facing
# PATCH /cases/{case_id}/context endpoint (app/api/v2/router.py::correct_context)
# may correct, and which workflow nodes must re-run for each one.
# app/api/v2/router.py derives its allowed_fields set from this dict's keys
# instead of keeping a second, independently-maintained list -- see
# docs/SPECIALIST_REVIEW_FOCUSED_AUDIT.md section 2.1 for the bug this
# replaces: 4 of the 8 fields router.py declared correctable
# (operating_years, has_bad_debt_12m, ubo_status, name) fell through to the
# generic "any field containing the substring 'customer'" branch below
# before reaching field-specific logic -- every customer.attributes.* field
# contains that substring, so they were always routed to a full re-run,
# which V2WorkflowEngine.resume() then unconditionally rejects.
CONTEXT_CORRECTION_POLICIES: Dict[str, List[str]] = {
    # These four affect which products the customer qualifies for at all
    # (segment sizing / cash-flow-based routing), so product matching has to
    # re-run, not just eligibility.
    "employees_count": DOWNSTREAM_PRODUCT_MATCH,
    "annual_revenue": DOWNSTREAM_PRODUCT_MATCH,
    "cash_flow_status": DOWNSTREAM_PRODUCT_MATCH,
    "account_or_unit_count": DOWNSTREAM_PRODUCT_MATCH,
    # These four only affect eligibility/evidence validation against the
    # already-matched product list -- product matching does not need to
    # re-run.
    "operating_years": DOWNSTREAM_ELIGIBILITY,
    "has_bad_debt_12m": DOWNSTREAM_ELIGIBILITY,
    "ubo_status": DOWNSTREAM_ELIGIBILITY,
    "name": DOWNSTREAM_ELIGIBILITY,
}


def impacted_nodes(changes: Iterable[str]) -> List[str]:
    normalized = {str(item).lower() for item in changes}
    for item in normalized:
        if item.startswith(CUSTOMER_ATTRIBUTE_PREFIX):
            field_name = item[len(CUSTOMER_ATTRIBUTE_PREFIX):]
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
