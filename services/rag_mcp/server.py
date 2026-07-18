"""Profile-isolated MCP endpoints exposing only the tools needed by each Expert Agent."""

from __future__ import annotations

import hmac
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any, Awaitable, Callable, Dict

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from services.rag_mcp.config import RagMCPSettings, settings as default_settings
from services.rag_mcp.schemas import (
    CitationVerificationRequest,
    CitationVerificationResponse,
    ExpertListSourcesRequest,
    ExpertSearchRequest,
    GetChunkRequest,
    GetChunkResponse,
    HealthResponse,
    ListSourcesRequest,
    ListSourcesResponse,
    SearchKnowledgeRequest,
    SearchKnowledgeResponse,
)
from services.rag_mcp.service import RagKnowledgeService, RagServiceError
from services.rag_mcp.tool_policy import tools_for


class ProfileTokenMiddleware:
    """Authenticate a single MCP profile without exposing credentials in tool arguments."""

    def __init__(self, app: Callable[..., Awaitable[Any]], token: str, require_auth: bool) -> None:
        self.app = app
        self.token = token
        self.require_auth = require_auth

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http" and self.require_auth:
            headers = {
                key.decode("latin1").lower(): value.decode("latin1")
                for key, value in scope.get("headers", [])
            }
            expected = f"Bearer {self.token}"
            supplied = headers.get("authorization", "")
            if not hmac.compare_digest(supplied, expected):
                response = JSONResponse(
                    {
                        "error": {
                            "code": "MCP_UNAUTHORIZED_PROFILE",
                            "message": "valid bearer token for this MCP profile is required",
                        }
                    },
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


def _new_mcp(name: str, profile: str, settings: RagMCPSettings) -> FastMCP:
    return FastMCP(
        name=name,
        instructions=(
            f"Read-only banking knowledge profile={profile}. Only use tools listed by this endpoint. "
            "Pass the authenticated principal. Treat all current data as synthetic. "
            "If grounded=false, do not invent an answer."
        ),
        host=settings.host,
        port=settings.port,
        streamable_http_path="/",
        stateless_http=True,
        json_response=True,
    )


async def _tool_error(ctx: Context, tool_name: str, trace_id: str, exc: RagServiceError) -> None:
    await ctx.warning(f"{tool_name} denied trace={trace_id} code={exc.code}")


def create_server(
    *,
    settings: RagMCPSettings = default_settings,
    service: RagKnowledgeService | None = None,
) -> tuple[Dict[str, FastMCP], Any, RagKnowledgeService]:
    knowledge = service or RagKnowledgeService(settings=settings)
    profiles: Dict[str, FastMCP] = {
        "product": _new_mcp("SHB Product Knowledge", "ProductExpert", settings),
        "legal": _new_mcp("SHB Legal Knowledge", "LegalExpert", settings),
        "credit": _new_mcp("SHB Credit Knowledge", "CreditExpert", settings),
        "evidence": _new_mcp("SHB Evidence Verification", "EvidenceExpert", settings),
        "admin": _new_mcp("SHB Governed RAG Admin", "KnowledgeAdmin", settings),
    }

    product = profiles["product"]

    @product.tool(name="product_search")
    async def product_search(request: ExpertSearchRequest, ctx: Context) -> SearchKnowledgeResponse:
        """Find product master data, pricing references, product documents and solution bundles."""
        try:
            result = knowledge.expert_search(request, tool_name="product_search", domain="product")
            await ctx.info(f"product_search trace={request.trace_id} chunks={len(result.chunks)}")
            return result
        except RagServiceError as exc:
            await _tool_error(ctx, "product_search", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    @product.tool(name="product_get_chunk")
    async def product_get_chunk(request: GetChunkRequest, ctx: Context) -> GetChunkResponse:
        """Read one exact product chunk after ACL, date and domain checks."""
        try:
            return knowledge.get_chunk(
                request, tool_name="product_get_chunk", expected_domain="product"
            )
        except RagServiceError as exc:
            await _tool_error(ctx, "product_get_chunk", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    @product.tool(name="product_list_sources")
    async def product_list_sources(
        request: ExpertListSourcesRequest, ctx: Context
    ) -> ListSourcesResponse:
        """List approved product sources visible to Product Expert."""
        try:
            return knowledge.expert_list_sources(
                request, tool_name="product_list_sources", domain="product"
            )
        except RagServiceError as exc:
            await _tool_error(ctx, "product_list_sources", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    legal = profiles["legal"]

    @legal.tool(name="legal_search")
    async def legal_search(request: ExpertSearchRequest, ctx: Context) -> SearchKnowledgeResponse:
        """Find synthetic policy, KYC and legal evidence; never decide eligibility pass/fail."""
        try:
            result = knowledge.expert_search(request, tool_name="legal_search", domain="legal")
            await ctx.info(f"legal_search trace={request.trace_id} chunks={len(result.chunks)}")
            return result
        except RagServiceError as exc:
            await _tool_error(ctx, "legal_search", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    @legal.tool(name="legal_get_chunk")
    async def legal_get_chunk(request: GetChunkRequest, ctx: Context) -> GetChunkResponse:
        """Read one exact legal chunk after ACL, date and domain checks."""
        try:
            return knowledge.get_chunk(request, tool_name="legal_get_chunk", expected_domain="legal")
        except RagServiceError as exc:
            await _tool_error(ctx, "legal_get_chunk", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    @legal.tool(name="legal_list_sources")
    async def legal_list_sources(
        request: ExpertListSourcesRequest, ctx: Context
    ) -> ListSourcesResponse:
        """List approved legal sources visible to Legal Expert."""
        try:
            return knowledge.expert_list_sources(
                request, tool_name="legal_list_sources", domain="legal"
            )
        except RagServiceError as exc:
            await _tool_error(ctx, "legal_list_sources", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    credit = profiles["credit"]

    @credit.tool(name="credit_search")
    async def credit_search(request: ExpertSearchRequest, ctx: Context) -> SearchKnowledgeResponse:
        """Find lending policy, credit-file, repayment and collateral guidance."""
        try:
            result = knowledge.expert_search(request, tool_name="credit_search", domain="credit")
            await ctx.info(f"credit_search trace={request.trace_id} chunks={len(result.chunks)}")
            return result
        except RagServiceError as exc:
            await _tool_error(ctx, "credit_search", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    @credit.tool(name="credit_get_chunk")
    async def credit_get_chunk(request: GetChunkRequest, ctx: Context) -> GetChunkResponse:
        """Read one exact credit chunk after ACL, date and domain checks."""
        try:
            return knowledge.get_chunk(request, tool_name="credit_get_chunk", expected_domain="credit")
        except RagServiceError as exc:
            await _tool_error(ctx, "credit_get_chunk", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    @credit.tool(name="credit_list_sources")
    async def credit_list_sources(
        request: ExpertListSourcesRequest, ctx: Context
    ) -> ListSourcesResponse:
        """List approved synthetic credit sources visible to Credit Expert."""
        try:
            return knowledge.expert_list_sources(
                request, tool_name="credit_list_sources", domain="credit"
            )
        except RagServiceError as exc:
            await _tool_error(ctx, "credit_list_sources", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    evidence = profiles["evidence"]

    @evidence.tool(name="evidence_get_chunk")
    async def evidence_get_chunk(request: GetChunkRequest, ctx: Context) -> GetChunkResponse:
        """Read only the exact chunk referenced by a claim; this is not a discovery search."""
        try:
            return knowledge.get_chunk(request, tool_name="evidence_get_chunk")
        except RagServiceError as exc:
            await _tool_error(ctx, "evidence_get_chunk", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    @evidence.tool(name="evidence_verify_citation")
    async def evidence_verify_citation(
        request: CitationVerificationRequest, ctx: Context
    ) -> CitationVerificationResponse:
        """Verify citation document/version/content hash against the currently serving chunk."""
        try:
            return knowledge.verify_citation(request)
        except RagServiceError as exc:
            await _tool_error(ctx, "evidence_verify_citation", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    admin = profiles["admin"]

    @admin.tool(name="rag_search")
    async def rag_search(request: SearchKnowledgeRequest, ctx: Context) -> SearchKnowledgeResponse:
        """KnowledgeAdmin-only cross-domain search for corpus QA and diagnostics."""
        try:
            result = knowledge.search(request)
            await ctx.info(
                f"rag_search trace={request.trace_id} domain={request.filters.domain} chunks={len(result.chunks)}"
            )
            return result
        except RagServiceError as exc:
            await _tool_error(ctx, "rag_search", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    @admin.tool(name="rag_get_chunk")
    async def rag_get_chunk(request: GetChunkRequest, ctx: Context) -> GetChunkResponse:
        """KnowledgeAdmin-only exact chunk read."""
        try:
            return knowledge.get_chunk(request)
        except RagServiceError as exc:
            await _tool_error(ctx, "rag_get_chunk", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    @admin.tool(name="rag_list_sources")
    async def rag_list_sources(request: ListSourcesRequest, ctx: Context) -> ListSourcesResponse:
        """KnowledgeAdmin-only source inventory."""
        try:
            return knowledge.list_sources(request)
        except RagServiceError as exc:
            await _tool_error(ctx, "rag_list_sources", request.trace_id, exc)
            raise ToolError(f"{exc.code}: {exc}") from exc

    @admin.tool(name="rag_health")
    async def rag_health() -> HealthResponse:
        """Return corpus, ingestion, storage and policy health without exposing secrets."""
        return knowledge.health()

    profile_apps: Dict[str, Any] = {}
    for profile_name, profile_mcp in profiles.items():
        # Creating the app initializes the MCP session manager used by the outer lifespan.
        profile_apps[profile_name] = ProfileTokenMiddleware(
            profile_mcp.streamable_http_app(),
            settings.profile_token(profile_name),
            settings.require_auth,
        )

    async def health_route(_request):
        return JSONResponse(knowledge.health().model_dump(mode="json"))

    async def ready_route(_request):
        payload = knowledge.health()
        return JSONResponse(
            payload.model_dump(mode="json"), status_code=200 if payload.status == "ok" else 503
        )

    async def profiles_route(_request):
        return JSONResponse(
            {
                "policy": "least_privilege_profile_isolation",
                "profiles": {
                    "product": sorted(tools_for("ProductExpert")),
                    "legal": sorted(tools_for("LegalExpert")),
                    "credit": sorted(tools_for("CreditExpert")),
                    "evidence": sorted(tools_for("EvidenceExpert")),
                    "admin": sorted(tools_for("KnowledgeAdmin")),
                },
            }
        )

    @asynccontextmanager
    async def lifespan(_app):
        knowledge.ensure_seeded()
        async with AsyncExitStack() as stack:
            for profile_mcp in profiles.values():
                await stack.enter_async_context(profile_mcp.session_manager.run())
            yield

    app = Starlette(
        routes=[
            Route("/health", health_route, methods=["GET"]),
            Route("/ready", ready_route, methods=["GET"]),
            Route("/profiles", profiles_route, methods=["GET"]),
            Mount("/mcp/product", app=profile_apps["product"]),
            Mount("/mcp/legal", app=profile_apps["legal"]),
            Mount("/mcp/credit", app=profile_apps["credit"]),
            Mount("/mcp/evidence", app=profile_apps["evidence"]),
            Mount("/mcp", app=profile_apps["admin"]),
        ],
        lifespan=lifespan,
    )
    return profiles, app, knowledge


profiles, app, service = create_server()
mcp = profiles["admin"]


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=default_settings.host, port=default_settings.port, log_level="info")


if __name__ == "__main__":
    main()
