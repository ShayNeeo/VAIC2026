"""Product Agent MCP Server — FastMCP entrypoint."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from mcp_common.schemas import ProductResult, EvidenceItem
from mcp_common.config import settings

from servers.product_agent.rag.retriever import ProductRetriever
from servers.product_agent.product.matcher import ProductMatcher
from servers.product_agent.safety.guardrails import InputGuardrails, OutputGuardrails
from servers.product_agent.safety.verify import EvidenceVerifier


mcp = FastMCP("product-agent")
retriever = ProductRetriever()
matcher = ProductMatcher()
input_guardrails = InputGuardrails()
output_guardrails = OutputGuardrails()
verifier = EvidenceVerifier()


class ProductAnalyzeRequest(BaseModel):
    request_text: str
    company_profile: Dict[str, Any]
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    trace_id: Optional[str] = None


class ProductSearchRequest(BaseModel):
    q: str
    top_k: int = 5


@mcp.tool()
async def product_analyze(request: dict) -> dict:
    """Full Product Agent pipeline: RAG → Guardrails → Match → Verify."""
    trace_id = request.get("trace_id") or str(uuid.uuid4())[:8]
    request_text = request.get("request_text", "")
    company_profile = request.get("company_profile", {})
    documents = request.get("documents", [])

    # 1. Input Guardrails
    gr = input_guardrails.inspect(request_text, documents)
    if not gr["allowed"]:
        return {"allowed": False, "error": "INPUT_BLOCKED", "security_flags": gr["security_flags"], "trace_id": trace_id}

    # 2. RAG Retrieval
    retrieval_results = retriever.search(gr["sanitized_text"], top_k=settings.RAG_TOP_K)

    # 3. Matcher
    match_result = matcher.run(
        request_text=gr["sanitized_text"],
        profile=company_profile,
        retrieval_results=retrieval_results,
    )

    # 4. Evidence Verification
    from mcp_common.schemas import EvidenceItem
    evidences = [EvidenceItem(**e) for e in match_result.get("citations", [])]
    verified_evidences, verify_summary = verifier.verify(evidences)

    # 5. Output Guardrails
    allowed, reason = output_guardrails.validate_output(
        product_result=match_result,
        evidences=verified_evidences,
        legal_result={},
    )

    # Build ProductResult
    from mcp_common.schemas import ProductResult
    result = ProductResult(
        recommended_bundle=match_result["recommended_bundle"],
        recommended_products=match_result["recommended_products"],
        missing_parameters=match_result["missing_parameters"],
        retrieval_query=match_result["retrieval_query"],
        citations=verified_evidences,
        guardrail_verdict={
            "input_allowed": gr["allowed"],
            "input_flags": gr["security_flags"],
            "output_allowed": allowed,
            "output_reason": reason,
            "evidence_valid": verify_summary["all_valid"],
            "evidence_valid_count": verify_summary["valid"],
            "evidence_invalid_count": verify_summary["invalid"],
        },
    )

    return {"allowed": allowed, "result": result.model_dump(), "trace_id": trace_id}


@mcp.tool()
async def product_search(request: dict) -> dict:
    """Raw RAG search for debugging / RM direct query."""
    q = request.get("q", "")
    top_k = request.get("top_k", 5)
    context = retriever.build_context(q, top_k=top_k)
    return {
        "query": q,
        "context": context["context"],
        "sources": context["sources"],
        "grounded": context["grounded"],
    }


@mcp.tool()
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "product-agent", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.http_app(), host=settings.BIND_HOST, port=settings.PRODUCT_AGENT_PORT)