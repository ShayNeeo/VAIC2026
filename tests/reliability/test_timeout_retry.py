"""Reliability Tests - Tier 5 REL-* cases."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

# REL-01: Gemma timeout -> retry -> fallback
@pytest.mark.asyncio
async def test_rel_01_gemma_timeout_fallback():
    from mcp_common.llm_client import GemmaClient, LLMClientError

    client = GemmaClient(api_key="test", timeout=0.001, max_retries=1)

    with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
        import httpx
        mock_post.side_effect = httpx.TimeoutException("timeout")
        with pytest.raises(LLMClientError):
            await client.generate("test")
        assert mock_post.call_count == 2  # initial + 1 retry


# REL-02: RAG index unavailable -> circuit breaker -> manual path
@pytest.mark.asyncio
async def test_rel_02_rag_unavailable_circuit_breaker():
    from servers.v3_product_agent.rag.retriever import ProductRetriever

    retriever = ProductRetriever()
    original_embed = retriever._embedder

    def failing_embed(text):
        raise RuntimeError("Index unavailable")
    retriever._embedder = failing_embed

    try:
        results = retriever.search("test", top_k=3)
        assert results == []
    finally:
        retriever._embedder = original_embed


# REL-03: Concurrent approve -> single external action
@pytest.mark.asyncio
async def test_rel_03_concurrent_approve_idempotent():
    from servers.approval_agent.server import issue_token, verify_token, IssueTokenRequest, VerifyTokenRequest

    issue = await issue_token(IssueTokenRequest(
        case_id="CASE-CONCURRENT", rm_id="RM-001",
        permissions=["create_crm_case"], payload={"action": "create_case", "idempotency_key": "idem-123"},
    ))

    tasks = [
        verify_token(VerifyTokenRequest(
            token=issue["token"], case_id="CASE-CONCURRENT", rm_id="RM-001",
            payload={"action": "create_case", "idempotency_key": "idem-123"},
        ))
        for _ in range(3)
    ]
    results = await asyncio.gather(*tasks)

    valid_count = sum(1 for r in results if r.get("valid"))
    assert valid_count == 1


# REL-04: Replay approval dedupe
@pytest.mark.asyncio
async def test_rel_04_replay_dedupe():
    from servers.approval_agent.server import issue_token, verify_token, IssueTokenRequest, VerifyTokenRequest

    issue = await issue_token(IssueTokenRequest(
        case_id="CASE-REPLAY", rm_id="RM-001",
        permissions=["create_crm_case"], payload={"action": "create_case"},
    ))

    r1 = await verify_token(VerifyTokenRequest(
        token=issue["token"], case_id="CASE-REPLAY", rm_id="RM-001", payload={"action": "create_case"},
    ))
    r2 = await verify_token(VerifyTokenRequest(
        token=issue["token"], case_id="CASE-REPLAY", rm_id="RM-001", payload={"action": "create_case"},
    ))

    assert r1["valid"] is True
    assert r2["valid"] is False
    assert r2["reason"] == "TOKEN_ALREADY_USED"


# REL-05: MCP server crash mid-flow -> orchestrator fallback
@pytest.mark.asyncio
async def test_rel_05_mcp_crash_fallback():
    from app.services.mcp_clients import MCPClientHub

    hub = MCPClientHub()
    hub._clients = {"product": None}

    with patch.object(hub, '_get_client', return_value=None):
        result = await hub.product_analyze(
            "test request",
            {"employees_count": 100},
            [],
            "trace-123"
        )
        assert "result" in result or "error" in result
