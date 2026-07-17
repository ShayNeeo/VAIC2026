"""Product Agent pipeline - pure orchestration, no MCP wiring.

Stages (blueprint §7 / §14):
    input guardrails -> RAG retrieval -> matcher -> evidence verify -> output guardrails

The pipeline is deterministic and LLM-optional. ``run_pipeline`` returns a
typed :class:`PipelineResult`; the MCP server maps it to the wire format.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from mcp_common.config import settings
from mcp_common.schemas import ProductResult, EvidenceItem, ResolvedValue

from servers.v3_product_agent.rag.retriever import ProductRetriever
from servers.v3_product_agent.product.matcher import ProductMatcher
from servers.v3_product_agent.safety.guardrails import InputGuardrails, OutputGuardrails
from servers.v3_product_agent.safety.verify import EvidenceVerifier


@dataclass
class PipelineRequest:
    request_text: str
    company_profile: Dict[str, Any]
    documents: List[Dict[str, Any]] = field(default_factory=list)
    trace_id: Optional[str] = None
    context_snapshot: Optional[Dict[str, Any]] = None


@dataclass
class PipelineResult:
    allowed: bool
    trace_id: str
    error: Optional[str] = None
    security_flags: List[str] = field(default_factory=list)
    result: Optional[ProductResult] = None
    guardrail_verdict: Dict[str, Any] = field(default_factory=dict)


class ProductPipeline:
    """Coordinates the five-stage Product Agent flow."""

    def __init__(self) -> None:
        self.retriever = ProductRetriever()
        self.matcher = ProductMatcher()
        self.input_guardrails = InputGuardrails()
        self.output_guardrails = OutputGuardrails()
        self.verifier = EvidenceVerifier()

    def run(self, req: PipelineRequest, legal_result: Optional[Dict[str, Any]] = None) -> PipelineResult:
        trace_id = req.trace_id or uuid.uuid4().hex[:8]

        # 1. INPUT GUARDRAILS
        guard = self.input_guardrails.inspect(
            req.request_text, req.documents, context_snapshot=req.context_snapshot
        )
        if not guard["allowed"]:
            return PipelineResult(
                allowed=False,
                trace_id=trace_id,
                error="INPUT_BLOCKED",
                security_flags=guard["security_flags"],
                guardrail_verdict={"input_allowed": False, "input_flags": guard["security_flags"]},
            )

        # 2. RAG RETRIEVAL
        sanitized = guard["sanitized_text"]
        retrieval_results = self.retriever.search(sanitized, top_k=settings.RAG_TOP_K)

        # 3. MATCHER (deterministic + optional LLM reason)
        match = self.matcher.run(
            request_text=sanitized,
            profile=req.company_profile,
            retrieval_results=retrieval_results,
        )

        # 4. EVIDENCE VERIFICATION (items built once in matcher, passed by ref)
        evidences: List[EvidenceItem] = match["evidences"]
        verified, verify_summary = self.verifier.verify(evidences)

        # 5. OUTPUT GUARDRAILS
        # Legal result is owned by the Legal Agent; default to safe pending_review
        # when the orchestrator has not supplied it yet (fail closed, never pass).
        safe_legal = legal_result or {"failed_checks": [], "status": "pending_review"}
        allowed, reason = self.output_guardrails.validate_output(
            product_result=match, evidences=verified, legal_result=safe_legal
        )

        provenance = self._build_provenance(match, verified)
        result = ProductResult(
            recommended_bundle=match["recommended_bundle"],
            recommended_products=match["recommended_products"],
            missing_parameters=match["missing_parameters"],
            retrieval_query=match["retrieval_query"],
            citations=verified,
            guardrail_verdict={
                "input_allowed": guard["allowed"],
                "input_flags": guard["security_flags"],
                "output_allowed": allowed,
                "output_reason": reason,
                "evidence_valid": verify_summary["all_valid"],
                "evidence_valid_count": verify_summary["valid"],
                "evidence_invalid_count": verify_summary["invalid"],
                "needs": match.get("needs", []),
                "missing_parameters": match["missing_parameters"],
            },
            provenance=provenance,
        )

        return PipelineResult(
            allowed=allowed,
            trace_id=trace_id,
            result=result,
            guardrail_verdict=result.guardrail_verdict,
        )

    @staticmethod
    def _build_provenance(match: Dict[str, Any], evidences: List[EvidenceItem]) -> Dict[str, Any]:
        """F-04 provenance: catalog version/owner + evidence ids per product."""
        from servers.v3_product_agent.product.catalog import source_ref

        evidence_ids = [e.claim_id for e in evidences]
        product_provenance = {}
        for pid in match["recommended_products"]:
            ref = source_ref(pid)
            product_provenance[pid] = {
                "source_document_id": ref["source_document_id"],
                "source_section": ref["source_section"],
                "source_version": ref["source_version"],
                "owner": ref["owner"],
                "evidence_ids": evidence_ids,
            }
        return {"schema_version": "3.0.0", "products": product_provenance}
