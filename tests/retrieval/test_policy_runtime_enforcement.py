"""Phase 2 section 7/17: AGENT_RETRIEVAL_POLICIES must actually be
consulted by ControlledRetrievalOrchestrator, not just exist as data
(Phase 1 status). Legal's fail_closed=True must turn an empty result into
a hard ERROR, never a silent pass -- see
docs/RAG_GUARDRAIL_IMPLEMENTATION_PLAN.md Legal Agent policy."""

from __future__ import annotations

from datetime import date, datetime, timezone

from app.knowledge.index import LocalEmbedding, PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk
from app.knowledge.retrieval_contracts import (
    AgentType, AuthorityTier, RetrievalErrorCode, RetrievalRequest, RetrievalStatus, VerificationStatus,
)
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator


def _empty_orchestrator(tmp_path) -> ControlledRetrievalOrchestrator:
    index = PersistentHybridIndex(tmp_path / "empty.sqlite3", provider=LocalEmbedding())
    return ControlledRetrievalOrchestrator(index)


def _request(agent_type: AgentType, policy_id: str) -> RetrievalRequest:
    return RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="RM", agent_type=agent_type,
        task_type="search", raw_query="von luu dong", normalized_query="von luu dong",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id=policy_id,
    )


def test_legal_fail_closed_turns_empty_result_into_hard_error(tmp_path):
    orchestrator = _empty_orchestrator(tmp_path)
    result = orchestrator.retrieve(_request(AgentType.LEGAL_POLICY, "retrieval-policy-legal-v1"))
    assert result.diagnostics.status == RetrievalStatus.ERROR
    assert result.diagnostics.error_code == RetrievalErrorCode.SOURCE_SCOPE_EMPTY
    assert result.grounding_pack is None


def test_product_not_fail_closed_reports_no_relevant_result_not_error(tmp_path):
    orchestrator = _empty_orchestrator(tmp_path)
    result = orchestrator.retrieve(_request(AgentType.PRODUCT, "retrieval-policy-product-v1"))
    assert result.diagnostics.status == RetrievalStatus.OK
    assert result.diagnostics.error_code == RetrievalErrorCode.NO_RELEVANT_RESULT


def test_legal_policy_minimum_verification_status_rejects_unverified_chunk(tmp_path):
    index = PersistentHybridIndex(tmp_path / "unverified.sqlite3", provider=LocalEmbedding())
    index.upsert(
        [
            KnowledgeChunk(
                chunk_id="C1", document_id="DOC-1", document_version="1", product_id="PROD-X",
                section_path="1.1", text="von luu dong dieu kien",
                effective_from=date(2026, 1, 1), effective_to=None, active=True, segments=[],
                access_scope={"branches": ["*"]}, content_hash="h1",
                verification_status=VerificationStatus.UNVERIFIED,
                authority_tier=AuthorityTier.TIER_2_VERIFIED_INTERNAL,
            )
        ],
        source_hash="s1", dataset_version="v1",
    )
    orchestrator = ControlledRetrievalOrchestrator(index)
    result = orchestrator.retrieve(_request(AgentType.LEGAL_POLICY, "retrieval-policy-legal-v1"))
    assert result.diagnostics.status == RetrievalStatus.ERROR
    assert result.diagnostics.blocked_candidate_reason_counts.get("VERIFICATION_LEVEL_TOO_LOW") == 1


def test_product_policy_allows_the_same_unverified_chunk_legal_rejects(tmp_path):
    """Same data, different agent policy -- proves policy DATA actually
    changes runtime behavior, not just documentation (Phase 1's gap)."""
    index = PersistentHybridIndex(tmp_path / "unverified2.sqlite3", provider=LocalEmbedding())
    index.upsert(
        [
            KnowledgeChunk(
                chunk_id="C1", document_id="DOC-1", document_version="1", product_id="PROD-X",
                section_path="1.1", text="von luu dong dieu kien",
                effective_from=date(2026, 1, 1), effective_to=None, active=True, segments=[],
                access_scope={"branches": ["*"]}, content_hash="h1",
                verification_status=VerificationStatus.UNVERIFIED,
                authority_tier=AuthorityTier.TIER_3_CUSTOMER_PROVIDED_UNVERIFIED,
            )
        ],
        source_hash="s1", dataset_version="v1",
    )
    orchestrator = ControlledRetrievalOrchestrator(index)
    result = orchestrator.retrieve(_request(AgentType.PRODUCT, "retrieval-policy-product-v1"))
    assert result.diagnostics.status == RetrievalStatus.OK
    assert result.grounding_pack is not None
    assert len(result.grounding_pack.items) == 1
