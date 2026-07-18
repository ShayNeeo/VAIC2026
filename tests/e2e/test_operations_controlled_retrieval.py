"""Phase 2 E2E: Operations Agent through ControlledRetrievalOrchestrator,
using the new OperationsKnowledgeService (real SOP step ingestion from
data/synthetic/v3/operations/sop_workflow.json). Proves the audit finding
"Operations Agent không có retrieval nào" (docs/RAG_GUARDRAIL_CURRENT_STATE_AUDIT.md)
now has a real, tested, cited retrieval path available -- without
claiming OperationsService.prepare() itself was migrated (it was not, see
app/operations/sop_knowledge.py module docstring)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.knowledge.index import LocalEmbedding
from app.knowledge.retrieval_contracts import AgentType, RetrievalRequest, RetrievalStatus
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator
from app.operations.sop_knowledge import OperationsKnowledgeService


def test_operations_agent_retrieves_only_the_requested_products_sop_steps(tmp_path):
    svc = OperationsKnowledgeService(index_path=tmp_path / "ops.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    orchestrator = ControlledRetrievalOrchestrator(svc.index)
    request = RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="RM", agent_type=AgentType.OPERATIONS,
        task_type="ops_search", raw_query="buoc tiep theo", normalized_query="buoc tiep theo can lam gi",
        product_ids=["SYNTH-PROD-PAYROLL"],
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-operations-v1",
    )
    result = orchestrator.retrieve(request)
    assert result.diagnostics.status == RetrievalStatus.OK
    assert result.grounding_pack is not None
    assert len(result.grounding_pack.items) > 0
    for item in result.grounding_pack.items:
        assert item.chunk_id.split(":")[0] == "SYNTH-SOP-CORP-SALES-002"  # the Payroll workflow_id


def test_operations_agent_gets_no_result_not_an_error_when_product_has_no_sop(tmp_path):
    """OPERATIONS policy has fail_closed=False (unlike Legal) -- a product
    with no SOP steps indexed must be a normal empty result, not a hard
    error, since operations readiness for an unmodeled product is a
    legitimate "nothing to say yet" case rather than a security failure."""
    svc = OperationsKnowledgeService(index_path=tmp_path / "ops2.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    orchestrator = ControlledRetrievalOrchestrator(svc.index)
    request = RetrievalRequest(
        request_id="r2", trace_id="t2", actor_id="u1", actor_role="RM", agent_type=AgentType.OPERATIONS,
        task_type="ops_search", raw_query="buoc tiep theo", normalized_query="buoc tiep theo can lam gi",
        product_ids=["SYNTH-PROD-DOES-NOT-EXIST"],
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-operations-v1",
    )
    result = orchestrator.retrieve(request)
    assert result.diagnostics.status == RetrievalStatus.OK
    assert result.grounding_pack is None
