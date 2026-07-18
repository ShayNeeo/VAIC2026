"""Product-scoped synthetic B2B policy and legal-output acceptance tests."""

from __future__ import annotations

import json
from datetime import date

import pytest

from app.eligibility.engine import EligibilityEngine
from app.eligibility.policy_registry import B2BPolicyRegistry, DEFAULT_POLICIES, PolicyRegistryError


BUSINESS_REG = {"document_type": "business_registration", "status": "verified"}


def _product(result, product_id):
    return next(item for item in result["products"] if item["product_id"] == product_id)


def test_all_active_products_receive_general_and_product_specific_policies():
    result = EligibilityEngine().evaluate(
        ["PROD-PAYROLL", "PROD-CASH-MGMT", "PROD-BULK-PAYMENT", "PROD-WORKING-CAPITAL"],
        customer={"employees_count": 20, "annual_revenue": 60_000_000_000, "account_or_unit_count": 3, "technical_contact_available": True, "operating_years": 4, "ubo_status": "verified", "has_bad_debt_12m": False},
        documents=[BUSINESS_REG, {"document_type": "financial_statements", "status": "verified"}],
    )
    expected = {
        "PROD-PAYROLL": "SYN-B2B-PAYROLL-001",
        "PROD-CASH-MGMT": "SYN-B2B-CASH-001",
        "PROD-BULK-PAYMENT": "SYN-B2B-BULK-001",
        "PROD-WORKING-CAPITAL": "SYN-B2B-CREDIT-001",
    }
    for product_id, policy_id in expected.items():
        policies = _product(result, product_id)["related_policies"]
        ids = {item["policy_id"] for item in policies}
        assert "SYN-B2B-KYC-001" in ids
        assert policy_id in ids
        assert len({(item["policy_id"], item["document_version"], item["section"]) for item in policies}) == len(policies)


def test_payroll_never_receives_credit_or_ubo_policy_sections():
    payroll = _product(EligibilityEngine().evaluate(["PROD-PAYROLL"], customer={"employees_count": 20}, documents=[BUSINESS_REG]), "PROD-PAYROLL")
    assert "SYN-B2B-CREDIT-001" not in {item["policy_id"] for item in payroll["related_policies"]}
    assert "KYC-8" not in {item["section"] for item in payroll["related_policies"]}


def test_missing_document_returns_required_action_and_policy_reference():
    credit = _product(EligibilityEngine().evaluate(["PROD-WORKING-CAPITAL"], customer={"operating_years": 4, "ubo_status": "verified", "has_bad_debt_12m": False}, documents=[BUSINESS_REG]), "PROD-WORKING-CAPITAL")
    assert credit["status"] == "pending_information"
    assert "documents" in credit["legal_summary"]["required_actions"]
    policy = next(item for item in credit["related_policies"] if "RULE-CREDIT-FS-001" in item["rule_ids"])
    assert policy["decision_effect"] == "required_information"
    assert policy["source_quote"]


def test_inactive_and_wrong_product_policies_are_filtered(tmp_path):
    source = json.loads(DEFAULT_POLICIES.read_text(encoding="utf-8"))
    source["policies"].append({**source["policies"][1], "policy_id": "EXPIRED", "effective_to": "2025-01-01", "active": True})
    path = tmp_path / "policies.json"
    path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
    registry = B2BPolicyRegistry(path)
    assert "EXPIRED" not in {item["policy_id"] for item in registry.active_for_product("PROD-PAYROLL", as_of=date(2026, 7, 18))}
    assert "SYN-B2B-CREDIT-001" not in {item["policy_id"] for item in registry.active_for_product("PROD-PAYROLL")}
    assert "SYN-B2B-CREDIT-001" not in {item["policy_id"] for item in registry.active_for_product("PROD-WORKING-CAPITAL", branch="DN01")}


def test_policy_pack_without_synthetic_label_is_rejected(tmp_path):
    path = tmp_path / "policies.json"
    path.write_text('{"dataset_version":"x","synthetic":false,"policies":[]}', encoding="utf-8")
    with pytest.raises(PolicyRegistryError):
        B2BPolicyRegistry(path)


def test_no_product_recommendation_does_not_invent_default_products():
    result = EligibilityEngine().evaluate([], customer={}, documents=[])
    assert result["products"] == []
