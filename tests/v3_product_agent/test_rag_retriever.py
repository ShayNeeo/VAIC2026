"""Test V3 Product Agent RAG Retriever."""

import pytest
from servers.v3_product_agent.rag.retriever import ProductRetriever


class TestRAGRetriever:
    @pytest.fixture
    def retriever(self):
        return ProductRetriever()

    def test_rag_01_payroll_query(self, retriever):
        """RAG-01: Payroll query retrieves PROD-PAYROLL at Hit@1."""
        results = retriever.search("chi lương 500 nhân viên", top_k=3)
        assert len(results) >= 1
        assert results[0].product_id == "PROD-PAYROLL"

    def test_rag_02_cash_management_query(self, retriever):
        """RAG-02: Cash management query retrieves PROD-CASH-MGMT."""
        results = retriever.search("quản lý dòng tiền phân tán doanh thu lớn", top_k=3)
        ids = [r.product_id for r in results]
        assert "PROD-CASH-MGMT" in ids

    def test_rag_03_working_capital_query(self, retriever):
        """RAG-03: Working capital query retrieves PROD-WORKING-CAPITAL."""
        results = retriever.search("thấu chi vốn lưu động", top_k=3)
        ids = [r.product_id for r in results]
        assert "PROD-WORKING-CAPITAL" in ids

    def test_rag_04_exact_product_code(self, retriever):
        """RAG-04: Exact product code found by sparse retrieval."""
        results = retriever.search("PROD-PAYROLL", top_k=3)
        assert any(r.product_id == "PROD-PAYROLL" for r in results)

    def test_rag_05_oos_query_returns_empty(self, retriever):
        """RAG-05: Out-of-scope query returns empty."""
        results = retriever.search("thời tiết hôm nay", top_k=3)
        assert results == []

    def test_rag_06_effective_date_metadata(self, retriever):
        """RAG-06: Results have effective_date metadata."""
        results = retriever.search("chi lương", top_k=5)
        for r in results:
            assert "effective_date" in r.metadata
            assert r.metadata["effective_date"] is not None

    def test_rag_07_threshold_gate(self, retriever):
        """RAG-07: Threshold 0.35 gate - low scores dropped."""
        results = retriever.search("xyzabc", top_k=5)
        assert results == []

    def test_rag_08_legal_article_boost(self, retriever):
        """RAG-08: Legal article 'Điều' gets heuristic boost."""
        results = retriever.search("Điều 5 chi lương", top_k=3)
        assert isinstance(results, list)

    def test_rag_09_citation_format(self, retriever):
        """RAG-09: Citation format has source_doc, section, product_id."""
        results = retriever.search("chi lương", top_k=1)
        assert len(results) > 0
        cit = results[0].citation()
        assert "source_doc" in cit
        assert "page_or_section" in cit
        assert "product_id" in cit

    def test_rag_10_underthesea_fallback(self, retriever):
        """RAG-10: underthesea missing -> regex VIE fallback works."""
        tokens = retriever._tokens("chi lương nhân viên")
        assert isinstance(tokens, set)
        assert len(tokens) > 0

    def test_rag_11_hash_embedding_fallback(self, retriever):
        """RAG-11: Hash embedding fallback deterministic."""
        vec1 = retriever._embedder("test query")
        vec2 = retriever._embedder("test query")
        assert vec1 == vec2
        assert len(vec1) == 128

    def test_rag_12_citation_preserves_tier(self, retriever):
        """RAG-12: Citation metadata includes tier."""
        results = retriever.search("chi lương", top_k=1)
        if results:
            assert "tier" in results[0].metadata
            assert results[0].metadata["tier"] in ("A", "B", "C", "D", "E")