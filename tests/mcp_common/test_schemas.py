"""Test mcp_common schemas contract validation."""

import pytest
from mcp_common.schemas import (
    SharedCaseState,
    EvidenceItem,
    ProductResult,
    EligibilityResult,
    OperationsResult,
    ApprovalToken,
    ErrorContract,
    CreateCaseRequest,
)


class TestSchemas:
    def test_valid_minimal_product_result(self):
        pr = ProductResult(
            recommended_bundle={"bundle_name": "Test", "products": [], "bundle_reason": ""},
            recommended_products=[],
            missing_parameters=["need"],
            retrieval_query="test",
            citations=[],
            guardrail_verdict={"input_allowed": True, "output_allowed": True},
        )
        assert pr.schema_version == "3.0.0"

    def test_valid_full_shared_case_state(self):
        state = SharedCaseState(
            case_id="CORP-001",
            customer_id="COMP-ABC",
            rm_id="RM-001",
        )
        assert state.final_status == "new"
        assert state.schema_version == "3.0.0"

    def test_invalid_final_status_enum(self):
        with pytest.raises(Exception):
            SharedCaseState(
                case_id="CORP-001",
                customer_id="COMP-ABC",
                rm_id="RM-001",
                final_status="invalid_status",
            )

    def test_missing_required_case_id(self):
        with pytest.raises(Exception):
            SharedCaseState(customer_id="COMP-ABC", rm_id="RM-001")

    def test_confidence_out_of_range_rejected(self):
        from mcp_common.schemas import ResolvedValue
        with pytest.raises(Exception):
            ResolvedValue(value="x", source_type="user_explicit", confidence=1.5)

    def test_evidence_item_missing_quote(self):
        with pytest.raises(Exception):
            EvidenceItem(
                claim_id="E-1",
                agent="Product",
                claim="test",
                source_document_id="doc.pdf",
                source_version="v1",
                section_or_page="p1",
                validation_method="exact_match",
            )

    def test_error_contract_shape(self):
        err = ErrorContract(
            error_code="TEST_ERROR",
            message="test",
            retryable=True,
            safe_to_retry=True,
            correlation_id="trace-123",
        )
        assert err.error_code == "TEST_ERROR"

    def test_old_version_migration(self):
        state = SharedCaseState(case_id="C", customer_id="X", rm_id="R")
        assert "schema_version" in state.model_dump()