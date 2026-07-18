"""Phase 2 E2E: Legal Agent through ControlledRetrievalOrchestrator, using
the REAL LegalKnowledgeService ingestion path (data/synthetic/v2/
eligibility_rules.json), not a hand-built fixture. Proves the whole chain
-- policy resolution, exact/sparse/dense/RRF, security filtering,
GroundingPack, claim validation -- works end-to-end against real data."""

from __future__ import annotations

from datetime import datetime, timezone

from app.knowledge.index import LocalEmbedding
from app.knowledge.legal_service import LegalKnowledgeService
from app.knowledge.retrieval_contracts import AgentType, RetrievalRequest, RetrievalStatus
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator
from app.safety.claim_evidence_validator import ClaimEvidenceStatus, validate_claim_against_pack


def test_legal_agent_retrieves_grounded_ubo_rule_and_claim_validates_as_supported(tmp_path):
    svc = LegalKnowledgeService(index_path=tmp_path / "legal.sqlite3", provider=LocalEmbedding())
    svc.ensure_index()
    orchestrator = ControlledRetrievalOrchestrator(svc.index)
    request = RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="LegalExpert",
        agent_type=AgentType.LEGAL_POLICY, task_type="legal_search",
        raw_query="UBO", normalized_query="UBO xac minh chu so huu huong loi",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-legal-v1",
    )
    result = orchestrator.retrieve(request)
    assert result.diagnostics.status == RetrievalStatus.OK
    assert result.grounding_pack is not None
    ubo_item = next((i for i in result.grounding_pack.items if "UBO" in i.chunk_id), None)
    assert ubo_item is not None, "expected the UBO rule chunk to be retrieved"

    # A quote genuinely present in the retrieved chunk's content must
    # validate as SUPPORTED via the whole claim-evidence chain.
    quote = ubo_item.content.split("Nội dung nguồn: ")[-1]
    claim = validate_claim_against_pack(
        claim_id="CLAIM-UBO-1", chunk_id=ubo_item.chunk_id, quote=quote,
        pinned_pack=result.grounding_pack, index=svc.index,
    )
    assert claim.status == ClaimEvidenceStatus.SUPPORTED
    assert claim.usable_for_readiness_or_approval is True
