"""Legal Agent MCP Server V2.

Real implementation using the LegalAgentV2 adapter.
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Any, Dict, List

from app.schemas.state import SharedCaseState
from app.legal.adapter import LegalAgentV2
from app.legal.tools import screen_watchlist, check_representative_and_ubo
from mcp_common.config import settings


mcp = FastMCP(
    "legal-agent-v2",
    host=settings.BIND_HOST,
    port=settings.LEGAL_AGENT_PORT + 1
)


class LegalCheckRequest(BaseModel):
    company_profile: Dict[str, Any]
    product_proposal: Dict[str, Any]
    documents: List[Dict[str, Any]] = Field(default_factory=list)


class KYCUBORequest(BaseModel):
    company_profile: Dict[str, Any]
    documents: List[Dict[str, Any]] = Field(default_factory=list)


@mcp.tool()
async def legal_check(request: LegalCheckRequest) -> Dict[str, Any]:
    """Execute full Legal Agent V2 check."""
    agent = LegalAgentV2()
    
    # Mocking state for the agent
    # Actually, the agent expects SharedCaseState
    state = SharedCaseState(
        case_id="case-mcp",
        employee_id="mcp-user",
        customer_id=request.company_profile.get("customer_id", "unknown"),
        company_profile=request.company_profile,
        documents=request.documents,
        recommended_products=[request.product_proposal] if request.product_proposal else []
    )
    
    result = agent.run(state)
    return result


@mcp.tool()
async def kyc_ubo_screen(request: KYCUBORequest) -> Dict[str, Any]:
    """Execute watchlist/PEP/sanction screening and UBO check."""
    company_name = request.company_profile.get("company_name", "")
    tax_code = request.company_profile.get("tax_code", "")
    rep_dict = request.company_profile.get("representative", {})
    representatives = [rep_dict] if rep_dict else []
    
    watchlist_result = screen_watchlist(company_name, tax_code, representatives)
    ubo_result = check_representative_and_ubo(request.company_profile, request.documents)
    
    return {
        "watchlist_match": watchlist_result.get("match_found", False),
        "pep_match": "PEP" in watchlist_result.get("reason", ""),
        "sanction_match": "Sanction" in watchlist_result.get("reason", ""),
        "screening_id": "SCR-V2-001",
        "watchlist_details": watchlist_result,
        "ubo_details": ubo_result,
        "note": "Real execution via Extended Legal Tools",
    }


@mcp.tool()
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "legal-agent-v2", "version": "2.0.0"}


if __name__ == "__main__":
    mcp.run(transport="sse")
