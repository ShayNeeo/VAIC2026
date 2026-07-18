"""Phase 1 section 8: per-agent retrieval policy data. This tests the
POLICY DATA is correct and internally consistent with
docs/RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md section 2 (Doc B mục 30's
per-agent source table) -- runtime enforcement (a retrieval call actually
consulting this registry) is NOT_RUNTIME_WIRED, see
app/knowledge/agent_retrieval_policies.py module docstring."""

from __future__ import annotations

from app.knowledge.agent_retrieval_policies import (
    AGENT_RETRIEVAL_POLICIES,
    LEGAL_POLICY_RETRIEVAL_POLICY,
    OPERATIONS_RETRIEVAL_POLICY,
    PRODUCT_RETRIEVAL_POLICY,
)
from app.knowledge.retrieval_contracts import AgentType


def test_all_three_agents_have_a_registered_policy():
    assert set(AGENT_RETRIEVAL_POLICIES.keys()) == {AgentType.PRODUCT, AgentType.LEGAL_POLICY, AgentType.OPERATIONS}


def test_legal_policy_is_fail_closed_and_exact_lookup_first():
    """docs/RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md section 2: Legal
    "Không được tự suy đoán: Kết luận pháp lý không policy" -- fail_closed
    must be True, unlike Product/Operations."""
    assert LEGAL_POLICY_RETRIEVAL_POLICY.fail_closed is True
    assert LEGAL_POLICY_RETRIEVAL_POLICY.exact_lookup_first is True


def test_legal_policy_never_allows_unverified_customer_data_as_a_source():
    assert LEGAL_POLICY_RETRIEVAL_POLICY.allow_customer_unverified_data is False


def test_product_policy_allows_unverified_customer_data_labelled_clearly():
    """docs/RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md section 2: Product's
    allowed sources explicitly include customer-provided facts (not just
    the controlled catalog) -- unlike Legal."""
    assert PRODUCT_RETRIEVAL_POLICY.allow_customer_unverified_data is True


def test_no_agent_policy_allows_model_inference_as_a_source():
    """None of the three agents are allowed to retrieve "model inference"
    as if it were a real source -- see forbidden-claim lists in
    docs/RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md section 2."""
    for policy in AGENT_RETRIEVAL_POLICIES.values():
        assert policy.allow_model_inference_sources is False


def test_operations_policy_only_allows_operations_domain_sources():
    assert set(OPERATIONS_RETRIEVAL_POLICY.allowed_source_types) == {
        "sop", "process_catalog", "operational_checklist", "readiness_evidence",
    }


def test_policy_ids_are_unique_across_agents():
    ids = [policy.policy_id for policy in AGENT_RETRIEVAL_POLICIES.values()]
    assert len(ids) == len(set(ids))
