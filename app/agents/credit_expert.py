"""Credit Expert that builds an auditable credit memo analysis."""

from __future__ import annotations

import uuid
from time import perf_counter
from typing import Any, Dict, List, Optional

from app.agents.base import BaseExpertRuntime
from app.agents.contracts import ConfidenceBreakdown, EvidenceReference, StopReason, SupportStatus, TaskAssignment
from app.agents.finding_factory import build_finding, validate_assignment
from app.agents.manifests import CREDIT_MANIFEST
from app.credit.service import CreditReadinessService
from app.knowledge.credit_service import CreditKnowledgeService
from app.tools.agent_gateway import AgentToolGateway


class CreditExpertAgent(BaseExpertRuntime):
    manifest = CREDIT_MANIFEST

    def __init__(
        self,
        service: Optional[CreditReadinessService] = None,
        knowledge: Optional[CreditKnowledgeService] = None,
    ) -> None:
        super().__init__()
        self.service = service or CreditReadinessService()
        self.knowledge = knowledge or CreditKnowledgeService()
        self.gateway = AgentToolGateway(
            self.manifest,
            {
                "credit_analyze_readiness": self.service.analyze,
                "credit_search": self.knowledge.search,
                "credit_get_chunk": self.knowledge.index.exact_lookup_by_chunk_id,
                "credit_list_sources": self.knowledge.index.list_chunks,
            },
        )

    async def analyze(
        self,
        task: TaskAssignment,
        *,
        product_result: Dict[str, Any],
        eligibility_result: Dict[str, Any],
        customer_attributes: Dict[str, Any],
        documents: List[Dict[str, Any]],
        business_snapshot: Optional[Dict[str, Any]] = None,
        requested_amount: Optional[float] = None,
        requested_tenor_months: Optional[int] = None,
        loan_purpose: Optional[str] = None,
        branch: str = "*",
    ):
        validate_assignment(task, self.manifest)
        self.gateway.reset_trace()
        started = perf_counter()
        result = await self.gateway.call(
            "credit_analyze_readiness",
            product_result=product_result,
            eligibility_result=eligibility_result,
            customer_attributes=customer_attributes,
            documents=documents,
            business_snapshot=business_snapshot or {},
            requested_amount=requested_amount,
            requested_tenor_months=requested_tenor_months,
            loan_purpose=loan_purpose,
        )
        evidence_refs: List[EvidenceReference] = []
        credit_ids = list(result.get("credit_product_ids", []))
        retrieval_fallback_reason: Optional[str] = None
        if credit_ids:
            try:
                hits = await self.gateway.call(
                    "credit_search",
                    query="phân tích tín dụng vốn lưu động, nguồn trả nợ, hồ sơ tài chính và tài sản bảo đảm",
                    branch=branch,
                    product_id=credit_ids[0],
                    top_k=3,
                )
            except Exception as exc:
                retrieval_fallback_reason = f"credit_retrieval_{type(exc).__name__}"
                hits = []
            for hit in hits:
                evidence_refs.append(
                    EvidenceReference(
                        claim_id=f"CREDIT-{hit.chunk.chunk_id}",
                        chunk_id=hit.chunk.chunk_id,
                        document_id=hit.chunk.document_id,
                        document_version=hit.chunk.document_version,
                        content_hash=hit.chunk.content_hash,
                        location=hit.chunk.section_path,
                        quote=hit.chunk.text,
                        support_status=SupportStatus.SUPPORTED,
                    )
                )
        else:
            hits = []

        llm = await self._enrich(
            system_prompt=(
                "Bạn là chuyên gia tín dụng doanh nghiệp. Hãy viết credit memo ngắn từ các facts, ratios, hồ sơ, "
                "hard blocks và information gaps được cung cấp. Phân tích mô hình kinh doanh, mục đích vay, nguồn trả "
                "nợ, khả năng trả nợ, lịch sử tín dụng và tài sản bảo đảm. Không tự tạo số liệu, không sửa Rule Engine, "
                "không đưa lãi suất/hạn mức phê duyệt và không kết luận phê duyệt khoản vay."
            ),
            payload={
                "credit_analysis": result,
                "source_refs": [
                    {"document_id": item.document_id, "version": item.document_version, "location": item.location}
                    for item in evidence_refs
                ],
                "output_contract": {
                    "decision_rationale_summary": ["string"],
                    "inferences": [{"statement": "string", "basis": ["field_or_indicator"]}],
                    "unknowns": [{"field": "string", "impact": "string", "next_evidence": "string"}],
                    "credit_officer_focus": [{"topic": "string", "why": "string"}],
                },
            },
        )
        rationale = []
        inferences = []
        unknowns = [
            {
                "field": field,
                "impact": "Giới hạn độ sâu hoặc độ tin cậy của phân tích tín dụng.",
                "next_evidence": field,
            }
            for field in result.get("missing_information", [])
        ]
        recommendations = list(result.get("structure_scenarios", []))
        if isinstance(llm, dict):
            if isinstance(llm.get("decision_rationale_summary"), list):
                rationale = [str(item) for item in llm["decision_rationale_summary"][:8] if str(item).strip()]
            if isinstance(llm.get("inferences"), list):
                inferences = [item for item in llm["inferences"][:8] if isinstance(item, dict)]
            if isinstance(llm.get("unknowns"), list):
                unknowns.extend(item for item in llm["unknowns"][:8] if isinstance(item, dict))
            if isinstance(llm.get("credit_officer_focus"), list):
                recommendations.extend(item for item in llm["credit_officer_focus"][:8] if isinstance(item, dict))
        if not rationale:
            rationale = [
                str(result.get("conclusion")),
                f"Đã đánh giá {len(result.get('analysis_dimensions', []))} chiều bối cảnh và hồ sơ khách hàng.",
                "Mọi tỷ số chỉ là chỉ báo mô tả; thẩm quyền quyết định thuộc cán bộ tín dụng và approval workflow.",
            ]
        status = str(result.get("status"))
        stop_reason = (
            StopReason.HARD_BLOCK
            if status == "hard_block_detected"
            else StopReason.INSUFFICIENT_EVIDENCE
            if status == "needs_information"
            else StopReason.FALLBACK
            if self.last_fallback_reason
            else StopReason.COMPLETED
        )
        confidence_score = float((result.get("analysis_confidence") or {}).get("input_completeness", 0.0))
        return build_finding(
            manifest=self.manifest,
            task=task,
            finding_id=f"FND-CREDIT-{uuid.uuid4().hex[:10].upper()}",
            conclusion=str(result.get("conclusion")),
            rationale=rationale,
            known_facts=tuple(result.get("known_facts", []))
            + ({"capacity_indicators": result.get("capacity_indicators", {})},),
            inferences=inferences,
            unknowns=unknowns,
            assumptions=(),
            recommendations=recommendations,
            constraints=tuple(result.get("hard_blocks", [])),
            evidence_refs=evidence_refs,
            confidence=ConfidenceBreakdown(
                evidence_coverage=1.0 if evidence_refs else 0.0 if credit_ids else 1.0,
                source_authority="E_SYNTHETIC",
                freshness_status="current" if evidence_refs or not credit_ids else "unknown",
                retrieval_quality=max((float(hit.score) for hit in hits), default=None),
                consistency_status="consistent",
                rule_certainty="deterministic",
                input_completeness=confidence_score,
                display_confidence=round(min(1.0, 0.6 * confidence_score + (0.4 if evidence_refs else 0.0)), 4),
                calibration_policy_version="credit-confidence-v1",
            ),
            domain_result=result,
            stop_reason=stop_reason,
            model=self.model,
            prompt_version="credit-expert-structured-v1",
            tools_called=self.gateway.trace.called,
            denied_tools=self.gateway.trace.denied,
            latency_ms=int((perf_counter() - started) * 1000),
            fallback_reason=retrieval_fallback_reason or self.last_fallback_reason,
            revision=task.round or 1,
        )
