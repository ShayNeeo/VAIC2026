"""Concrete per-agent RetrievalPolicy instances -- RAG & Guardrail
Implementation Plan Phase 1 section 8, sourced from
docs/RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md section 2 (Doc B mục 30's
per-agent source table, the most specific source available for this
repo -- not the generic prompt list).

These are DATA, asserted by tests/retrieval/test_agent_retrieval_policy.py.
Runtime ENFORCEMENT (a retrieval call actually consulting this registry
before deciding what to search) is NOT_RUNTIME_WIRED yet -- see the
implementation report.
"""

from __future__ import annotations

from app.knowledge.retrieval_contracts import AgentType, AuthorityTier, RetrievalPolicy, VerificationStatus

PRODUCT_RETRIEVAL_POLICY = RetrievalPolicy(
    policy_id="retrieval-policy-product-v1",
    version="1.0.0",
    agent_type=AgentType.PRODUCT,
    allowed_source_types=["product_catalog", "product_policy", "customer_facts", "verified_evidence"],
    minimum_authority_tier=AuthorityTier.TIER_3_CUSTOMER_PROVIDED_UNVERIFIED,
    minimum_verification_status=VerificationStatus.UNVERIFIED,
    exact_lookup_first=True,
    fail_closed=False,
    allow_customer_unverified_data=True,
    allow_model_inference_sources=False,
    required_filters=["effective_at", "is_superseded", "product_ids"],
    maximum_candidates=30,
    sparse_weight=0.9,
    dense_weight=1.1,
)

LEGAL_POLICY_RETRIEVAL_POLICY = RetrievalPolicy(
    policy_id="retrieval-policy-legal-v1",
    version="1.0.0",
    agent_type=AgentType.LEGAL_POLICY,
    allowed_source_types=["policy_registry", "eligibility_rule", "kyc_ubo_evidence", "legal_document", "exception_record"],
    minimum_authority_tier=AuthorityTier.TIER_2_VERIFIED_INTERNAL,
    minimum_verification_status=VerificationStatus.VERIFIED,
    exact_lookup_first=True,
    fail_closed=True,
    allow_customer_unverified_data=False,
    allow_model_inference_sources=False,
    required_filters=["effective_at", "is_superseded", "is_quarantined", "policy_ids"],
    maximum_candidates=20,
    sparse_weight=1.3,
    dense_weight=0.7,
)

OPERATIONS_RETRIEVAL_POLICY = RetrievalPolicy(
    policy_id="retrieval-policy-operations-v1",
    version="1.0.0",
    agent_type=AgentType.OPERATIONS,
    allowed_source_types=["sop", "process_catalog", "operational_checklist", "readiness_evidence"],
    minimum_authority_tier=AuthorityTier.TIER_2_VERIFIED_INTERNAL,
    minimum_verification_status=VerificationStatus.VERIFIED,
    exact_lookup_first=True,
    fail_closed=False,
    allow_customer_unverified_data=False,
    allow_model_inference_sources=False,
    required_filters=["effective_at", "process_ids"],
    maximum_candidates=20,
)

AGENT_RETRIEVAL_POLICIES = {
    AgentType.PRODUCT: PRODUCT_RETRIEVAL_POLICY,
    AgentType.LEGAL_POLICY: LEGAL_POLICY_RETRIEVAL_POLICY,
    AgentType.OPERATIONS: OPERATIONS_RETRIEVAL_POLICY,
}
