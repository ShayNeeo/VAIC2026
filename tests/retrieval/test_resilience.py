"""Phase 5 section 49: resilience -- Legal fails closed, Product/Operations
degrade gracefully, on a provider/index failure. Reuses the orchestrator
paths already built in Phase 2 rather than a new resilience layer; this
file asserts the DISTINCTION the prompt requires exists and is testable
in one place."""

from __future__ import annotations

from datetime import datetime, timezone

from app.knowledge.index import LocalEmbedding, PersistentHybridIndex
from app.knowledge.retrieval_contracts import AgentType, RetrievalErrorCode, RetrievalRequest, RetrievalStatus
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator


def _request(agent_type: AgentType, policy_id: str) -> RetrievalRequest:
    return RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="RM", agent_type=agent_type,
        task_type="search", raw_query="von luu dong", normalized_query="von luu dong",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id=policy_id,
    )


def test_legal_source_unavailable_fails_closed(tmp_path):
    index = PersistentHybridIndex(tmp_path / "empty.sqlite3", provider=LocalEmbedding())
    orchestrator = ControlledRetrievalOrchestrator(index)
    result = orchestrator.retrieve(_request(AgentType.LEGAL_POLICY, "retrieval-policy-legal-v1"))
    assert result.diagnostics.status == RetrievalStatus.ERROR
    assert result.diagnostics.error_code == RetrievalErrorCode.SOURCE_SCOPE_EMPTY


def test_product_source_unavailable_degrades_without_error(tmp_path):
    """Product exploratory error: "degraded + warning + no grounded
    recommendation" -- OK status (not ERROR), no grounding pack, an
    explicit reason code the caller can surface as a warning."""
    index = PersistentHybridIndex(tmp_path / "empty2.sqlite3", provider=LocalEmbedding())
    orchestrator = ControlledRetrievalOrchestrator(index)
    result = orchestrator.retrieve(_request(AgentType.PRODUCT, "retrieval-policy-product-v1"))
    assert result.diagnostics.status == RetrievalStatus.OK
    assert result.diagnostics.error_code == RetrievalErrorCode.NO_RELEVANT_RESULT
    assert result.grounding_pack is None


def test_operations_source_unavailable_produces_no_executable_steps(tmp_path):
    """Operations SOP error: "không sinh executable steps" -- same shape
    as Product (OK + no grounding pack), verified separately because
    Operations' policy has different fail_closed/authority defaults and
    this must hold regardless."""
    index = PersistentHybridIndex(tmp_path / "empty3.sqlite3", provider=LocalEmbedding())
    orchestrator = ControlledRetrievalOrchestrator(index)
    result = orchestrator.retrieve(_request(AgentType.OPERATIONS, "retrieval-policy-operations-v1"))
    assert result.diagnostics.status == RetrievalStatus.OK
    assert result.grounding_pack is None


def test_index_not_ready_and_no_relevant_result_remain_distinguishable_through_the_orchestrator(tmp_path):
    """Phase 0's core distinction (INDEX_NOT_READY vs NO_RELEVANT_RESULT)
    must still be recoverable at the orchestrator layer via
    candidate_count_before_filter, not collapsed into one generic
    failure."""
    from app.knowledge.legal_service import LegalKnowledgeService

    empty_index = PersistentHybridIndex(tmp_path / "empty4.sqlite3", provider=LocalEmbedding())
    orchestrator_empty = ControlledRetrievalOrchestrator(empty_index)
    result_empty = orchestrator_empty.retrieve(_request(AgentType.PRODUCT, "retrieval-policy-product-v1"))
    assert result_empty.diagnostics.candidate_count_before_filter == 0

    svc = LegalKnowledgeService(index_path=tmp_path / "legal.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    orchestrator_populated = ControlledRetrievalOrchestrator(svc.index)
    no_match_request = RetrievalRequest(
        request_id="r2", trace_id="t2", actor_id="u1", actor_role="RM", agent_type=AgentType.PRODUCT,
        task_type="search", raw_query="hoan toan khong lien quan toi ngan hang", normalized_query="hoan toan khong lien quan toi ngan hang du lich vu tru",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-product-v1",
    )
    result_no_match = orchestrator_populated.retrieve(no_match_request)
    assert result_no_match.diagnostics.candidate_count_before_filter > 0
