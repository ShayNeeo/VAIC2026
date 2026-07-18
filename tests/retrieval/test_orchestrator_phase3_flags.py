"""Phase 3 feature-flag wiring on ControlledRetrievalOrchestrator.

test_reranker_and_mmr_together_still_surface_the_single_correct_answer is
a regression test for a real bug found via manual E2E verification: MMR
was rebuilding RerankedCandidate wrappers from the stale pre-rerank
fused_score instead of reusing the reranker's actual rerank_score, which
silently undid the reranker's improvement and (combined with a since-
removed conflict-based MMR-protection mechanism) pushed the single
correct answer for a real "UBO" query out of the top 5 entirely. See
app/knowledge/retrieval_orchestrator.py's inline comments for the full
root-cause writeup and docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md's
Phase 3 section."""

from __future__ import annotations

from datetime import datetime, timezone

from app.knowledge.index import LocalEmbedding
from app.knowledge.legal_service import LegalKnowledgeService
from app.knowledge.reranker import RerankerMode
from app.knowledge.retrieval_contracts import AgentType, RetrievalRequest
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator


def _ubo_request() -> RetrievalRequest:
    return RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="LegalExpert",
        agent_type=AgentType.LEGAL_POLICY, task_type="legal_search",
        raw_query="UBO", normalized_query="UBO xac minh",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-legal-v1",
    )


def _legal_orchestrator(tmp_path) -> ControlledRetrievalOrchestrator:
    svc = LegalKnowledgeService(index_path=tmp_path / "legal.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    return ControlledRetrievalOrchestrator(svc.index)


def test_all_flags_off_matches_phase_2_baseline_behavior(tmp_path):
    orchestrator = _legal_orchestrator(tmp_path)
    result = orchestrator.retrieve(_ubo_request())
    assert result.grounding_pack.items[0].chunk_id.startswith("RULE-CREDIT-UBO-001")


def test_reranker_and_mmr_together_still_surface_the_single_correct_answer(tmp_path):
    orchestrator = _legal_orchestrator(tmp_path)
    result = orchestrator.retrieve(
        _ubo_request(), query_expansion_enabled=True, reranker_mode=RerankerMode.HEURISTIC, mmr_enabled=True,
    )
    chunk_ids = [item.chunk_id for item in result.grounding_pack.items]
    assert any(cid.startswith("RULE-CREDIT-UBO-001") for cid in chunk_ids)
    assert chunk_ids[0].startswith("RULE-CREDIT-UBO-001")


def test_cross_encoder_mode_raises_not_implemented(tmp_path):
    orchestrator = _legal_orchestrator(tmp_path)
    try:
        orchestrator.retrieve(_ubo_request(), reranker_mode=RerankerMode.CROSS_ENCODER)
        assert False, "expected NotImplementedError"
    except NotImplementedError:
        pass


def test_query_expansion_alone_does_not_change_the_top_result_for_this_query(tmp_path):
    orchestrator = _legal_orchestrator(tmp_path)
    result = orchestrator.retrieve(_ubo_request(), query_expansion_enabled=True)
    assert result.grounding_pack.items[0].chunk_id.startswith("RULE-CREDIT-UBO-001")
