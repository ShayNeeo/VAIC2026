"""Tests for Rule Engine."""

from app.schemas.state import SharedCaseState
from app.legal.models import LegalProfile, RepresentativeInfo, UBOInfo
from app.legal.rule_registry import RuleRegistry
from app.legal.rule_engine import RuleEngine

def test_rule_engine():
    registry = RuleRegistry()
    engine = RuleEngine(registry)
    
    # Test valid profile
    rep = RepresentativeInfo(name="A", id_number="123")
    ubo = UBOInfo(status="complete", doc_present=True)
    profile = LegalProfile(
        has_business_reg=True,
        has_financial_reports=True,
        representative=rep,
        ubo=ubo
    )
    
    state = SharedCaseState(
        case_id="1", employee_id="2", rm_id="2", customer_id="3",
        company_profile={}, documents=[],
        product_result={"recommended_products": [{"product_id": "PROD-WORKING-CAPITAL"}]}
    )
    
    results = engine.evaluate_all_products(state, profile)
    
    assert len(results) == 1
    assert results[0].status == "passed"
    assert len(results[0].blocking_rules) == 0

def test_rule_engine_missing_ubo():
    registry = RuleRegistry()
    engine = RuleEngine(registry)
    
    rep = RepresentativeInfo(name="A", id_number="123")
    ubo = UBOInfo(status="missing", doc_present=False) # Missing UBO
    profile = LegalProfile(
        has_business_reg=True,
        has_financial_reports=True,
        representative=rep,
        ubo=ubo
    )
    
    state = SharedCaseState(
        case_id="1", employee_id="2", rm_id="2", customer_id="3",
        company_profile={}, documents=[],
        product_result={"recommended_products": [{"product_id": "PROD-WORKING-CAPITAL"}]}
    )
    
    results = engine.evaluate_all_products(state, profile)
    
    assert results[0].status == "pending_information"
    
    # Payroll does not require UBO
    state.product_result = {"recommended_products": [{"product_id": "PROD-PAYROLL"}]}
    results2 = engine.evaluate_all_products(state, profile)
    assert results2[0].status == "passed"
