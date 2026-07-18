"""Safety acceptance tests for deterministic eligibility."""

from __future__ import annotations

from app.eligibility.engine import EligibilityEngine


VERIFIED_BUSINESS_REG = {"document_type": "business_registration", "status": "verified"}
VERIFIED_FS = {"document_type": "financial_statements", "status": "verified"}


def product(result, product_id):
    return next(item for item in result["products"] if item["product_id"] == product_id)


def test_missing_ubo_blocks_credit_only_while_payroll_can_pass():
    result = EligibilityEngine().evaluate(
        ["PROD-PAYROLL", "PROD-WORKING-CAPITAL"],
        customer={
            "employees_count": 500,
            "operating_years": 8,
            "has_bad_debt_12m": False,
        },
        documents=[VERIFIED_BUSINESS_REG, VERIFIED_FS],
    )
    assert product(result, "PROD-PAYROLL")["status"] == "passed"
    assert product(result, "PROD-WORKING-CAPITAL")["status"] == "pending_information"
    assert "ubo_status" in product(result, "PROD-WORKING-CAPITAL")["missing_information"]


def test_explicit_disqualifying_value_fails_with_versioned_evidence():
    result = EligibilityEngine().evaluate(
        ["PROD-PAYROLL"],
        customer={"employees_count": 5},
        documents=[VERIFIED_BUSINESS_REG],
    )
    payroll = product(result, "PROD-PAYROLL")
    failed = next(item for item in payroll["rules"] if item["status"] == "failed")
    assert payroll["status"] == "failed"
    assert failed["rule_id"] == "RULE-PAYROLL-EMPLOYEE-001"
    assert failed["source_document_id"] and failed["source_version"] and failed["source_quote"]


def test_missing_financial_statement_is_pending_information_not_passed():
    result = EligibilityEngine().evaluate(
        ["PROD-WORKING-CAPITAL"],
        customer={"operating_years": 8, "ubo_status": "verified", "has_bad_debt_12m": False},
        documents=[VERIFIED_BUSINESS_REG],
    )
    assert product(result, "PROD-WORKING-CAPITAL")["status"] == "pending_information"
    assert "documents" in product(result, "PROD-WORKING-CAPITAL")["missing_information"]


def test_live_credit_timeout_can_never_return_passed():
    result = EligibilityEngine().evaluate(
        ["PROD-WORKING-CAPITAL"],
        customer={"operating_years": 8, "ubo_status": "verified", "has_bad_debt_12m": False},
        documents=[VERIFIED_BUSINESS_REG, VERIFIED_FS],
        live_check_error="timeout",
    )
    assert product(result, "PROD-WORKING-CAPITAL")["status"] == "pending_review"


def test_warning_does_not_block_bulk_payment():
    result = EligibilityEngine().evaluate(
        ["PROD-BULK-PAYMENT"],
        customer={"technical_contact_available": False},
        documents=[VERIFIED_BUSINESS_REG],
    )
    assert product(result, "PROD-BULK-PAYMENT")["status"] == "passed"
    assert any(item["severity"] == "warning" and item["status"] == "failed" for item in product(result, "PROD-BULK-PAYMENT")["rules"])


def test_verified_ubo_document_resolves_missing_customer_field():
    result = EligibilityEngine().evaluate(
        ["PROD-WORKING-CAPITAL"],
        customer={"operating_years": 8, "has_bad_debt_12m": False},
        documents=[
            VERIFIED_BUSINESS_REG,
            VERIFIED_FS,
            {"document_type": "ubo_information", "status": "verified"},
        ],
    )
    assert product(result, "PROD-WORKING-CAPITAL")["status"] == "passed"
