"""Phase 2 section 18 hard gate: superseded_source_used_as_current = 0. A
superseded (is_superseded=True) legal rule must never be used as the
current answer -- even when a NEWER, non-superseded chunk for the same
slot exists and IS retrievable."""

from __future__ import annotations

from datetime import date, datetime, timezone

from app.knowledge.index import LocalEmbedding, PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk
from app.knowledge.retrieval_contracts import (
    AgentType, AuthorityTier, RetrievalRequest, RetrievalStatus, VerificationStatus,
)
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator


def test_superseded_rule_is_excluded_while_its_replacement_is_retrieved(tmp_path):
    index = PersistentHybridIndex(tmp_path / "supersede.sqlite3", provider=LocalEmbedding())
    index.upsert(
        [
            KnowledgeChunk(
                chunk_id="RULE-UBO-001:v1", document_id="DOC-1", document_version="1.0",
                product_id="PROD-WORKING-CAPITAL", section_path="4.2",
                text="quy dinh xac minh chu so huu huong loi UBO cu",
                effective_from=date(2025, 1, 1), effective_to=None, active=True, segments=[],
                access_scope={"branches": ["*"]}, content_hash="h-old", is_superseded=True,
                authority_tier=AuthorityTier.TIER_2_VERIFIED_INTERNAL, verification_status=VerificationStatus.VERIFIED,
            ),
            KnowledgeChunk(
                chunk_id="RULE-UBO-001:v2", document_id="DOC-1", document_version="2.0",
                product_id="PROD-WORKING-CAPITAL", section_path="4.2",
                text="quy dinh xac minh chu so huu huong loi UBO moi nhat",
                effective_from=date(2026, 1, 1), effective_to=None, active=True, segments=[],
                access_scope={"branches": ["*"]}, content_hash="h-new", is_superseded=False,
                authority_tier=AuthorityTier.TIER_2_VERIFIED_INTERNAL, verification_status=VerificationStatus.VERIFIED,
            ),
        ],
        source_hash="s1", dataset_version="v1",
    )
    orchestrator = ControlledRetrievalOrchestrator(index)
    request = RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="LegalExpert",
        agent_type=AgentType.LEGAL_POLICY, task_type="legal_search",
        raw_query="UBO", normalized_query="xac minh chu so huu huong loi UBO",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-legal-v1",
    )
    result = orchestrator.retrieve(request)
    assert result.diagnostics.status == RetrievalStatus.OK
    assert result.grounding_pack is not None
    chunk_ids = {item.chunk_id for item in result.grounding_pack.items}
    assert "RULE-UBO-001:v2" in chunk_ids
    assert "RULE-UBO-001:v1" not in chunk_ids
    assert result.diagnostics.blocked_candidate_reason_counts.get("SOURCE_SUPERSEDED") == 1
