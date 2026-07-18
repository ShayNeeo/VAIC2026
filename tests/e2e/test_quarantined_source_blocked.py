"""Phase 2 section 18 hard gate: quarantined_source_selected = 0. A
quarantined chunk must never appear in an orchestrator GroundingPack, even
when it is the single best textual/semantic match for the query."""

from __future__ import annotations

from datetime import date, datetime, timezone

from app.knowledge.index import LocalEmbedding, PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk
from app.knowledge.retrieval_contracts import AgentType, RetrievalRequest, RetrievalStatus
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator


def test_quarantined_chunk_never_appears_in_the_grounding_pack(tmp_path):
    index = PersistentHybridIndex(tmp_path / "quar.sqlite3", provider=LocalEmbedding())
    index.upsert(
        [
            KnowledgeChunk(
                chunk_id="C1", document_id="DOC-1", document_version="1", product_id="SYNTH-PROD-PAYROLL",
                section_path="1.1", text="dich vu chi luong nhan su doanh nghiep chi tiet",
                effective_from=date(2026, 1, 1), effective_to=None, active=True, segments=[],
                access_scope={"branches": ["*"]}, content_hash="h1", is_quarantined=True,
            )
        ],
        source_hash="s1", dataset_version="v1",
    )
    orchestrator = ControlledRetrievalOrchestrator(index)
    request = RetrievalRequest(
        request_id="r1", trace_id="t1", actor_id="u1", actor_role="RM", agent_type=AgentType.PRODUCT,
        task_type="product_search", raw_query="chi luong", normalized_query="dich vu chi luong nhan su",
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id="retrieval-policy-product-v1",
    )
    result = orchestrator.retrieve(request)
    assert result.diagnostics.status == RetrievalStatus.OK
    assert result.grounding_pack is None
    assert result.diagnostics.blocked_candidate_reason_counts.get("SOURCE_QUARANTINED") == 1
