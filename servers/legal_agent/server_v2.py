"""Legal Agent MCP Server V2 (aligned with V3 Product Agent MCP mesh).

Wraps the friend's LegalAgentV2 (deterministic rule engine + Legal RAG) and
exposes it as an MCP tool compatible with the orchestrator hub in
app/services/mcp_clients.py (legal_check / kyc_ubo_screen / health_check).

Contract:
- legal_check returns mcp_common.schemas.EligibilityResult
- port = settings.LEGAL_AGENT_PORT (8005), transport streamable-http (/mcp)
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Any, Dict, List

from app.schemas.state import SharedCaseState
from app.legal.adapter import LegalAgentV2
from app.legal.tools import screen_watchlist, check_representative_and_ubo
from app.legal.models import LegalCheckOutput
from mcp_common.config import settings
from mcp_common.schemas import EligibilityResult, EvidenceItem, EligibilityIssue


mcp = FastMCP(
    "legal-agent-v2",
    host=settings.BIND_HOST,
    port=settings.LEGAL_AGENT_PORT,
)


class LegalCheckRequest(BaseModel):
    company_profile: Dict[str, Any]
    product_proposal: Dict[str, Any]
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    trace_id: str = ""


class KYCUBORequest(BaseModel):
    company_profile: Dict[str, Any]
    documents: List[Dict[str, Any]] = Field(default_factory=list)


def _map_to_eligibility(output: LegalCheckOutput) -> EligibilityResult:
    """Map LegalCheckOutput (friend's contract) to V3 EligibilityResult."""
    status = output.eligibility_status
    blocking = status in ("failed", "pending_review", "pending_information")

    failed_checks = []
    for rule in output.failed_checks:
        failed_checks.append(EligibilityIssue(
            rule_id=rule.get("rule_id", rule.get("rule", "UNKNOWN")),
            rule_name=rule.get("rule_name", rule.get("rule", "")),
            severity=rule.get("severity", "blocking"),
            passed=False,
            message=rule.get("reason", rule.get("message", "")),
        ))

    evidence = []
    for c in output.citations:
        quote = c.get("quote", c.get("evidence_quote", ""))
        if not quote and c.get("source_document_id"):
            quote = f"Ref: {c['source_document_id']}"
        evidence.append(EvidenceItem(
            claim_id=c.get("claim_id", f"EVID-{len(evidence)+1:03d}"),
            agent="Legal",
            claim=c.get("claim", c.get("rule_name", "compliance check")),
            source_document_id=c.get("source_document_id", "ComplianceRules"),
            source_version=c.get("source_version", "2026.1"),
            section_or_page=c.get("source_location", c.get("section", "")),
            quote=quote,
            validation_method="semantic_support",
            is_valid=(status == "passed"),
        ))

    return EligibilityResult(
        eligible=(status == "passed"),
        failed_checks=failed_checks,
        blocking=blocking,
        evidence=evidence,
        missing_documents=output.missing_documents,
    )


@mcp.tool()
async def legal_check(request: LegalCheckRequest) -> Dict[str, Any]:
    """Execute full Legal Agent V2 eligibility check.

    Input: company profile, proposed product, supporting documents.
    Output: EligibilityResult (eligible, failed_checks, blocking, evidence,
    missing_documents) compatible with the orchestrator MCP hub.
    """
    agent = LegalAgentV2()

    state = SharedCaseState(
        case_id=request.trace_id or "case-mcp",
        customer_id=request.company_profile.get("customer_id", "unknown"),
        rm_id="mcp-user",
        company_profile=request.company_profile,
        documents=request.documents,
        product_result={"recommended_products": [request.product_proposal]} if request.product_proposal else {},
    )

    output = LegalCheckOutput(**agent.run(state))
    result = _map_to_eligibility(output)
    return result.model_dump()


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
async def health_check() -> Dict[str, Any]:
    return {"status": "ok", "service": "legal-agent-v2", "version": "2.0.0"}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
