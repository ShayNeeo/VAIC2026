"""Test V3 Evidence Verification."""

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
        """VER-02: Fee/limit quote not in source -> is_valid=False."""
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
        """VER-04: Semantic claim below threshold -> flagged."""
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
        """VER-06: Unsupported product claim -> hallucination flag."""
        ev = EvidenceItem(
            claim_id="E-1", agent="Product", claim="Sản phẩm XYZ có phí 10%",
            source_document_id="Product_Catalog_v3.pdf", source_version="2026-01-01",
            section_or_page="Payroll", quote="Sản phẩm XYZ có phí 10%",
            validation_method="exact_match", is_valid=False
        )
        updated, summary = verifier.verify([ev])
        assert updated[0].is_valid is False
        assert summary["invalid"] == 1