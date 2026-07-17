"""Transport-level smoke test: initialize MCP, list tools and fetch LLM-ready chunks."""

from __future__ import annotations

import asyncio
import json
import sys
import uuid

from services.rag_mcp.client import RagMCPClient
from services.rag_mcp.schemas import CallerPrincipal, SearchFilters, SearchKnowledgeRequest


async def run() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    request = SearchKnowledgeRequest(
        query="dịch vụ chi lương cho 500 nhân viên và quản lý dòng tiền",
        principal=CallerPrincipal(
            employee_id="RM-999",
            branch="HN01",
            roles=["RM"],
            permissions=["knowledge:read"],
        ),
        filters=SearchFilters(domain="product", segments=["CORPORATE"]),
        top_k=4,
        trace_id=f"TRACE-SMOKE-{uuid.uuid4().hex.upper()}",
    )
    async with RagMCPClient() as client:
        tools = await client.list_tools()
        health = await client.health()
        result = await client.search(request)
    print(
        json.dumps(
            {
                "tools": tools,
                "health": health.model_dump(mode="json"),
                "trace_id": request.trace_id,
                "grounded": result.grounded,
                "chunk_ids": [chunk.chunk_id for chunk in result.chunks],
                "context_text": result.context_text,
                "audit_event_id": result.audit_event_id,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(run())
