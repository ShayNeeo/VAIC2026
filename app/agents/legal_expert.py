"""Independent Legal/Compliance Expert backed by deterministic eligibility."""

from __future__ import annotations

import hashlib
import uuid
from time import perf_counter
from typing import Any, Dict, Iterable, List, Optional

from app.agents.base import BaseExpertRuntime
from app.agents.contracts import (
    ConfidenceBreakdown,
    EvidenceReference,
    StopReason,
    SupportStatus,
    TaskAssignment,
)
from app.agents.finding_factory import build_finding, validate_assignment
from app.agents.manifests import LEGAL_MANIFEST
from app.eligibility.engine import EligibilityEngine
from app.knowledge.legal_service import LegalKnowledgeService
from app.safety.domain_guardrails import validate_legal_agent_output
from app.tools.agent_gateway import AgentToolGateway


class LegalComplianceAgent(BaseExpertRuntime):
    manifest = LEGAL_MANIFEST

    def __init__(self, rule_registry: Any, knowledge: Optional[LegalKnowledgeService] = None) -> None:
        super().__init__()
        self.engine = EligibilityEngine(rule_registry)
        self.knowledge = knowledge or LegalKnowledgeService()
        self.gateway = AgentToolGateway(
            self.manifest,
            {
                "eligibility_evaluate": self.engine.evaluate,
                "legal_search": self.knowledge.search,
                "legal_get_chunk": self.knowledge.index.exact_lookup_by_chunk_id,
                "legal_list_sources": self.knowledge.index.list_chunks,
            },
        )

    async def analyze(
        self,
        task: TaskAssignment,
        *,
        product_result: Dict[str, Any],
        customer_attributes: Dict[str, Any],
        documents: Optional[List[Dict[str, Any]]] = None,
        branch: str = "*",
    ):
        validate_assignment(task, self.manifest)
        self.gateway.reset_trace()
        started = perf_counter()
        product_ids = [str(item["product_id"]) for item in product_result.get("recommendations", [])]
        result = await self.gateway.call(
            "eligibility_evaluate",
            product_ids=product_ids,
            customer=customer_attributes,
            documents=documents or [],
        )
        validate_legal_agent_output(result)

        # Retrieval explains policy text; it never feeds a pass/fail mutation.
        policy_hits = []
        retrieval_fallback_reason: Optional[str] = None
        if product_ids:
            try:
                policy_hits = await self.gateway.call(
                    "legal_search",
                    query="điều kiện, hồ sơ và điểm chặn áp dụng cho sản phẩm",
                    branch=branch,
                    product_id=product_ids[0],
                    top_k=3,
                )
            except Exception as exc:
                retrieval_fallback_reason = f"legal_retrieval_{type(exc).__name__}"
                policy_hits = []

        constraints: List[Dict[str, Any]] = []
        unknowns: List[Dict[str, Any]] = []
        rationale: List[str] = []
        evidence_refs: List[EvidenceReference] = []
        has_hard_block = False
        for product in result.get("products", []):
            for rule in product.get("rules", []):
                status = str(rule.get("status"))
                if status == "passed":
                    continue
                severity = str(rule.get("severity"))
                is_hard = severity == "blocking" and status in {"failed", "pending_review"}
                has_hard_block = has_hard_block or is_hard
                constraint = {
                    "product_id": product.get("product_id"),
                    "rule_id": rule.get("rule_id"),
                    "status": status,
                    "severity": severity,
                    "failure_code": rule.get("failure_code"),
                    "field": rule.get("field"),
                    "overridable": bool(rule.get("human_review_allowed", False)),
                }
                constraints.append(constraint)
                if status == "pending_information":
                    unknowns.append(
                        {
                            "field": rule.get("field"),
                            "required_for_product_id": product.get("product_id"),
                            "impact": "Không thể hoàn tất eligibility khi chưa có dữ liệu này.",
                        }
                    )
                rationale.append(
                    f"Rule {rule.get('rule_id')} trả {status} với severity={severity}; kết quả được giữ nguyên từ Rule Engine."
                )
                quote = str(rule.get("source_quote") or "")
                if rule.get("source_document_id"):
                    evidence_refs.append(
                        EvidenceReference(
                            claim_id=f"LEGAL-{rule.get('rule_id')}",
                            chunk_id=f"{rule.get('rule_id')}:{rule.get('rule_version')}",
                            document_id=str(rule.get("source_document_id")),
                            document_version=str(rule.get("source_version") or "UNKNOWN"),
                            content_hash=hashlib.sha256(quote.encode("utf-8")).hexdigest(),
                            location=rule.get("source_location"),
                            quote=quote or None,
                            support_status=SupportStatus.SUPPORTED if quote else SupportStatus.MISSING,
                        )
                    )
        for hit in policy_hits:
            evidence_refs.append(
                EvidenceReference(
                    claim_id=f"LEGAL-RETRIEVAL-{hit.chunk.chunk_id}",
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
                "Bạn là Legal/Compliance Expert. Giải thích ngắn gọn kết quả Rule Engine và khoảng trống bằng chứng. "
                "Không được sửa overall_status/rule status, miễn hard block, tạo sản phẩm hay phê duyệt ngoại lệ."
            ),
            payload={
                "rule_output": result,
                "constraints": constraints,
                "policy_evidence": [
                    {"document_id": ref.document_id, "version": ref.document_version, "location": ref.location}
                    for ref in evidence_refs
                ],
                "output_contract": {
                    "decision_rationale_summary": ["string"],
                    "inferences": [{"statement": "string", "basis_rule_id": "string"}],
                    "unknowns": [{"field": "string", "impact": "string"}],
                },
            },
        )
        if isinstance(llm, dict):
            extra_rationale = llm.get("decision_rationale_summary")
            if isinstance(extra_rationale, list):
                rationale = [str(item) for item in extra_rationale[:8] if str(item).strip()] or rationale
            extra_unknowns = llm.get("unknowns")
            if isinstance(extra_unknowns, list):
                unknowns.extend(item for item in extra_unknowns[:8] if isinstance(item, dict))
        overall = str(result.get("overall_status", "pending_review"))
        conclusion = f"Eligibility deterministic kết luận {overall}; Legal Expert không thay đổi verdict này."
        stop_reason = (
            StopReason.HARD_BLOCK
            if has_hard_block
            else StopReason.FALLBACK
            if self.last_fallback_reason
            else StopReason.INSUFFICIENT_EVIDENCE
            if overall == "pending_information"
            else StopReason.COMPLETED
        )
        return build_finding(
            manifest=self.manifest,
            task=task,
            finding_id=f"FND-LEGAL-{uuid.uuid4().hex[:10].upper()}",
            conclusion=conclusion,
            rationale=rationale or ["Không có rule vi phạm trong output deterministic hiện tại."],
            known_facts=({"product_ids": product_ids}, {"overall_status": overall}),
            inferences=tuple(
                item for item in (llm or {}).get("inferences", [])[:8] if isinstance(item, dict)
            ) if isinstance(llm, dict) else (),
            unknowns=unknowns,
            assumptions=(),
            recommendations=tuple(
                {"action": "collect_information", "field": item.get("field")} for item in unknowns
            ),
            constraints=constraints,
            evidence_refs=evidence_refs,
            confidence=ConfidenceBreakdown(
                evidence_coverage=1.0 if all(ref.quote for ref in evidence_refs) else 0.75 if evidence_refs else 0.0,
                source_authority="E_SYNTHETIC",
                freshness_status="current" if evidence_refs else "unknown",
                retrieval_quality=max((float(hit.score) for hit in policy_hits), default=None),
                consistency_status="consistent",
                rule_certainty="deterministic",
                input_completeness=1.0 if overall != "pending_information" else 0.6,
                display_confidence=1.0 if overall in {"passed", "failed"} else 0.7,
                calibration_policy_version="legal-confidence-v1",
            ),
            domain_result=result,
            stop_reason=stop_reason,
            model=self.model,
            prompt_version="legal-expert-structured-v1",
            tools_called=self.gateway.trace.called,
            denied_tools=self.gateway.trace.denied,
            latency_ms=int((perf_counter() - started) * 1000),
            fallback_reason=retrieval_fallback_reason or self.last_fallback_reason,
            revision=task.round or 1,
        )

    async def evaluate(
        self,
        product_result: Dict[str, Any],
        customer_attributes: Dict[str, Any],
        *,
        documents: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        product_ids = [item["product_id"] for item in product_result.get("recommendations", [])]
        return self.engine.evaluate(product_ids, customer=customer_attributes, documents=documents or [])
