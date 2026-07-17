"""Test V3 Product Matcher - 7 core cases matching blueprint §7."""

import pytest
from servers.v3_product_agent.product.matcher import ProductMatcher
from servers.v3_product_agent.rag.retriever import ProductRetrievalResult


class TestProductMatcher:
    @pytest.fixture
    def matcher(self):
        return ProductMatcher()

    def test_mat_01_payroll_employees_ge_10(self, matcher):
        """MAT-01: Payroll + employees>=10 -> score boost."""
        result = matcher.run(
            request_text="chi lương",
            profile={"employees_count": 50, "annual_revenue": 100_000_000_000, "cash_flow_status": "bình thường"},
            retrieval_results=[],
        )
        payroll = next(p for p in result["recommended_bundle"].products if p.product_id == "PROD-PAYROLL")
        assert payroll.match_score.total >= 0.90

    def test_mat_02_cash_mgmt_revenue_ge_50b(self, matcher):
        """MAT-02: Cash Mgmt + revenue>=50B -> score boost."""
        result = matcher.run(
            request_text="dòng tiền",
            profile={"employees_count": 50, "annual_revenue": 60_000_000_000, "cash_flow_status": "phân tán"},
            retrieval_results=[],
        )
        cm = next(p for p in result["recommended_bundle"].products if p.product_id == "PROD-CASH-MGMT")
        assert cm.match_score.total >= 0.90

    def test_mat_03_working_capital_keywords(self, matcher):
        """MAT-03: Working Capital keywords -> score boost."""
        result = matcher.run(
            request_text="cần thấu chi vốn lưu động",
            profile={"employees_count": 100, "annual_revenue": 200_000_000_000, "cash_flow_status": "tốt"},
            retrieval_results=[],
        )
        wc = next(p for p in result["recommended_bundle"].products if p.product_id == "PROD-WORKING-CAPITAL")
        assert wc.match_score.total >= 0.90

    def test_mat_04_no_keywords_returns_missing(self, matcher):
        """MAT-04: No product keywords -> missing_parameters."""
        result = matcher.run(
            request_text="xin chào",
            profile={"employees_count": 10, "annual_revenue": 1_000_000_000, "cash_flow_status": "bình thường"},
            retrieval_results=[],
        )
        assert "product_need_unresolved" in result["missing_parameters"]

    def test_mat_05_dedupe_preserves_order(self, matcher):
        """MAT-05: Duplicate product IDs deduplicated."""
        result = matcher.run(
            request_text="chi lương trả lương",
            profile={"employees_count": 200, "annual_revenue": 100_000_000_000, "cash_flow_status": "bình thường"},
            retrieval_results=[],
        )
        ids = result["recommended_products"]
        assert len(ids) == len(set(ids))

    def test_mat_06_bundle_name_multi_product(self, matcher):
        """MAT-06: Bundle name for >1 product."""
        result = matcher.run(
            request_text="chi lương dòng tiền",
            profile={"employees_count": 200, "annual_revenue": 60_000_000_000, "cash_flow_status": "phân tán"},
            retrieval_results=[],
        )
        assert "tổng hợp" in result["recommended_bundle"].bundle_name.lower()

    def test_mat_07_score_cap_0_99(self, matcher):
        """MAT-07: Score capped at 0.99."""
        result = matcher.run(
            request_text="chi lương thấu chi",
            profile={"employees_count": 500, "annual_revenue": 100_000_000_000, "cash_flow_status": "phân tán"},
            retrieval_results=[],
        )
        for p in result["recommended_bundle"].products:
            assert p.match_score.total <= 0.99

    def test_retrieval_score_passed_through(self, matcher):
        """Retrieval score from RAG passed to matcher output."""
        from servers.v3_product_agent.rag.retriever import ProductRetrievalResult
        mock_retrieval = [ProductRetrievalResult(
            product_id="PROD-PAYROLL",
            score=0.95,
            text="test",
            source_doc="doc.pdf",
            section="Payroll",
            metadata={},
        )]
        result = matcher.run(
            request_text="chi lương",
            profile={"employees_count": 100, "annual_revenue": 1e11},
            retrieval_results=mock_retrieval,
        )
        payroll = next(p for p in result["recommended_bundle"].products if p.product_id == "PROD-PAYROLL")
        assert payroll.retrieval_score == 0.95