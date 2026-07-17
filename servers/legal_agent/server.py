"""Legal Agent MCP Server — STUB for team to fill.

Contract only: returns EligibilityResult schema.
"""

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


mcp = FastMCP("legal-agent")


class LegalCheckRequest(BaseModel):
    company_profile: Dict[str, Any]
    product_proposal: Dict[str, Any]
    documents: List[Dict[str, Any]] = Field(default_factory=list)


class KYCUBORequest(BaseModel):
    company_profile: Dict[str, Any]


@mcp.tool()
async def legal_check(request: LegalCheckRequest) -> Dict[str, Any]:
    """STUB: Return mock eligibility result matching EligibilityResult schema."""
    return {
        "eligible": True,
        "failed_checks": [],
        "missing_documents": ["UBO Declaration", "Audited Financial Statements"],
        "issues": [],
        "evidence": [
            {"agent": "Legal", "claim": "Company registration valid", "source_doc": "ERC.pdf", "page_or_section": "Section 1", "quote": "Active status confirmed", "is_valid": True}
        ],
        "schema_version": "2.0.0",
        "note": "STUB - replace with real KYC/UBO/eligibility logic",
    }


@mcp.tool()
async def kyc_ubo_screen(request: KYCUBORequest) -> Dict[str, Any]:
    """STUB: Mock watchlist/PEP/sanction screening."""
    return {
        "watchlist_match": False,
        "pep_match": False,
        "sanction_match": False,
        "screening_id": "SCR-001",
        "note": "STUB - integrate with real screening service",
    }


@mcp.tool()
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "legal-agent", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    from mcp_common.config import settings
    uvicorn.run(mcp.http_app(), host=settings.BIND_HOST, port=settings.LEGAL_AGENT_PORT)