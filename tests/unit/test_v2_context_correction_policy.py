"""Regression tests for the CONTEXT_CORRECTION_POLICIES registry
(app/workflow/impact.py) that replaced two independently-maintained field
lists -- app/api/v2/router.py::correct_context's own `allowed_fields` set,
and app/workflow/impact.py::impacted_nodes' field-specific branches.

See docs/SPECIALIST_REVIEW_FOCUSED_AUDIT.md section 2.1: the two lists had
drifted (router.py declared 8 fields correctable, impact.py only handled 4
of them correctly, silently sending the other 4 into a full re-run that
V2WorkflowEngine.resume() rejects). This file pins down the invariant that
must never regress: router.py's allowed fields and the registry's fields
are the exact same set, by construction, not by two people remembering to
keep two lists in sync.
"""

from __future__ import annotations

import inspect

import pytest

from app.workflow.impact import (
    CONTEXT_CORRECTION_POLICIES,
    DOWNSTREAM_ELIGIBILITY,
    DOWNSTREAM_PRODUCT_MATCH,
    FULL,
    impacted_nodes,
)


def _find_endpoint_by_name(router, *, function_name: str):
    for route in router.routes:
        if getattr(route, "endpoint", None) is not None and route.endpoint.__name__ == function_name:
            return route.endpoint
    raise AssertionError(f"no route registered with endpoint function {function_name!r}")


def test_router_correct_context_derives_allowed_fields_from_the_registry():
    """app/api/v2/router.py must not keep its own separate field list --
    inspect the real registered endpoint function's source (correct_context
    is a closure inside create_router(), not a module-level name, so it has
    to be located via the built router's routes) so this test fails loudly
    if someone reintroduces a hardcoded set instead of importing the
    registry."""
    from app.api.v2.router import create_router

    endpoint = _find_endpoint_by_name(create_router(), function_name="correct_context")
    source = inspect.getsource(endpoint)
    assert "CONTEXT_CORRECTION_POLICIES" in source
    assert "employees_count" not in source, (
        "correct_context() appears to hardcode field names again instead of "
        "reading them from CONTEXT_CORRECTION_POLICIES -- see "
        "docs/SPECIALIST_REVIEW_FOCUSED_AUDIT.md section 2.1"
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "employees_count",
        "annual_revenue",
        "cash_flow_status",
        "account_or_unit_count",
        "operating_years",
        "has_bad_debt_12m",
        "ubo_status",
        "name",
    ],
)
def test_every_router_declared_field_has_a_registry_policy(field_name):
    assert field_name in CONTEXT_CORRECTION_POLICIES


def test_registry_has_no_undeclared_extra_fields():
    """Guards the other direction: a field added to the registry without
    also being reachable from correct_context's allowed_fields would be
    dead policy, silently never used."""
    assert set(CONTEXT_CORRECTION_POLICIES.keys()) == {
        "employees_count", "annual_revenue", "cash_flow_status", "account_or_unit_count",
        "operating_years", "has_bad_debt_12m", "ubo_status", "name",
    }


@pytest.mark.parametrize(
    "field_name",
    ["employees_count", "annual_revenue", "cash_flow_status", "account_or_unit_count"],
)
def test_product_affecting_fields_resume_from_product_matching(field_name):
    nodes = impacted_nodes([f"customer.attributes.{field_name}"])
    assert nodes == DOWNSTREAM_PRODUCT_MATCH
    assert nodes[0] == "retrieve_products"


@pytest.mark.parametrize(
    "field_name",
    ["operating_years", "has_bad_debt_12m", "ubo_status", "name"],
)
def test_eligibility_only_fields_resume_from_eligibility_not_full_rerun(field_name):
    nodes = impacted_nodes([f"customer.attributes.{field_name}"])
    assert nodes == DOWNSTREAM_ELIGIBILITY
    assert nodes[0] == "evaluate_eligibility"
    assert "collect_context" not in nodes


def test_unprefixed_customer_field_still_falls_back_to_full_rerun():
    """Preserves pre-existing behavior for change tokens that are NOT a
    customer.attributes.* field correction (e.g. customer_id changing
    identity, not an attribute) -- must stay a full re-run, unaffected by
    the registry lookup added for the specific-field case."""
    assert impacted_nodes(["customer_id"]) == FULL
    assert impacted_nodes(["customer_id"])[0] == "collect_context"


def test_document_change_tokens_still_resume_from_eligibility():
    """Preserves pre-existing behavior for the /resume endpoint's
    document-driven change tokens (not customer.attributes.* fields at
    all) -- these never went through the buggy branch and must not change."""
    assert impacted_nodes(["document:financial_statements"]) == DOWNSTREAM_ELIGIBILITY
