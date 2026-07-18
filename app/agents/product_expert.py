"""Independent Product Expert runtime."""

from __future__ import annotations

import hashlib
import uuid
from time import perf_counter
from typing import Any, Dict, Optional, Sequence

from app.agents.base import BaseExpertRuntime
from app.agents.contracts import (
    ConfidenceBreakdown,
    EvidenceReference,
    StopReason,
    SupportStatus,
    TaskAssignment,
)
from app.agents.finding_factory import build_finding, validate_assignment
from app.agents.manifests import PRODUCT_MANIFEST
from app.knowledge.service import ProductKnowledgeService
from app.product.service import ProductService
from app.tools.agent_gateway import AgentToolGateway


class ProductExpertAgent(BaseExpertRuntime):
    manifest = PRODUCT_MANIFEST

    def __init__(self, knowledge: ProductKnowledgeService, *, service: Optional[ProductService] = None) -> None:
        super().__init__()
        self.knowledge = knowledge
        self.service = service or ProductService(knowledge)
        self.gateway = AgentToolGateway(
            self.manifest,
            {
                "product_search": self.service.recommend,
                "product_get_chunk": self.knowledge.index.exact_lookup_by_chunk_id,
                "product_list_sources": self.knowledge.index.list_chunks,
            },
        )

    async def analyze(
        self,
        task: TaskAssignment,
        *,
        query: str,
        branch: str,
        segment: Optional[str] = None,
        requested_product_ids: Optional[Sequence[str]] = None,
        customer_attributes: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
        exclude_credit: bool = False,
        parent_finding_id: Optional[str] = None,
    ):
        validate_assignment(task, self.manifest)
        self.gateway.reset_trace()
        started = perf_counter()
        search_query = query
        effective_requested = requested_product_ids
        effective_top_k = top_k
        if exclude_credit:
            search_query = f"{query}; thanh toán, quản lý dòng tiền, thu chi, chi lương phi tín dụng"
            effective_requested = None
            effective_top_k = max(8, top_k)
        result = await self.gateway.call(
            "product_search",
            query=search_query,
            branch=branch,
            segment=segment,
            requested_product_ids=effective_requested,
            customer_attributes=customer_attributes or {},
            top_k=effective_top_k,
        )
        if exclude_credit:
            result = dict(result)
            result["recommendations"] = [
                item for item in result.get("recommendations", []) if item.get("credit_flag") is False
            ][:top_k]
            result["status"] = "grounded" if result["recommendations"] else "no_grounded_product"
            result["alternative_constraint"] = "exclude:credit=true"

        llm = await self._enrich(
            system_prompt=(
                "Bạn là Product Expert ngân hàng doanh nghiệp. Chỉ diễn giải mức phù hợp của các sản phẩm có trong "
                "grounded_result; không tạo product ID, phí, lãi suất, hạn mức hay kết luận eligibility."
            ),
            payload={
                "business_need": query,
                "constraints": list(task.constraints),
                "customer_signals": self._safe_customer_signals(customer_attributes or {}),
                "grounded_candidates": [
                    {
                        "product_id": item.get("product_id"),
                        "product_family": item.get("product_family"),
                        "match_score": item.get("match_score"),
                        "matching_reason": item.get("matching_reason"),
                    }
                    for item in result.get("recommendations", [])
                ],
                "output_contract": {
                    "decision_rationale_summary": ["string"],
                    "inferences": [{"statement": "string", "basis_product_id": "string"}],
                    "unknowns": [{"field": "string", "impact": "string"}],
                },
            },
        )
        recommendations = list(result.get("recommendations", []))
        default_rationale = [
            f"{item.get('product_id')} được truy xuất từ catalog còn hiệu lực với match_score={item.get('match_score')}."
            for item in recommendations[:3]
        ]
        rationale = self._string_list(llm, "decision_rationale_summary") or default_rationale
        inferences = self._dict_list(llm, "inferences")
        unknowns = self._dict_list(llm, "unknowns")
        if not recommendations:
            unknowns.append({"field": "grounded_product", "impact": "Cần Product Specialist rà soát catalog."})

        evidences = []
        for item in recommendations:
            for source in item.get("evidences", []):
                quote = str(source.get("quote") or "")
                evidences.append(
                    EvidenceReference(
                        claim_id=str(source.get("claim_id") or f"PROD-{item.get('product_id')}"),
                        chunk_id=str(source.get("chunk_id") or source.get("claim_id") or item.get("product_id")),
                        document_id=str(source.get("source_document_id") or "UNKNOWN"),
                        document_version=str(source.get("source_version") or "UNKNOWN"),
                        content_hash=hashlib.sha256(quote.encode("utf-8")).hexdigest(),
                        location=source.get("location"),
                        quote=quote or None,
                        support_status=SupportStatus.SUPPORTED,
                    )
                )
        coverage = 1.0 if recommendations and len(evidences) >= len(recommendations) else 0.0
        conclusion = (
            f"Tìm thấy {len(recommendations)} sản phẩm có nguồn phù hợp để chuyển sang kiểm tra điều kiện."
            if recommendations
            else "Không tìm thấy sản phẩm có nguồn đáp ứng constraint hiện tại."
        )
        return build_finding(
            manifest=self.manifest,
            task=task,
            finding_id=f"FND-PRODUCT-{uuid.uuid4().hex[:10].upper()}",
            conclusion=conclusion,
            rationale=rationale,
            known_facts=({"business_need": query}, {"candidate_count": len(recommendations)}),
            inferences=inferences,
            unknowns=unknowns,
            assumptions=(),
            recommendations=recommendations,
            constraints=({"type": "exclude_credit", "active": exclude_credit},) if exclude_credit else (),
            evidence_refs=evidences,
            confidence=ConfidenceBreakdown(
                evidence_coverage=coverage,
                source_authority="E_SYNTHETIC",
                freshness_status="current" if recommendations else "unknown",
                retrieval_quality=max((float(item.get("match_score", 0)) for item in recommendations), default=0.0),
                consistency_status="consistent" if recommendations else "not_checked",
                rule_certainty="not_applicable",
                input_completeness=1.0 if query else 0.0,
                display_confidence=round(0.7 * coverage + 0.3 * min(1.0, len(recommendations) / max(1, top_k)), 4),
                calibration_policy_version="product-confidence-v1",
            ),
            domain_result=result,
            stop_reason=StopReason.FALLBACK if self.last_fallback_reason else StopReason.COMPLETED,
            model=self.model,
            prompt_version="product-expert-structured-v1",
            tools_called=self.gateway.trace.called,
            denied_tools=self.gateway.trace.denied,
            latency_ms=int((perf_counter() - started) * 1000),
            fallback_reason=self.last_fallback_reason,
            revision=task.round or 1,
            parent_finding_id=parent_finding_id,
        )

    async def recommend(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        """Compatibility adapter for callers not yet migrated to TaskAssignment."""

        return self.service.recommend(query, **kwargs)

    @staticmethod
    def _safe_customer_signals(values: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {
            "industry",
            "employees_count",
            "annual_revenue",
            "operating_years",
            "account_or_unit_count",
            "cash_flow_status",
        }
        return {key: values[key] for key in allowed if values.get(key) is not None}

    @staticmethod
    def _string_list(payload: Optional[Dict[str, Any]], key: str) -> list[str]:
        value = payload.get(key) if isinstance(payload, dict) else None
        return [str(item) for item in value[:8] if str(item).strip()] if isinstance(value, list) else []

    @staticmethod
    def _dict_list(payload: Optional[Dict[str, Any]], key: str) -> list[Dict[str, Any]]:
        value = payload.get(key) if isinstance(payload, dict) else None
        return [item for item in value[:8] if isinstance(item, dict)] if isinstance(value, list) else []
