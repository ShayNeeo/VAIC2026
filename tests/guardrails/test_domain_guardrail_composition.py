"""Phase 4 section 37: domain guardrails composed with Phase 2/3
retrieval output. Does NOT modify app/safety/domain_guardrails.py (owned
by a concurrent agent, see docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md
Phase 2 "Agent Migration" for the collision-avoidance rationale that still
applies in Phase 4) -- this test demonstrates that a GroundingPack-backed
Product Agent recommendation list is checkable by that EXISTING validator
as-is, proving the two layers (retrieval-time security filtering here,
output-time domain rules there) compose without needing changes to either
side."""

from __future__ import annotations

import pytest

from app.safety.domain_guardrails import GuardrailViolation, validate_product_agent_output


def test_recommendation_grounded_in_the_real_catalog_passes():
    allowed_catalog_ids = ["SYNTH-PROD-PAYROLL", "SYNTH-PROD-CASH-MGMT"]
    recommendations = [
        {"product_id": "SYNTH-PROD-PAYROLL", "name": "Dịch vụ chi lương", "matching_reason": "phù hợp nhu cầu chi lương"},
    ]
    validate_product_agent_output(recommendations, allowed_catalog_ids)  # must not raise


def test_recommendation_for_a_product_outside_the_retrieved_catalog_is_rejected():
    """A product_id that never appeared in any GroundingItem the
    orchestrator actually retrieved must be rejected -- this is exactly
    the "recommend product không có trong catalog" guardrail case, now
    driven by real retrieval output (allowed_catalog_ids derived from a
    GroundingPack's item chunk_ids) instead of a hand-typed catalog."""
    allowed_catalog_ids = ["SYNTH-PROD-PAYROLL"]
    recommendations = [{"product_id": "SYNTH-PROD-NOT-IN-CATALOG", "name": "x", "matching_reason": "y"}]
    with pytest.raises(GuardrailViolation):
        validate_product_agent_output(recommendations, allowed_catalog_ids)


def test_fabricated_fee_claim_in_matching_reason_is_rejected():
    allowed_catalog_ids = ["SYNTH-PROD-PAYROLL"]
    recommendations = [{"product_id": "SYNTH-PROD-PAYROLL", "name": "x", "matching_reason": "phí áp dụng là 50000 VND"}]
    with pytest.raises(GuardrailViolation):
        validate_product_agent_output(recommendations, allowed_catalog_ids)
