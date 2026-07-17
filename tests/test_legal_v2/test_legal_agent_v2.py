"""Tests for LegalAgentV2."""

import json
from pathlib import Path
from app.schemas.state import SharedCaseState
from app.legal.adapter import LegalAgentV2

def test_legal_agent_v2_comp_abc():
    agent = LegalAgentV2()
    
    # Load comp_abc
    abc_path = Path("data/legal/sample_companies/comp_abc.json")
    if abc_path.exists():
        with open(abc_path, "r", encoding="utf-8") as f:
            comp_profile = json.load(f)
    else:
        # Fallback for CI/local without data
        comp_profile = {
            "customer_id": "COMP-ABC",
            "company_name": "Công ty TNHH Sản xuất ABC",
            "tax_code": "0123456789",
            "ubo_status": "missing",
            "financial_reports": {"has_recent": False},
            "representative": {"name": "A", "id_number": "123"}
        }
        
    state = SharedCaseState(
        case_id="1", employee_id="2", rm_id="2", customer_id="COMP-ABC",
        company_profile=comp_profile,
        documents=[
            {"document_type_id": "BUSINESS_REGISTRATION", "is_expired": False},
            {"document_type_id": "IDENTITY_DOCUMENT", "is_expired": False},
        ],
        product_result={"recommended_products": [
            {"product_id": "PROD-WORKING-CAPITAL"},
            {"product_id": "PROD-PAYROLL"}
        ]}
    )
    
    output = agent.run(state)
    
    # Verify backward compatible fields
    assert output["eligibility_status"] == "pending_information"
    assert "missing_documents" in output
    
    # Verify extended fields
    assert output["risk_level"] == "high"
    assert output["review_required"] is False
    
    # Payroll should pass, Working Capital should fail (pending_info)
    results = output["per_product_eligibility"]
    for res in results:
        if res["product_id"] == "PROD-PAYROLL":
            assert res["status"] == "passed"
        elif res["product_id"] == "PROD-WORKING-CAPITAL":
            assert res["status"] == "pending_information"
            
    # Should have citations for the failed rules
    assert len(output["citations"]) > 0

def test_legal_agent_v2_watchlist():
    agent = LegalAgentV2()
    
    comp_profile = {
        "customer_id": "COMP-SANC",
        "company_name": "Công ty TNHH Thương mại Đen Demo",
        "tax_code": "9999999999",
        "ubo_status": "complete",
        "financial_reports": {"has_recent": True},
        "representative": {"name": "A", "id_number": "123"}
    }
    
    state = SharedCaseState(
        case_id="2", employee_id="2", rm_id="2", customer_id="COMP-SANC",
        company_profile=comp_profile,
        documents=[
            {"document_type_id": "BUSINESS_REGISTRATION", "is_expired": False},
            {"document_type_id": "IDENTITY_DOCUMENT", "is_expired": False},
            {"document_type_id": "UBO_DECLARATION", "is_expired": False},
            {"document_type_id": "FINANCIAL_STATEMENT", "is_expired": False},
        ],
        product_result={"recommended_products": [{"product_id": "PROD-WORKING-CAPITAL"}]}
    )
    
    output = agent.run(state)
    
    assert output["eligibility_status"] == "failed"
    assert output["risk_level"] == "high"
    assert output["review_required"] is True
