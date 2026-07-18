"""Phase 3 section 22: rule-based strategy selection."""

from __future__ import annotations

from app.knowledge.query_router import RetrievalStrategy, route_query
from app.knowledge.query_understanding import understand_query
from app.knowledge.retrieval_contracts import AgentType


def test_exact_id_only_query_routes_to_exact_only():
    understanding = understand_query("SYNTH-PROD-PAYROLL")
    assert route_query(understanding, AgentType.PRODUCT) == RetrievalStrategy.EXACT_ONLY


def test_legal_eligibility_question_routes_to_policy_first():
    understanding = understand_query("dieu kien vay von luu dong")
    assert route_query(understanding, AgentType.LEGAL_POLICY) == RetrievalStrategy.POLICY_FIRST


def test_product_discovery_without_exact_id_routes_to_hybrid_rrf():
    understanding = understand_query("giai phap ngan hang cho doanh nghiep nho")
    assert route_query(understanding, AgentType.PRODUCT) == RetrievalStrategy.HYBRID_RRF


def test_empty_query_routes_to_abstain():
    understanding = understand_query("")
    assert route_query(understanding, AgentType.PRODUCT) == RetrievalStrategy.ABSTAIN


def test_multi_hop_query_routes_to_multi_hop():
    understanding = understand_query("SYNTH-PROD-PAYROLL va SYNTH-PROD-CASH-MGMT can gi")
    assert route_query(understanding, AgentType.PRODUCT) == RetrievalStrategy.MULTI_HOP


def test_document_lookup_routes_to_evidence_first():
    understanding = understand_query("ho so tai lieu can nop la gi")
    assert route_query(understanding, AgentType.OPERATIONS) == RetrievalStrategy.EVIDENCE_FIRST
