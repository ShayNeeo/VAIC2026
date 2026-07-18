from app.insurance.service import InsuranceReadinessService
from app.workflow.synthesis import synthesize_expert_results


def test_insurance_is_not_applicable_when_solution_has_no_insurance_trigger():
    result = InsuranceReadinessService().analyze(
        product_result={"recommendations": [
            {"product_id": "PROD-PAYROLL", "product_family": "payments", "credit_flag": False}
        ]},
        customer_attributes={"industry": "Phân phối thiết bị công nghiệp"},
        documents=[],
        business_snapshot={},
    )
    assert result["status"] == "not_applicable"
    assert result["coverage_checks"] == []
    assert "không áp dụng" in result["conclusion"].lower()


def test_coordinator_keeps_other_accepted_products_as_supporting_solutions():
    recommendations = [
        {"product_id": "PROD-CASH-MGMT", "name": "Quản lý dòng tiền", "matching_reason": "Khớp dòng tiền"},
        {"product_id": "PROD-PAYROLL", "name": "Chi lương", "matching_reason": "Khớp 500 nhân viên"},
        {"product_id": "PROD-BULK-PAYMENT", "name": "Thu chi hộ", "matching_reason": "Khớp đối soát"},
    ]
    eligibility = {"products": [
        {"product_id": item["product_id"], "status": "passed", "rules": []}
        for item in recommendations
    ]}
    result = synthesize_expert_results(
        case_id="CASE-SEMANTIC",
        trace_id="TRACE-SEMANTIC",
        product_result={"recommendations": recommendations},
        eligibility_result=eligibility,
        credit_result={"status": "not_applicable", "missing_information": []},
        insurance_result={"status": "not_applicable", "missing_information": [], "hard_blocks": []},
        alternative_product_result=None,
        alternative_eligibility_result=None,
        findings=[],
    )
    assert result.primary_solution["product_id"] == "PROD-CASH-MGMT"
    assert [item["product_id"] for item in result.alternative_solutions] == [
        "PROD-PAYROLL", "PROD-BULK-PAYMENT"
    ]
