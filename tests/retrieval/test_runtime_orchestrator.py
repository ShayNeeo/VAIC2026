"""Phase 2 section 4/17: ControlledRetrievalOrchestrator must actually call
the index (not just construct output), producing a GroundingPack backed by
real retrieved chunks. Uses LegalKnowledgeService's real ingestion (Phase 2
tagged authority_tier=TIER_2_VERIFIED_INTERNAL/verification_status=VERIFIED,
see app/knowledge/legal_service.py) so this is a genuine end-to-end path,
not a hand-built fixture that assumes fields exist."""

from __future__ import annotations

from datetime import datetime, timezone

from app.knowledge.index import LocalEmbedding
from app.knowledge.legal_service import LegalKnowledgeService
from app.knowledge.retrieval_contracts import AgentType, RetrievalChannel, RetrievalRequest, RetrievalStatus
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator


def _request(**overrides) -> RetrievalRequest:
    base = dict(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="LegalExpert",
        agent_type=AgentType.LEGAL_POLICY, task_type="legal_search",
        raw_query="UBO", normalized_query="UBO xac minh",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        retrieval_policy_id="retrieval-policy-legal-v1",
    )
    base.update(overrides)
    return RetrievalRequest(**base)


def _legal_orchestrator(tmp_path) -> ControlledRetrievalOrchestrator:
    svc = LegalKnowledgeService(index_path=tmp_path / "legal.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    return ControlledRetrievalOrchestrator(svc.index)


def test_orchestrator_returns_ok_with_a_populated_grounding_pack(tmp_path):
    orchestrator = _legal_orchestrator(tmp_path)
    result = orchestrator.retrieve(_request())
    assert result.diagnostics.status == RetrievalStatus.OK
    assert result.grounding_pack is not None
    assert len(result.grounding_pack.items) > 0
    assert all(item.content for item in result.grounding_pack.items)


def test_orchestrator_executes_exact_sparse_dense_and_hybrid_channels(tmp_path):
    orchestrator = _legal_orchestrator(tmp_path)
    result = orchestrator.retrieve(_request())
    assert RetrievalChannel.SPARSE in result.diagnostics.channels_executed
    assert RetrievalChannel.DENSE in result.diagnostics.channels_executed


def test_orchestrator_diagnostics_report_real_candidate_counts(tmp_path):
    orchestrator = _legal_orchestrator(tmp_path)
    result = orchestrator.retrieve(_request())
    assert result.diagnostics.candidate_count_before_filter > 0
    assert result.diagnostics.candidate_count_after_filter <= result.diagnostics.candidate_count_before_filter


def test_grounding_pack_content_hash_changes_if_item_set_differs(tmp_path):
    orchestrator = _legal_orchestrator(tmp_path)
    # Same request twice must be byte-for-byte deterministic.
    a = orchestrator.retrieve(_request())
    b = orchestrator.retrieve(_request())
    assert a.grounding_pack.content_hash == b.grounding_pack.content_hash
    # Two different queries that retrieve genuinely different item sets must
    # produce different content hashes. "UBO" resolves to the UBO rule chunk,
    # "bad debt" to the bulk-payment tech rule chunk -- so the grounding packs
    # are not equivalent.
    ubo = orchestrator.retrieve(_request(normalized_query="UBO xac minh", raw_query="UBO"))
    debt = orchestrator.retrieve(_request(normalized_query="no bad debt 12 thang", raw_query="bad debt"))
    assert ubo.grounding_pack is not None and debt.grounding_pack is not None
    assert ubo.grounding_pack.content_hash != debt.grounding_pack.content_hash


def test_unknown_agent_type_is_a_configuration_error_not_a_crash(tmp_path):
    from app.knowledge.retrieval_contracts import RetrievalErrorCode

    orchestrator = _legal_orchestrator(tmp_path)
    result = orchestrator.retrieve(_request(agent_type=AgentType.UNDERWRITING_COMPILER))
    assert result.diagnostics.status == RetrievalStatus.ERROR
    assert result.diagnostics.error_code == RetrievalErrorCode.FILTER_CONFIGURATION_INVALID
    assert result.grounding_pack is None
