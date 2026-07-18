"""Phase 4 section 40/41: abstention decisions composed from Phase 2/3
retrieval + claim-validation outcomes, not a new source of truth."""

from __future__ import annotations

from datetime import datetime, timezone

from app.knowledge.index import LocalEmbedding
from app.knowledge.legal_service import LegalKnowledgeService
from app.knowledge.retrieval_contracts import AgentType, RetrievalRequest
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator
from app.safety.abstention import AbstentionReason, decide_from_claim, decide_from_retrieval
from app.safety.claim_evidence_validator import ClaimEvidenceResult, ClaimEvidenceStatus


def test_successful_retrieval_does_not_require_abstention(tmp_path):
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
    decision = decide_from_retrieval(result)
    assert decision.must_abstain is False


def test_legal_fail_closed_error_maps_to_policy_source_not_found(tmp_path):
    from app.knowledge.index import PersistentHybridIndex

    empty_index = PersistentHybridIndex(tmp_path / "empty.sqlite3", provider=LocalEmbedding())
    orchestrator = ControlledRetrievalOrchestrator(empty_index)
    request = RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="LegalExpert",
        agent_type=AgentType.LEGAL_POLICY, task_type="legal_search",
        raw_query="UBO", normalized_query="UBO xac minh",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-legal-v1",
    )
    result = orchestrator.retrieve(request)
    decision = decide_from_retrieval(result)
    assert decision.must_abstain is True
    assert decision.reason == AbstentionReason.POLICY_SOURCE_NOT_FOUND


def test_unsupported_claim_forces_abstention():
    claim = ClaimEvidenceResult("CLAIM-1", ClaimEvidenceStatus.UNSUPPORTED, "quote not found")
    decision = decide_from_claim(claim)
    assert decision.must_abstain is True
    assert decision.reason == AbstentionReason.INSUFFICIENT_EVIDENCE


def test_conflicted_claim_recommends_legal_specialist_review():
    claim = ClaimEvidenceResult("CLAIM-1", ClaimEvidenceStatus.CONFLICTED, "conflicting sources")
    decision = decide_from_claim(claim)
    assert decision.must_abstain is True
    assert decision.reason == AbstentionReason.CONFLICTING_SOURCES
    assert decision.recommended_reviewer == "Legal Specialist"


def test_supported_claim_does_not_require_abstention():
    claim = ClaimEvidenceResult("CLAIM-1", ClaimEvidenceStatus.SUPPORTED, "valid")
    decision = decide_from_claim(claim)
    assert decision.must_abstain is False
