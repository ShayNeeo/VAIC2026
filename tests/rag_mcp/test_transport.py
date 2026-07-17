from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import time
from dataclasses import replace

import httpx

from services.rag_mcp.client import RagMCPClient
from services.rag_mcp.config import settings
from services.rag_mcp.schemas import CallerPrincipal, SearchFilters, SearchKnowledgeRequest


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_health(url: str, timeout: float = 40.0) -> None:
    # 40s (not the original 12s): this spawns a brand-new Python interpreter
    # + uvicorn server subprocess, and 12s was observed to be too tight when
    # run inside the full suite (163+ other tests already consuming CPU) --
    # see docs/RAG_PROVIDER_AND_FALLBACK.md "Known flake" section. The
    # transport/auth assertions below are unchanged; only the startup budget
    # grew.
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(url, timeout=0.5).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    raise AssertionError("RAG MCP server did not become healthy")


def test_official_mcp_streamable_http_transport_with_service_auth(tmp_path):
    port = free_port()
    token = "transport-test-service-token"
    env = os.environ.copy()
    env.update(
        {
            "RAG_MCP_HOST": "127.0.0.1",
            "RAG_MCP_PORT": str(port),
            "RAG_MCP_URL": f"http://127.0.0.1:{port}/mcp",
            "RAG_MCP_DB_PATH": str(tmp_path / "transport.sqlite3"),
            "RAG_MCP_SERVICE_TOKEN": token,
            "RAG_MCP_REQUIRE_AUTH": "true",
        }
    )
    # Captured (not DEVNULL'd) so a startup failure is diagnosable instead of
    # only ever surfacing as an opaque "did not become healthy" timeout.
    server_log_path = tmp_path / "rag_mcp_server_subprocess.log"
    server_log = server_log_path.open("wb")
    process = subprocess.Popen(
        [sys.executable, "-m", "services.rag_mcp.server"],
        cwd=os.getcwd(),
        env=env,
        stdout=server_log,
        stderr=subprocess.STDOUT,
    )
    try:
        try:
            wait_for_health(f"http://127.0.0.1:{port}/health")
        except AssertionError:
            server_log.flush()
            log_tail = server_log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
            raise AssertionError(
                "RAG MCP server did not become healthy; subprocess output:\n" + log_tail
            ) from None
        unauthorized = httpx.post(
            f"http://127.0.0.1:{port}/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            timeout=2.0,
            follow_redirects=True,
        )
        assert unauthorized.status_code == 401

        async def scenario():
            runtime = replace(
                settings,
                port=port,
                url=f"http://127.0.0.1:{port}/mcp",
                db_path=tmp_path / "transport.sqlite3",
                service_token=token,
                require_auth=True,
            )
            request = SearchKnowledgeRequest(
                query="chi trả lương cho 500 nhân viên",
                principal=CallerPrincipal(
                    employee_id="RM-TRANSPORT",
                    branch="HN01",
                    agent_type="KnowledgeAdmin",
                    agent_instance_id="transport-test-instance-0001",
                    roles=["RM", "KnowledgeAdmin"],
                    permissions=["knowledge:admin"],
                ),
                filters=SearchFilters(domain="product"),
                trace_id="TRACE-MCP-TRANSPORT",
            )
            async with RagMCPClient(runtime) as client:
                tools = await client.list_tools()
                health = await client.health()
                result = await client.search(request)
            return tools, health, result

        tools, health, result = asyncio.run(scenario())
        assert tools == ["rag_search", "rag_get_chunk", "rag_list_sources", "rag_health"]
        assert health.status == "ok"
        assert result.grounded is True
        assert result.chunks[0].product_id == "PRD-PY-001"
        assert result.audit_event_id.startswith("RAG-AUD-")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        server_log.close()
