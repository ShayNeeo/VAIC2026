"""Acceptance and leakage tests for the persistent product RAG."""

from __future__ import annotations

from datetime import date

from app.knowledge.ingestion import load_product_chunks
from app.knowledge.service import DEFAULT_PRODUCTS, DEFAULT_SOURCE_CARD, ProductKnowledgeService
from app.data_catalog.registry import load_source_card
from app.product.service import ProductService


def service(tmp_path) -> ProductKnowledgeService:
    knowledge = ProductKnowledgeService(tmp_path / "products.sqlite3")
    report = knowledge.ingest()
    assert report.rejected == 0
    return knowledge


def test_ingestion_is_typed_and_reports_lineage():
    card = load_source_card(DEFAULT_SOURCE_CARD)
    assert card.is_usable_for_serving()
    assert card.tier.value == "E_SYNTHETIC"
    chunks, report = load_product_chunks(DEFAULT_PRODUCTS)
    assert report.accepted == 5
    assert report.indexed == 5
    assert len(report.source_hash) == 64
    assert all(chunk.document_id and chunk.document_version and chunk.content_hash for chunk in chunks)


def test_index_is_persistent_and_upsert_is_idempotent(tmp_path):
    first = service(tmp_path)
    assert first.index.count() == 17
    first.ingest()
    assert first.index.count() == 17
    restarted = ProductKnowledgeService(tmp_path / "products.sqlite3")
    assert restarted.index.count() == 17


def test_payroll_retrieval_has_exact_versioned_evidence(tmp_path):
    hits = service(tmp_path).search("dịch vụ chi trả lương cho 500 nhân viên", branch="HN01")
    assert hits[0].chunk.product_id == "PROD-PAYROLL"
    assert hits[0].chunk.document_version == "2026.1"


def test_expired_product_is_never_served(tmp_path):
    hits = service(tmp_path).index.search(
        "phiên bản cũ payroll",
        branch="HN01",
        as_of=date(2026, 7, 17),
        threshold=0.0,
    )
    assert "PROD-PAYROLL-OLD" not in {item.chunk.product_id for item in hits}


def test_acl_filter_is_applied_before_serving_context(tmp_path):
    knowledge = service(tmp_path)
    denied = knowledge.search(
        "vốn lưu động thấu chi",
        branch="DN01",
        product_ids=["PROD-WORKING-CAPITAL"],
    )
    allowed = knowledge.search(
        "vốn lưu động thấu chi",
        branch="HN01",
        product_ids=["PROD-WORKING-CAPITAL"],
    )
    assert denied == []
    assert allowed[0].chunk.product_id == "PROD-WORKING-CAPITAL"


def test_out_of_scope_query_does_not_return_a_product(tmp_path):
    assert service(tmp_path).search("thời tiết Đà Nẵng ngày mai", branch="HN01") == []


def test_product_recommendation_is_grounded_and_does_not_claim_eligibility(tmp_path):
    result = ProductService(service(tmp_path)).recommend(
        "Tìm gói trả lương",
        branch="HN01",
        segment="CORPORATE",
        customer_attributes={"employees_count": 500},
    )
    recommendation = result["recommendations"][0]
    assert result["status"] == "grounded"
    # PROD-PAYROLL (synthetic) must surface in a payroll query; the SHB public
    # manual payroll product may rank first under the offline local encoder,
    # which is acceptable. Eligibility is never asserted by the product layer.
    payroll_ids = {rec["product_id"] for rec in result["recommendations"]}
    # A payroll query must return a payroll product. Under the key-free local
    # encoder the SHB public-source payroll product (SHB-CORP-PAY-003) can
    # outrank the synthetic one; either is a correct, grounded result.
    assert payroll_ids & {"PROD-PAYROLL", "SHB-CORP-PAY-003"}
    assert recommendation["eligibility"] == "unknown"
    assert recommendation["evidences"][0]["source_document_id"]
