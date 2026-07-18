"""Phase 2 section 10/17: GroundingPack must be produced by a REAL
retrieval run (not hand-constructed), pinned with a content_hash, and its
items must carry a real source_locator -- never a fabricated page number
(this repo's KnowledgeChunk has no page field, see
app/knowledge/retrieval_contracts.py SourceLocator docstring)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.knowledge.index import LocalEmbedding
from app.knowledge.legal_service import LegalKnowledgeService
from app.knowledge.retrieval_contracts import AgentType, RetrievalRequest, SourceLocatorType
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator


def _request() -> RetrievalRequest:
    return RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="LegalExpert",
        agent_type=AgentType.LEGAL_POLICY, task_type="legal_search",
        raw_query="UBO", normalized_query="UBO xac minh",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-legal-v1",
    )


def test_grounding_pack_items_use_structured_field_or_document_span_never_a_fabricated_page(tmp_path):
    svc = LegalKnowledgeService(index_path=tmp_path / "legal.sqlite3")
    svc.ensure_index()
    result = ControlledRetrievalOrchestrator(svc.index).retrieve(_request())
    assert result.grounding_pack is not None
    for item in result.grounding_pack.items:
        assert item.source_locator.type == SourceLocatorType.DOCUMENT_SPAN
        assert item.source_locator.section is not None
        # No "page" attribute exists on SourceLocator at all -- structurally
        # impossible to fabricate one.
        assert not hasattr(item.source_locator, "page")


def test_grounding_pack_is_deterministic_for_the_same_retrieval(tmp_path):
    svc = LegalKnowledgeService(index_path=tmp_path / "legal.sqlite3")
    svc.ensure_index()
    orchestrator = ControlledRetrievalOrchestrator(svc.index)
    first = orchestrator.retrieve(_request())
    second = orchestrator.retrieve(_request())
    assert first.grounding_pack.content_hash == second.grounding_pack.content_hash


def test_grounding_pack_request_ref_points_at_the_originating_request(tmp_path):
    svc = LegalKnowledgeService(index_path=tmp_path / "legal.sqlite3")
    svc.ensure_index()
    result = ControlledRetrievalOrchestrator(svc.index).retrieve(_request())
    assert result.grounding_pack.request_ref.entity_id == "r1"
    assert result.grounding_pack.request_ref.entity_type == "retrieval_request"


def test_grounding_pack_agent_type_matches_the_request(tmp_path):
    svc = LegalKnowledgeService(index_path=tmp_path / "legal.sqlite3")
    svc.ensure_index()
    result = ControlledRetrievalOrchestrator(svc.index).retrieve(_request())
    assert result.grounding_pack.agent_type == AgentType.LEGAL_POLICY
