"""Persistent legal RAG acceptance tests."""

from __future__ import annotations

from app.knowledge.legal_service import LegalKnowledgeService


def test_legal_index_is_persistent_and_idempotent(tmp_path):
    path = tmp_path / "legal.sqlite3"
    first = LegalKnowledgeService(path)
    indexed = first.ingest()
    count = first.index.count()
    assert indexed >= 9
    first.ingest()
    assert first.index.count() == count
    assert LegalKnowledgeService(path).index.count() == count


def test_ubo_query_returns_exact_versioned_legal_evidence(tmp_path):
    service = LegalKnowledgeService(tmp_path / "legal.sqlite3")
    hits = service.search(
        "thông tin chủ sở hữu hưởng lợi UBO",
        branch="HN01",
        product_id="PROD-WORKING-CAPITAL",
    )
    assert hits
    assert hits[0].chunk.document_id == "SYN-KYC-POLICY"
    assert hits[0].chunk.document_version == "2026.1"
    assert "hưởng lợi" in hits[0].chunk.text


def test_product_scope_excludes_unrelated_credit_rule(tmp_path):
    service = LegalKnowledgeService(tmp_path / "legal.sqlite3")
    hits = service.search(
        "nợ xấu 12 tháng",
        branch="HN01",
        product_id="PROD-PAYROLL",
    )
    assert all(hit.chunk.product_id in {"*", "PROD-PAYROLL"} for hit in hits)


def test_credit_policy_acl_blocks_unapproved_branch(tmp_path):
    service = LegalKnowledgeService(tmp_path / "legal.sqlite3")
    denied = service.search("báo cáo tài chính", branch="DN01", product_id="PROD-WORKING-CAPITAL")
    assert all(hit.chunk.document_id != "SYN-CREDIT-POLICY" for hit in denied)
