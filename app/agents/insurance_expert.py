"""Independent Insurance Expert runtime -- mirrors app/agents/credit_expert.py's
structure. Reads only product_result + customer_attributes/business_snapshot;
never reads eligibility_result or credit_result, so it runs independently of
the other two experts (Product, Credit)."""

from __future__ import annotations

import uuid
from time import perf_counter
from typing import Any, Dict, List, Optional

from app.agents.base import BaseExpertRuntime
from app.agents.contracts import ConfidenceBreakdown, EvidenceReference, StopReason, SupportStatus, TaskAssignment
from app.agents.finding_factory import build_finding, validate_assignment
from app.agents.manifests import INSURANCE_MANIFEST
from app.insurance.service import InsuranceReadinessService
from app.knowledge.insurance_service import InsuranceKnowledgeService
from app.tools.agent_gateway import AgentToolGateway


class InsuranceExpertAgent(BaseExpertRuntime):
    manifest = INSURANCE_MANIFEST

    def __init__(
        self,
        service: Optional[InsuranceReadinessService] = None,
        knowledge: Optional[InsuranceKnowledgeService] = None,
    ) -> None:
        super().__init__()
        self.service = service or InsuranceReadinessService()
        self.knowledge = knowledge or InsuranceKnowledgeService()
        self.gateway = AgentToolGateway(
            self.manifest,
            {
                "insurance_analyze_readiness": self.service.analyze,
                "insurance_search": self.knowledge.search,
                "insurance_get_chunk": self.knowledge.index.exact_lookup_by_chunk_id,
                "insurance_list_sources": self.knowledge.index.list_chunks,
            },
        )

    async def analyze(
        self,
        task: TaskAssignment,
        *,
        product_result: Dict[str, Any],
        customer_attributes: Dict[str, Any],
        documents: List[Dict[str, Any]],
        business_snapshot: Optional[Dict[str, Any]] = None,
        branch: str = "*",
    ):
        validate_assignment(task, self.manifest)
        self.gateway.reset_trace()
        started = perf_counter()
        result = await self.gateway.call(
            "insurance_analyze_readiness",
            product_result=product_result,
            customer_attributes=customer_attributes,
            documents=documents,
            business_snapshot=business_snapshot or {},
        )

        evidence_refs: List[EvidenceReference] = []
        insurance_ids = list(result.get("insurance_product_ids", []))
        retrieval_fallback_reason: Optional[str] = None
        hits = []
        if insurance_ids or result.get("coverage_checks"):
            try:
                hits = await self.gateway.call(
                    "insurance_search",
                    query="yêu cầu bảo hiểm tài sản đảm bảo, hàng hóa vận chuyển và gián đoạn kinh doanh",
                    branch=branch,
                    product_id=insurance_ids[0] if insurance_ids else None,
                    top_k=3,
                )
            except Exception as exc:
                retrieval_fallback_reason = f"insurance_retrieval_{type(exc).__name__}"
                hits = []
            for hit in hits:
                evidence_refs.append(
                    EvidenceReference(
                        claim_id=f"INSURANCE-{hit.chunk.chunk_id}",
                        chunk_id=hit.chunk.chunk_id,
                        document_id=hit.chunk.document_id,
                        document_version=hit.chunk.document_version,
                        content_hash=hit.chunk.content_hash,
                        location=hit.chunk.section_path,
                        quote=hit.chunk.text,
                        support_status=SupportStatus.SUPPORTED,
                    )
                )

        llm = await self._enrich(
            system_prompt=(
                "Bạn là chuyên gia bảo hiểm doanh nghiệp. Diễn giải ngắn gọn coverage_checks và hard_blocks đã có; "
                "không tự tạo yêu cầu bảo hiểm mới, không xác nhận đã đủ điều kiện, không định giá phí bảo hiểm."
            ),
            payload={
                "insurance_analysis": result,
                "source_refs": [
                    {"document_id": item.document_id, "version": item.document_version, "location": item.location}
                    for item in evidence_refs
                ],
                "output_contract": {
                    "decision_rationale_summary": ["string"],
                    "unknowns": [{"field": "string", "impact": "string"}],
                },
            },
        )
        rationale: List[str] = []
        unknowns = [
            {"field": field, "impact": "Chưa xác nhận được yêu cầu bảo hiểm liên quan."}
            for field in result.get("missing_information", [])
        ]
        if isinstance(llm, dict):
            if isinstance(llm.get("decision_rationale_summary"), list):
                rationale = [str(item) for item in llm["decision_rationale_summary"][:8] if str(item).strip()]
            if isinstance(llm.get("unknowns"), list):
                unknowns.extend(item for item in llm["unknowns"][:8] if isinstance(item, dict))
        if not rationale:
            rationale = [
                str(result.get("conclusion")),
                f"Đã kiểm tra {len(result.get('coverage_checks', []))} yêu cầu bảo hiểm theo chính sách hiện hành.",
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
        coverage_present = sum(1 for item in result.get("coverage_checks", []) if item.get("status") == "present")
        coverage_total = len(result.get("coverage_checks", [])) or 1
        return build_finding(
            manifest=self.manifest,
            task=task,
            finding_id=f"FND-INSURANCE-{uuid.uuid4().hex[:10].upper()}",
            conclusion=str(result.get("conclusion")),
            rationale=rationale,
            known_facts=tuple(result.get("known_facts", [])),
            inferences=(),
            unknowns=unknowns,
            assumptions=(),
            recommendations=(),
            constraints=tuple(result.get("hard_blocks", [])) + tuple(result.get("risk_flags", [])),
            evidence_refs=evidence_refs,
            confidence=ConfidenceBreakdown(
                evidence_coverage=1.0 if evidence_refs else 0.0 if insurance_ids else 1.0,
                source_authority="E_SYNTHETIC",
                freshness_status="current" if evidence_refs else "unknown",
                retrieval_quality=max((float(hit.score) for hit in hits), default=None),
                consistency_status="consistent",
                rule_certainty="deterministic",
                input_completeness=round(coverage_present / coverage_total, 4) if result.get("coverage_checks") else 1.0,
                display_confidence=1.0 if status == "ready_for_insurance_review" else 0.6,
                calibration_policy_version="insurance-confidence-v1",
            ),
            domain_result=result,
            stop_reason=stop_reason,
            model=self.model,
            prompt_version="insurance-expert-structured-v1",
            tools_called=self.gateway.trace.called,
            denied_tools=self.gateway.trace.denied,
            latency_ms=int((perf_counter() - started) * 1000),
            fallback_reason=retrieval_fallback_reason or self.last_fallback_reason,
            revision=task.round or 1,
        )
