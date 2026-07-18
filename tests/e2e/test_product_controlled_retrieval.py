"""Phase 2 E2E: Product Agent through ControlledRetrievalOrchestrator.

Unlike Legal/Operations, this test ingests chunks directly rather than
through app/product/service.py's ProductService: that file had active,
uncommitted concurrent edits from another agent during this Phase (see
docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md Phase 2 "Agent Migration"),
so it was not modified or imported into new test coverage to avoid
colliding with in-flight work this session did not author. The chunks
below are built from data/synthetic/v3/products/product_catalog.json's
real field shape (product_name/category/features/supported_needs), tagged
with the authority_tier/verification_status a real ingestion pass would
assign to an internally-governed product catalog."""

from __future__ import annotations

from datetime import date, datetime, timezone

from app.knowledge.index import LocalEmbedding, PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk
from app.knowledge.retrieval_contracts import (
    AgentType, AuthorityTier, RetrievalRequest, RetrievalStatus, VerificationStatus,
)
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator


def _product_index(tmp_path) -> PersistentHybridIndex:
    index = PersistentHybridIndex(tmp_path / "product.sqlite3", provider=LocalEmbedding())
    index.upsert(
        [
            KnowledgeChunk(
                chunk_id="SYNTH-PROD-PAYROLL:overview:1.0", document_id="SYNTH-DOC-PRODUCT-003",
                document_version="1.0", product_id="SYNTH-PROD-PAYROLL", section_path="overview",
                chunk_type="product_overview",
                text="Dịch vụ chi lương doanh nghiệp | nhu cầu: payroll_processing, salary_account_opening | "
                     "yêu cầu: business_registration, employee_headcount_confirmation",
                effective_from=date(2026, 1, 1), effective_to=None, active=True, segments=[],
                access_scope={"branches": ["*"]}, content_hash="hash-payroll",
                source_type="product_catalog", authority_tier=AuthorityTier.TIER_1_AUTHORITATIVE,
                verification_status=VerificationStatus.VERIFIED,
            ),
            KnowledgeChunk(
                chunk_id="SYNTH-PROD-CASH-MGMT:overview:1.0", document_id="SYNTH-DOC-PRODUCT-005",
                document_version="1.0", product_id="SYNTH-PROD-CASH-MGMT", section_path="overview",
                chunk_type="product_overview",
                text="Quản lý dòng tiền tập trung | nhu cầu: cash_pooling, multi_account_visibility",
                effective_from=date(2026, 1, 1), effective_to=None, active=True, segments=[],
                access_scope={"branches": ["*"]}, content_hash="hash-cashmgmt",
                source_type="product_catalog", authority_tier=AuthorityTier.TIER_1_AUTHORITATIVE,
                verification_status=VerificationStatus.VERIFIED,
            ),
        ],
        source_hash="s1", dataset_version="v3.2026.07.18",
    )
    return index


def test_product_agent_retrieves_the_matching_product_and_not_the_unrelated_one(tmp_path):
    orchestrator = ControlledRetrievalOrchestrator(_product_index(tmp_path))
    request = RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="RM", agent_type=AgentType.PRODUCT,
        task_type="product_search", raw_query="chi luong", normalized_query="dich vu chi luong nhan su",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-product-v1",
    )
    result = orchestrator.retrieve(request)
    assert result.diagnostics.status == RetrievalStatus.OK
    assert result.grounding_pack is not None
    chunk_ids = {item.chunk_id for item in result.grounding_pack.items}
    assert "SYNTH-PROD-PAYROLL:overview:1.0" in chunk_ids


def test_product_agent_exact_lookup_by_product_id_bypasses_ranking(tmp_path):
    orchestrator = ControlledRetrievalOrchestrator(_product_index(tmp_path))
    request = RetrievalRequest(
        request_id="r2", trace_id="t2", actor_id="u1", actor_role="RM", agent_type=AgentType.PRODUCT,
        task_type="product_search", raw_query="", normalized_query="",
        product_ids=["SYNTH-PROD-CASH-MGMT"],
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-product-v1",
    )
    result = orchestrator.retrieve(request)
    assert result.grounding_pack is not None
    assert len(result.grounding_pack.items) == 1
    assert result.grounding_pack.items[0].chunk_id == "SYNTH-PROD-CASH-MGMT:overview:1.0"
    assert result.grounding_pack.items[0].retrieval_channel.value == "exact"
