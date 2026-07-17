"""V3 Product Agent MCP Server — RAG → Guardrails → Verify pipeline.

Flow:
1. Input Guardrails (injection regex + PII mask + semantic judge)
2. RAG Retrieval (hybrid dense+sparse, heuristic rerank, threshold 0.35)
3. Deterministic Matcher + LLM Reason
4. Evidence Verification (exact match fee/limit, semantic support)
5. Output Guardrails (block ungrounded, legal blocking, fee hallucination)

Tools: product_analyze, product_search, health_check
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from mcp_common.config import settings
from mcp_common.schemas import (
    ProductResult,
    EvidenceItem,
    ProductRecommendation,
    ProductBundle,
    ProductMatchScore,
    ProductPrerequisite,
    ValidationMethod,
    ResolvedValue,
)

from servers.v3_product_agent.rag.retriever import ProductRetriever
from servers.v3_product_agent.product.matcher import ProductMatcher
from servers.v3_product_agent.safety.guardrails import InputGuardrails, OutputGuardrails
from servers.v3_product_agent.safety.verify import EvidenceVerifier


# Initialize components
mcp = FastMCP("v3-product-agent")
retriever = ProductRetriever()
matcher = ProductMatcher()
input_guardrails = InputGuardrails()
output_guardrails = OutputGuardrails()
verifier = EvidenceVerifier()


# =============================================================================
# Request/Response Models
# =============================================================================

class ProductAnalyzeRequest(BaseModel):
    request_text: str
    company_profile: Dict[str, Any]
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    trace_id: Optional[str] = None
    context_snapshot: Optional[Dict[str, Any]] = None


class ProductSearchRequest(BaseModel):
    q: str
    top_k: int = 5


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "v3-product-agent"
    version: str = "3.0.0"
    config: Dict[str, Any]


# =============================================================================
# MCP Tools
# =============================================================================

@mcp.tool()
async def product_analyze(request: ProductAnalyzeRequest) -> Dict[str, Any]:
    """
    Full Product Agent pipeline: RAG → Guardrails → Match → Verify.

    Input: customer request + company profile + documents
    Output: ProductResult with bundle, citations, guardrail verdict
    """
    trace_id = request.trace_id or uuid.uuid4().hex[:8]

    # 1. INPUT GUARDRAILS
    guardrail_result = input_guardrails.inspect(
        request.request_text,
        request.documents,
        context_snapshot=request.context_snapshot
    )
    if not guardrail_result["allowed"]:
        return {
            "allowed": False,
            "error": "INPUT_BLOCKED",
            "security_flags": guardrail_result["security_flags"],
            "trace_id": trace_id,
        }

    # 2. RAG RETRIEVAL
    sanitized_text = guardrail_result["sanitized_text"]
    retrieval_results = retriever.search(sanitized_text, top_k=settings.RAG_TOP_K)

    # 3. MATCHER (deterministic + LLM reason)
    match_result = matcher.run(
        request_text=sanitized_text,
        profile=request.company_profile,
        retrieval_results=retrieval_results,
    )

    # 4. EVIDENCE VERIFICATION
    evidences = [
        EvidenceItem(**e) for e in match_result.get("citations", [])
    ]
    verified_evidences, verify_summary = verifier.verify(evidences)

    # 5. OUTPUT GUARDRAILS
    allowed, reason = output_guardrails.validate_output(
        product_result=match_result,
        evidences=verified_evidences,
        legal_result={},  # Legal runs separately in orchestrator
    )

    # Build ProductResult
    result = ProductResult(
        recommended_bundle=match_result["recommended_bundle"],
        recommended_products=match_result["recommended_products"],
        missing_parameters=match_result["missing_parameters"],
        retrieval_query=match_result["retrieval_query"],
        citations=verified_evidences,
        guardrail_verdict={
            "input_allowed": guardrail_result["allowed"],
            "input_flags": guardrail_result["security_flags"],
            "output_allowed": allowed,
            "output_reason": reason,
            "evidence_valid": verify_summary["all_valid"],
            "evidence_valid_count": verify_summary["valid"],
            "evidence_invalid_count": verify_summary["invalid"],
        },
    )

    return {
        "allowed": allowed,
        "result": result.model_dump(),
        "trace_id": trace_id,
    }


@mcp.tool()
async def product_search(request: ProductSearchRequest) -> Dict[str, Any]:
    """Raw RAG search for debugging / RM direct query."""
    context = retriever.build_context(request.q, top_k=request.top_k)
    return {
        "query": request.q,
        "context": context["context"],
        "sources": context["sources"],
        "grounded": context["grounded"],
    }


@mcp.tool()
async def health_check() -> HealthResponse:
    return HealthResponse(
        config={
            "rag_threshold": settings.RAG_THRESHOLD,
            "rag_top_k": settings.RAG_TOP_K,
            "dense_weight": settings.RAG_DENSE_WEIGHT,
            "sparse_weight": settings.RAG_SPARSE_WEIGHT,
            "use_real_embedding": settings.USE_REAL_EMBEDDING,
            "evidence_semantic_threshold": settings.EVIDENCE_SEMANTIC_THRESHOLD,
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.http_app(), host=settings.BIND_HOST, port=settings.PRODUCT_AGENT_PORT)