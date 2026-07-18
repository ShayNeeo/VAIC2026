"""Deterministic, constraint-aware synthesis for expert findings."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Iterable, List, Optional

from app.agents.contracts import ExpertFinding, SupportStatus, SynthesisResult, canonical_hash


SYNTHESIS_POLICY_VERSION = "constraint-aware-synthesis-1.0.0"

# Below this aggregate/min display_confidence, the Coordinator flags the
# output for human review. Advisory only -- app/workflow/risk_gate.py stays
# the sole deterministic gate for case status/approval routing; this never
# overrides it, it only tells the RM/specialist that AI confidence was low.
LOW_CONFIDENCE_THRESHOLD = 0.5


def _assess_findings_quality(
    findings: List[ExpertFinding],
) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Aggregate confidence/evidence-support signals across the independent
    Product/Credit/Insurance findings so the Coordinator actually evaluates
    output quality instead of just merging results untouched."""
    all_refs = [ref for finding in findings for ref in finding.evidence_refs]
    supported = [ref for ref in all_refs if ref.support_status == SupportStatus.SUPPORTED]
    confidences = [
        finding.confidence.display_confidence
        for finding in findings
        if finding.confidence.display_confidence is not None
    ]
    low_confidence_agents = [
        finding.agent_type.value
        for finding in findings
        if (finding.confidence.display_confidence or 1.0) < LOW_CONFIDENCE_THRESHOLD
    ]
    quality_summary = {
        "expert_evidence_ref_count": len(all_refs),
        "expert_evidence_supported_count": len(supported),
        "expert_evidence_supported_ratio": round(len(supported) / len(all_refs), 4) if all_refs else None,
        "aggregate_confidence": round(sum(confidences) / len(confidences), 4) if confidences else None,
        "min_confidence": round(min(confidences), 4) if confidences else None,
        "low_confidence_agents": low_confidence_agents,
    }
    conflicts = [
        {
            "agent_type": finding.agent_type.value,
            "finding_id": finding.finding_id,
            "reason": "consistency_status=conflicting",
        }
        for finding in findings
        if finding.confidence.consistency_status == "conflicting"
    ]
    return quality_summary, conflicts


def synthesize_expert_results(
    *,
    case_id: str,
    trace_id: str,
    product_result: Dict[str, Any],
    eligibility_result: Dict[str, Any],
    credit_result: Dict[str, Any],
    insurance_result: Optional[Dict[str, Any]] = None,
    alternative_product_result: Optional[Dict[str, Any]],
    alternative_eligibility_result: Optional[Dict[str, Any]],
    findings: Iterable[ExpertFinding],
) -> SynthesisResult:
    insurance_result = insurance_result or {}
    findings = list(findings)
    legal_by_product = {
        str(item.get("product_id")): item for item in eligibility_result.get("products", [])
    }
    blocked_ids = {
        product_id
        for product_id, item in legal_by_product.items()
        if str(item.get("status")) in {"failed", "pending_review"}
    }
    blocked: List[Dict[str, Any]] = []
    accepted: List[Dict[str, Any]] = []
    for candidate in product_result.get("recommendations", []):
        product_id = str(candidate.get("product_id"))
        legal = legal_by_product.get(product_id, {})
        if product_id in blocked_ids:
            blocked.append(
                {
                    **candidate,
                    "eligibility_status": legal.get("status"),
                    "block_reasons": [
                        {
                            "rule_id": rule.get("rule_id"),
                            "failure_code": rule.get("failure_code"),
                            "status": rule.get("status"),
                        }
                        for rule in legal.get("rules", [])
                        if rule.get("status") in {"failed", "pending_review"}
                    ],
                    "preserved_for_audit": True,
                }
            )
        elif str(legal.get("status", "passed")) == "passed":
            accepted.append({**candidate, "eligibility_status": "passed"})

    alternative_status = {
        str(item.get("product_id")): str(item.get("status"))
        for item in (alternative_eligibility_result or {}).get("products", [])
    }
    alternatives = [
        {**item, "eligibility_status": alternative_status.get(str(item.get("product_id")), "unknown")}
        for item in (alternative_product_result or {}).get("recommendations", [])
        if alternative_status.get(str(item.get("product_id")), "passed") == "passed"
    ][:2]

    missing: List[Dict[str, Any]] = []
    for product in eligibility_result.get("products", []):
        for field in product.get("missing_information", []):
            missing.append(
                {"field": field, "source": "EligibilityEngine", "product_id": product.get("product_id")}
            )
    for field in credit_result.get("missing_information", []):
        if not any(item["field"] == field for item in missing):
            missing.append({"field": field, "source": "CreditExpert", "product_id": None})
    for field in insurance_result.get("missing_information", []):
        if not any(item["field"] == field for item in missing):
            missing.append({"field": field, "source": "InsuranceExpert", "product_id": None})

    quality_summary, conflicts = _assess_findings_quality(findings)

    human_review = []
    if blocked:
        human_review.append(
            {
                "role": "Credit Specialist",
                "reason": "Hard block tín dụng/eligibility được giữ nguyên; phương án phi tín dụng không xóa quyết định này.",
                "required": True,
            }
        )
    if insurance_result.get("hard_blocks"):
        human_review.append(
            {
                "role": "Insurance Specialist",
                "reason": "Thiếu bảo hiểm bắt buộc theo chính sách cho sản phẩm có bảo đảm.",
                "required": True,
            }
        )
    if quality_summary["low_confidence_agents"]:
        human_review.append(
            {
                "role": "AI Quality Reviewer",
                "reason": (
                    f"Độ tin cậy đầu ra dưới ngưỡng {LOW_CONFIDENCE_THRESHOLD} từ: "
                    f"{', '.join(quality_summary['low_confidence_agents'])}. Không tự động chặn phê duyệt, "
                    "chỉ cảnh báo để RM/chuyên viên rà soát trước khi trình."
                ),
                "required": False,
            }
        )
    if conflicts:
        human_review.append(
            {
                "role": "AI Quality Reviewer",
                "reason": (
                    "Phát hiện kết luận mâu thuẫn (consistency_status=conflicting) giữa các Expert Agent "
                    "hoạt động độc lập; cần chuyên viên đối chiếu trước khi trình duyệt."
                ),
                "required": True,
            }
        )
    primary = accepted[0] if accepted else None
    body = {
        "primary_solution": primary,
        "alternative_solutions": alternatives,
        "blocked_candidates": blocked,
        "missing_information": missing,
        "human_review_requirements": human_review,
        "source_finding_ids": [item.finding_id for item in findings],
    }
    return SynthesisResult(
        synthesis_id=f"SYN-{uuid.uuid4().hex[:12].upper()}",
        case_id=case_id,
        trace_id=trace_id,
        primary_solution=primary,
        alternative_solutions=tuple(alternatives),
        blocked_candidates=tuple(blocked),
        unresolved_conflicts=tuple(conflicts),
        missing_information=tuple(missing),
        operations_plan=None,
        customer_draft=None,
        evidence_validation_summary={
            **quality_summary,
            "validation_status": "pending_workflow_evidence_gate",
        },
        human_review_requirements=tuple(human_review),
        source_finding_ids=tuple(item.finding_id for item in findings),
        synthesis_policy_version=SYNTHESIS_POLICY_VERSION,
        output_hash=canonical_hash(body),
    )

