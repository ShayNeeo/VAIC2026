"""Immutable expert identities and least-privilege tool policies."""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from app.agents.contracts import AgentManifest, AgentType


TOOL_POLICY_VERSION = "agent-tools-1.0.0"


PRODUCT_MANIFEST = AgentManifest(
    agent_type=AgentType.PRODUCT_EXPERT,
    objective="Tìm và xếp hạng sản phẩm doanh nghiệp có nguồn.",
    accepted_task_types=("product_discovery", "product_alternative"),
    allowed_tools=("product_search", "product_get_chunk", "product_list_sources"),
    forbidden_decisions=("eligibility_pass_fail", "legal_exception", "external_action"),
    fallback_policy="deterministic_product_service",
)

LEGAL_MANIFEST = AgentManifest(
    agent_type=AgentType.LEGAL_EXPERT,
    objective="Giải thích chính sách và phát hành constraint từ kết quả rule deterministic.",
    accepted_task_types=("legal_precheck", "eligibility_evaluation", "legal_clarification"),
    allowed_tools=("legal_search", "legal_get_chunk", "legal_list_sources", "eligibility_evaluate"),
    forbidden_decisions=("product_ranking", "hard_block_override", "external_action"),
    fallback_policy="deterministic_eligibility_engine",
)

CREDIT_MANIFEST = AgentManifest(
    agent_type=AgentType.CREDIT_EXPERT,
    objective="Phân tích nhu cầu vay, cấu trúc tín dụng và mức sẵn sàng hồ sơ mà không phê duyệt khoản vay.",
    accepted_task_types=("credit_precheck", "credit_structuring", "credit_gap_analysis"),
    allowed_tools=(
        "credit_search",
        "credit_get_chunk",
        "credit_list_sources",
        "credit_analyze_readiness",
    ),
    forbidden_decisions=("final_credit_approval", "legal_exception", "external_action"),
    fallback_policy="deterministic_credit_readiness_service",
)

INSURANCE_MANIFEST = AgentManifest(
    agent_type=AgentType.INSURANCE_EXPERT,
    objective="Đánh giá mức độ sẵn sàng về bảo hiểm (tài sản đảm bảo, hàng hóa vận chuyển) mà không phê duyệt hợp đồng bảo hiểm.",
    accepted_task_types=("insurance_precheck", "insurance_coverage_review"),
    allowed_tools=(
        "insurance_search",
        "insurance_get_chunk",
        "insurance_list_sources",
        "insurance_analyze_readiness",
    ),
    forbidden_decisions=("policy_binding", "premium_pricing", "external_action"),
    fallback_policy="deterministic_insurance_readiness_service",
)

COORDINATOR_MANIFEST = AgentManifest(
    agent_type=AgentType.PLANNER_COORDINATOR,
    objective="Điều phối task, assistance, convergence và synthesis theo constraint.",
    accepted_task_types=("plan", "coordinate", "synthesize"),
    allowed_tools=(),
    forbidden_decisions=("domain_fact_creation", "hard_block_override", "external_action"),
    max_tool_calls=0,
    fallback_policy="deterministic_synthesis_policy",
)

EVIDENCE_MANIFEST = AgentManifest(
    agent_type=AgentType.EVIDENCE_VALIDATOR,
    objective="Kiểm chứng exact chunk, hash, version và citation.",
    accepted_task_types=("verify_claim",),
    allowed_tools=("evidence_get_chunk", "evidence_verify_citation"),
    forbidden_decisions=("product_ranking", "eligibility_pass_fail", "external_action"),
    fallback_policy="deterministic_evidence_validator",
)

MANIFESTS: Mapping[AgentType, AgentManifest] = MappingProxyType(
    {
        manifest.agent_type: manifest
        for manifest in (
            PRODUCT_MANIFEST,
            LEGAL_MANIFEST,
            CREDIT_MANIFEST,
            INSURANCE_MANIFEST,
            COORDINATOR_MANIFEST,
            EVIDENCE_MANIFEST,
        )
    }
)


def manifest_for(agent_type: AgentType) -> AgentManifest:
    return MANIFESTS[agent_type]
