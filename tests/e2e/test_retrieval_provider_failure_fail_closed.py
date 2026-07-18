"""Phase 2 section 18 hard gate:
provider_failure_reported_as_no_result = 0, extended to the pipeline
level. When Legal's policy source is completely absent (empty index) --
the retrieval-layer analogue of "provider unavailable" -- the orchestrator
must fail closed with an explicit ERROR/SOURCE_SCOPE_EMPTY, never a quiet
RetrievalStatus.OK carrying zero items that a caller might treat as "no
applicable policy, proceed"."""

from __future__ import annotations

from datetime import datetime, timezone

from app.knowledge.index import LocalEmbedding, PersistentHybridIndex
from app.knowledge.retrieval_contracts import AgentType, RetrievalErrorCode, RetrievalRequest, RetrievalStatus
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator


def test_legal_agent_against_an_empty_index_fails_closed_not_silently_ok(tmp_path):
    index = PersistentHybridIndex(tmp_path / "empty.sqlite3", provider=LocalEmbedding())
    orchestrator = ControlledRetrievalOrchestrator(index)
    request = RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="LegalExpert",
        agent_type=AgentType.LEGAL_POLICY, task_type="legal_search",
        raw_query="UBO", normalized_query="UBO xac minh",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-legal-v1",
    )
    result = orchestrator.retrieve(request)
    assert result.diagnostics.status == RetrievalStatus.ERROR
    assert result.diagnostics.error_code == RetrievalErrorCode.SOURCE_SCOPE_EMPTY
    assert result.grounding_pack is None
    # This must be a real ERROR status a caller can branch on -- not an OK
    # status with an empty items list a caller could mistake for "checked,
    # nothing applies".
    assert result.diagnostics.status != RetrievalStatus.OK
