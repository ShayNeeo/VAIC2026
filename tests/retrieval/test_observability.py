"""Phase 5 section 48: observability events -- real event emission from
the orchestrator, no PII/secret fields in the logged payload."""

from __future__ import annotations

from datetime import datetime, timezone

from app.knowledge.index import LocalEmbedding, PersistentHybridIndex
from app.knowledge.legal_service import LegalKnowledgeService
from app.knowledge.observability import InMemoryObservabilityRecorder
from app.knowledge.retrieval_contracts import AgentType, RetrievalRequest
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator


def test_orchestrator_emits_one_event_per_retrieve_call(tmp_path):
    svc = LegalKnowledgeService(index_path=tmp_path / "legal.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    recorder = InMemoryObservabilityRecorder()
    orchestrator = ControlledRetrievalOrchestrator(svc.index)
    request = RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="LegalExpert",
        agent_type=AgentType.LEGAL_POLICY, task_type="legal_search",
        raw_query="UBO", normalized_query="UBO xac minh",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-legal-v1",
    )
    orchestrator.retrieve(request, observer=recorder)
    assert len(recorder.events) == 1
    event = recorder.events[0]
    assert event.trace_id == "t1"
    assert event.agent_type == "legal_policy"
    assert event.latency_ms is not None
    assert len(event.selected_chunk_ids) > 0


def test_event_log_dict_never_includes_raw_query_or_chunk_content(tmp_path):
    svc = LegalKnowledgeService(index_path=tmp_path / "legal.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    recorder = InMemoryObservabilityRecorder()
    orchestrator = ControlledRetrievalOrchestrator(svc.index)
    request = RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="LegalExpert",
        agent_type=AgentType.LEGAL_POLICY, task_type="legal_search",
        raw_query="UBO", normalized_query="UBO xac minh",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-legal-v1",
    )
    orchestrator.retrieve(request, observer=recorder)
    log_dict = recorder.events[0].to_log_dict()
    assert "raw_query" not in log_dict
    assert "content" not in log_dict
    assert "quote" not in log_dict


def test_error_events_are_countable_by_error_code(tmp_path):
    empty_index = PersistentHybridIndex(tmp_path / "empty.sqlite3", provider=LocalEmbedding())
    recorder = InMemoryObservabilityRecorder()
    orchestrator = ControlledRetrievalOrchestrator(empty_index)
    request = RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="LegalExpert",
        agent_type=AgentType.LEGAL_POLICY, task_type="legal_search",
        raw_query="UBO", normalized_query="UBO xac minh",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-legal-v1",
    )
    orchestrator.retrieve(request, observer=recorder)
    counts = recorder.count_by_error_code()
    assert counts.get("source_scope_empty") == 1


def test_no_observer_means_no_event_recording_overhead(tmp_path):
    """observer=None (the default) must not raise or require any observer
    -- backward compatible with every Phase 2/3 call site that never
    passes it."""
    svc = LegalKnowledgeService(index_path=tmp_path / "legal.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    orchestrator = ControlledRetrievalOrchestrator(svc.index)
    request = RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="LegalExpert",
        agent_type=AgentType.LEGAL_POLICY, task_type="legal_search",
        raw_query="UBO", normalized_query="UBO xac minh",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-legal-v1",
    )
    result = orchestrator.retrieve(request)
    assert result.diagnostics.status.value == "ok"
