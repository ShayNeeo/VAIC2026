from app.rag.product_retriever import ProductRAGService


def test_payroll_query_returns_grounded_product_source():
    rag = ProductRAGService()
    results = rag.search("Doanh nghiệp cần dịch vụ chi trả lương cho 500 nhân viên")

    assert results
    assert results[0].product_id == "PROD-PAYROLL"
    assert results[0].source_doc == "SHB_Product_Catalog_2026.pdf"


def test_rag_context_contains_citations_and_grounding_flag():
    context = ProductRAGService().build_context("giải pháp quản lý dòng tiền nhiều tài khoản")

    assert context["grounded"] is True
    assert context["sources"]
    assert "SHB_Cash_Management_Policy.pdf" in context["context"]


def test_out_of_scope_query_is_filtered_by_threshold():
    context = ProductRAGService().build_context("thời tiết Hà Nội hôm nay")

    assert context["grounded"] is False
    assert context["sources"] == []


def test_query_normalization_preserves_vietnamese_text():
    assert ProductRAGService.normalize_query("  Payroll   cho ABC!!! ") == "Payroll cho ABC!"

