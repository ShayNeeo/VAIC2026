"""Phase 1 section 2: canonical retrieval Pydantic models construct and
validate correctly. These models are INTERFACE_ONLY (see
app/knowledge/retrieval_contracts.py module docstring) -- this test proves
the contract itself is well-formed, not that any runtime path uses it yet."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.knowledge.retrieval_contracts import (
    AgentType,
    AuthorityTier,
    MetadataRef,
    RetrievalCandidate,
    RetrievalChannel,
    RetrievalDiagnostics,
    RetrievalErrorCode,
    RetrievalRequest,
    RetrievalStatus,
    VerificationStatus,
)


def test_retrieval_request_requires_agent_type_and_query():
    request = RetrievalRequest(
        request_id="REQ-1", trace_id="TRACE-1", actor_id="RM-999", actor_role="relationship_manager",
        agent_type=AgentType.LEGAL_POLICY, task_type="check_eligibility",
        raw_query="kiểm tra UBO", normalized_query="kiem tra ubo",
        effective_at=datetime.now(timezone.utc), retrieval_policy_id="retrieval-policy-legal-v1",
    )
    assert request.agent_type == AgentType.LEGAL_POLICY
    assert request.tenant_id is None


def test_retrieval_request_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        RetrievalRequest(
            request_id="REQ-1", trace_id="TRACE-1", actor_id="RM-999", actor_role="relationship_manager",
            agent_type=AgentType.PRODUCT, task_type="find_product", raw_query="q", normalized_query="q",
            effective_at=datetime.now(timezone.utc), retrieval_policy_id="p",
            not_a_real_field="should be rejected",
        )


def test_retrieval_candidate_carries_full_provenance():
    candidate = RetrievalCandidate(
        candidate_id="CAND-1", source_id="SYNTH-DOC-1", source_version="1", chunk_id="CHUNK-1",
        entity_type="product_policy", content="text", content_hash="hash",
        source_type="product_policy", authority_tier=AuthorityTier.TIER_1_AUTHORITATIVE,
        verification_status=VerificationStatus.VERIFIED,
        retrieval_channel=RetrievalChannel.SPARSE, representation_type="HASH_BOW_VECTOR",
        raw_score=0.8, rank=1,
    )
    assert candidate.is_superseded is False
    assert candidate.is_quarantined is False


def test_metadata_ref_is_minimal_typed_pointer():
    ref = MetadataRef(entity_type="product", entity_id="SYNTH-PROD-PAYROLL")
    assert ref.version is None


def test_retrieval_diagnostics_distinguishes_error_vs_ok():
    ok = RetrievalDiagnostics(
        status=RetrievalStatus.OK, strategy="hybrid", candidate_count_before_filter=10,
        candidate_count_after_filter=3, latency_ms=12,
    )
    assert ok.error_code is None

    error = RetrievalDiagnostics(
        status=RetrievalStatus.ERROR, error_code=RetrievalErrorCode.PROVIDER_UNAVAILABLE,
        strategy="hybrid", candidate_count_before_filter=0, candidate_count_after_filter=0, latency_ms=3000,
    )
    assert error.error_code == RetrievalErrorCode.PROVIDER_UNAVAILABLE


def test_retrieval_error_code_keeps_phase_0_codes():
    """Phase 1 section 3: "Giữ các code Phase 0" -- the pipeline-level
    error taxonomy must be a superset, not a replacement, of the
    index-level codes app.knowledge.index.RetrievalOutcomeCode already
    ships with real tests for."""
    assert RetrievalErrorCode.NO_RELEVANT_RESULT.value == "no_relevant_result"
    assert RetrievalErrorCode.INDEX_NOT_READY.value == "index_not_ready"
    assert RetrievalErrorCode.EMPTY_QUERY.value == "empty_query"
