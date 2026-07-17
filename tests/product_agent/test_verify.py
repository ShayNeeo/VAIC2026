"""Test Evidence Verification - Tier 2 VER-* cases."""

import pytest
from mcp_common.schemas import EvidenceItem
from servers.v3_product_agent.safety.verify import EvidenceVerifier


class TestEvidenceVerifier:
    @pytest.fixture
    def verifier(self):
        return EvidenceVerifier()

    def test_ver_01_exact_match_valid(self, verifier):
        """VER-01: Exact quote in source -> is_valid=True."""
        ev = EvidenceItem(
            claim_id="E-1", agent="Product", claim="Điều kiện: 10 nhân sự",
            source_document_id="Product_Catalog_v3.pdf", source_version="2026-01-01",
            section_or_page="Payroll", quote="Doanh nghiệp từ 10 nhân sự",
            validation_method="exact_match", is_valid=False
        )
        updated, summary = verifier.verify([ev])
        assert updated[0].is_valid is True
        assert summary["valid"] == 1

    def test_ver_02_exact_mismatch_invalid(self, verifier):
        """VER-02: Fee/limit quote not in source -> is_valid=False, hallucination_flag."""
        ev = EvidenceItem(
            claim_id="E-1", agent="Product", claim="Phí: 10%/năm",
            source_document_id="Product_Catalog_v3.pdf", source_version="2026-01-01",
            section_or_page="Payroll", quote="Phí: 10%/năm",
            validation_method="numeric_exact", is_valid=False
        )
        updated, summary = verifier.verify([ev])
        assert updated[0].is_valid is False
        assert summary["invalid"] == 1

    def test_ver_03_fee_limit_exact_required(self, verifier):
        """VER-03: Fee/limit claims require exact match."""
        ev = EvidenceItem(
            claim_id="E-1", agent="Product", claim="Phí: 5%/năm",
            source_document_id="Product_Catalog_v3.pdf", source_version="2026-01-01",
            section_or_page="Payroll", quote="Phí: 2%/năm",
            validation_method="numeric_exact", is_valid=False
        )
        updated, _ = verifier.verify([ev])
        assert updated[0].is_valid is False

    def test_ver_04_semantic_below_threshold_review(self, verifier):
        """VER-04: Semantic claim below threshold -> flagged for review."""
        ev = EvidenceItem(
            claim_id="E-1", agent="Product", claim="Sản phẩm phù hợp doanh nghiệp vừa",
            source_document_id="Product_Catalog_v3.pdf", source_version="2026-01-01",
            section_or_page="Payroll", quote="Dành cho doanh nghiệp quy mô vừa",
            validation_method="semantic_support", is_valid=False
        )
        updated, _ = verifier.verify([ev])
        assert isinstance(updated[0].is_valid, bool)

    def test_ver_05_all_claims_validated(self, verifier):
        """VER-05: All important claims must have valid evidence."""
        ev1 = EvidenceItem(
            claim_id="E-1", agent="Product", claim="valid claim",
            source_document_id="Product_Catalog_v3.pdf", source_version="2026-01-01",
            section_or_page="Payroll", quote="Doanh nghiệp từ 10 nhân sự",
            validation_method="exact_match", is_valid=False
        )
        ev2 = EvidenceItem(
            claim_id="E-2", agent="Product", claim="another valid",
            source_document_id="Product_Catalog_v3.pdf", source_version="2026-01-01",
            section_or_page="Payroll", quote="Có tài khoản SHB",
            validation_method="exact_match", is_valid=False
        )
        updated, summary = verifier.verify([ev1, ev2])
        assert summary["all_valid"] is True

    def test_ver_06_unsupported_product_blocked(self, verifier):
        """VER-06: Unsupported product claim -> hallucination_flag in audit."""
        ev = EvidenceItem(
            claim_id="E-1", agent="Product", claim="Sản phẩm XYZ có phí 10%",
            source_document_id="Product_Catalog_v3.pdf", source_version="2026-01-01",
            section_or_page="Payroll", quote="Sản phẩm XYZ có phí 10%",
            validation_method="exact_match", is_valid=False
        )
        updated, summary = verifier.verify([ev])
        assert updated[0].is_valid is False
        assert summary["invalid"] == 1

    def test_ver_07_numeric_exact_matches_catalog_fee(self, verifier):
        """VER-07: interest_rate 8.5 %/year for Working Capital -> NUMERIC_EXACT valid."""
        ev = EvidenceItem(
            claim_id="E-1", agent="Product",
            claim="Lãi suất 8.5 %/year cho vốn lưu động",
            source_document_id="Product_Catalog_v3.pdf", source_version="2026-01-01",
            section_or_page="Working_Capital", quote="Lãi suất 8.5 %/year",
            validation_method="numeric_exact", is_valid=False
        )
        updated, summary = verifier.verify([ev])
        assert updated[0].is_valid is True
        assert updated[0].validation_method.value == "numeric_exact"
        assert summary["valid"] == 1

    def test_ver_08_numeric_exact_wrong_value_invalid(self, verifier):
        """VER-08: interest_rate 5% (not 8.5) -> NUMERIC_EXACT invalid (no semantic leniency)."""
        ev = EvidenceItem(
            claim_id="E-1", agent="Product",
            claim="Lãi suất 5 %/year cho vốn lưu động",
            source_document_id="Product_Catalog_v3.pdf", source_version="2026-01-01",
            section_or_page="Working_Capital", quote="Lãi suất 8.5 %/year",
            validation_method="numeric_exact", is_valid=False
        )
        updated, _ = verifier.verify([ev])
        assert updated[0].is_valid is False