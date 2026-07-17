"""V3 Product Agent MCP Server — RAG → Guardrails → Verify pipeline.

This module is wiring only. All decision logic lives in
``servers.v3_product_agent.product.pipeline``. The server exposes three MCP
tools and maps a :class:`PipelineResult` onto the wire contract.

Tools: ``product_analyze``, ``product_search``, ``health_check``
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from mcp_common.config import settings

from servers.v3_product_agent.product.pipeline import ProductPipeline, PipelineRequest


mcp = FastMCP("v3-product-agent")
pipeline = ProductPipeline()


# =============================================================================
# Request/Response Models
# =============================================================================

class ProductAnalyzeRequest(BaseModel):
    request_text: str
    company_profile: Dict[str, Any]
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    trace_id: Optional[str] = None
    context_snapshot: Optional[Dict[str, Any]] = None
    legal_result: Optional[Dict[str, Any]] = None


class ProductSearchRequest(BaseModel):
    q: str
    top_k: int = 5


class HealthResponseModel(BaseModel):
    status: str = "ok"
    service: str = "v3-product-agent"
    version: str = "3.0.0"
    config: Dict[str, Any]


# =============================================================================
# MCP Tools
# =============================================================================

@mcp.tool()
async def product_analyze(request: ProductAnalyzeRequest) -> Dict[str, Any]:
    """Full Product Agent pipeline: RAG → Guardrails → Match → Verify.

    Input: customer request + company profile + documents
    Output: ProductResult with bundle, citations, guardrail verdict
    """
    result = pipeline.run(
        PipelineRequest(
            request_text=request.request_text,
            company_profile=request.company_profile,
            documents=request.documents,
            trace_id=request.trace_id,
            context_snapshot=request.context_snapshot,
        ),
        legal_result=request.legal_result,
    )

    if not result.allowed:
        return {
            "allowed": False,
            "error": result.error or "BLOCKED",
            "security_flags": result.security_flags,
            "trace_id": result.trace_id,
        }

    return {
        "allowed": True,
        "result": result.result.model_dump(),
        "trace_id": result.trace_id,
    }


@mcp.tool()
async def product_search(request: ProductSearchRequest) -> Dict[str, Any]:
    """Raw RAG search for debugging / RM direct query."""
    context = pipeline.retriever.build_context(request.q, top_k=request.top_k)
    return {
        "query": request.q,
        "context": context["context"],
        "sources": context["sources"],
        "grounded": context["grounded"],
    }


@mcp.tool()
async def health_check() -> HealthResponseModel:
    return HealthResponseModel(
        config={
            "rag_threshold": settings.RAG_THRESHOLD,
            "rag_top_k": settings.RAG_TOP_K,
            "rag_sparse_gate": settings.RAG_SPARSE_GATE,
            "dense_weight": settings.RAG_DENSE_WEIGHT,
            "sparse_weight": settings.RAG_SPARSE_WEIGHT,
            "use_real_embedding": settings.USE_REAL_EMBEDDING,
            "evidence_semantic_threshold": settings.EVIDENCE_SEMANTIC_THRESHOLD,
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.http_app(), host=settings.BIND_HOST, port=settings.PRODUCT_AGENT_PORT)
