"""Small official-SDK client used by an orchestrator or smoke test."""

from __future__ import annotations

import json
from contextlib import AsyncExitStack
from typing import Any, Dict, Optional

import httpx
from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client

from services.rag_mcp.config import RagMCPSettings, settings as default_settings
from services.rag_mcp.schemas import (
    GetChunkRequest,
    GetChunkResponse,
    HealthResponse,
    ListSourcesRequest,
    ListSourcesResponse,
    SearchKnowledgeRequest,
    SearchKnowledgeResponse,
)


class RagMCPClient:
    def __init__(self, settings: RagMCPSettings = default_settings) -> None:
        self.settings = settings
        self._stack: Optional[AsyncExitStack] = None
        self._session: Optional[ClientSession] = None

    async def __aenter__(self) -> "RagMCPClient":
        self._stack = AsyncExitStack()
        await self._stack.__aenter__()
        headers = {"Authorization": f"Bearer {self.settings.service_token}"} if self.settings.require_auth else {}
        http_client = await self._stack.enter_async_context(
            httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True)
        )
        read_stream, write_stream, _ = await self._stack.enter_async_context(
            streamable_http_client(self.settings.url, http_client=http_client)
        )
        self._session = await self._stack.enter_async_context(ClientSession(read_stream, write_stream))
        await self._session.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._stack is not None:
            await self._stack.__aexit__(exc_type, exc, tb)
        self._session = None
        self._stack = None

    @property
    def session(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError("RagMCPClient must be used as an async context manager")
        return self._session

    async def list_tools(self) -> list[str]:
        result = await self.session.list_tools()
        return [tool.name for tool in result.tools]

    async def _call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.session.call_tool(name, arguments=arguments)
        if result.isError:
            message = " | ".join(
                item.text for item in result.content if isinstance(item, types.TextContent)
            )
            raise RuntimeError(f"MCP tool {name} failed: {message}")
        if result.structuredContent is not None:
            return dict(result.structuredContent)
        for item in result.content:
            if isinstance(item, types.TextContent):
                return dict(json.loads(item.text))
        raise RuntimeError(f"MCP tool {name} returned no structured content")

    async def search(self, request: SearchKnowledgeRequest) -> SearchKnowledgeResponse:
        payload = await self._call("rag_search", {"request": request.model_dump(mode="json")})
        return SearchKnowledgeResponse.model_validate(payload)

    async def get_chunk(self, request: GetChunkRequest) -> GetChunkResponse:
        payload = await self._call("rag_get_chunk", {"request": request.model_dump(mode="json")})
        return GetChunkResponse.model_validate(payload)

    async def list_sources(self, request: ListSourcesRequest) -> ListSourcesResponse:
        payload = await self._call("rag_list_sources", {"request": request.model_dump(mode="json")})
        return ListSourcesResponse.model_validate(payload)

    async def health(self) -> HealthResponse:
        payload = await self._call("rag_health", {})
        return HealthResponse.model_validate(payload)
