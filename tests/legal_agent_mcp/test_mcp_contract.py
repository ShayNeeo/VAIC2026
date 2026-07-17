"""MCP contract + compatibility tests for Legal Agent V2.

Ensures the Legal Agent MCP server is compatible with the orchestrator hub
(app/services/mcp_clients.py) and the V3 Product Agent result contract.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mcp_common.schemas import EligibilityResult  # noqa: E402
from servers.legal_agent.server_v2 import (  # noqa: E402
    legal_check,
    kyc_ubo_screen,
    health_check,
    _map_to_eligibility,
)
from app.legal.models import LegalCheckOutput  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_company():
    return {
        "customer_id": "COMP-ABC",
        "company_name": "Công ty TNHH ABC",
        "tax_code": "0101234567",
        "representative": {
            "name": "Nguyễn Văn A",
            "id_number": "001099000123",
            "position": "Giám đốc",
            "is_authorized": True,
        },
        "ubo_status": "complete",
    }


@pytest.fixture
def clean_documents():
    return [
        {"document_type_id": "BUSINESS_REGISTRATION", "is_expired": False},
        {"document_type_id": "FINANCIAL_STATEMENT", "is_expired": False},
        {"document_type_id": "UBO_DECLARATION", "is_expired": False},
    ]


@pytest.fixture
def product_proposal():
    return {
        "product_id": "PROD-PAYROLL",
        "name": "SHB Payroll",
    }


# ---------------------------------------------------------------------------
# MCP tool registration / signature
# ---------------------------------------------------------------------------

def test_mcp_tools_registered():
    """Server_v2 exposes the exact tools the orchestrator hub calls."""
    from mcp.server.fastmcp import FastMCP

    server = legal_check.__globals__["mcp"]
    assert isinstance(server, FastMCP)
    tools = server._tool_manager._tools
    assert "legal_check" in tools
    assert "kyc_ubo_screen" in tools
    assert "health_check" in tools


# ---------------------------------------------------------------------------
# legal_check contract (matches EligibilityResult)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_legal_check_passed_shape(sample_company, product_proposal, clean_documents):
    """LGL-01: clean company + valid product -> eligible=True, blocking=False."""
    req = type(
        "R",
        (),
        {
            "company_profile": sample_company,
            "product_proposal": product_proposal,
            "documents": clean_documents,
            "trace_id": "LGL-TRACE-1",
        },
    )()
    result = await legal_check(req)
    elig = EligibilityResult(**result)
    assert elig.eligible is True
    assert elig.blocking is False
    assert isinstance(elig.evidence, list)


@pytest.mark.asyncio
async def test_legal_check_watchlist_blocked():
    """LGL-02: sanctioned entity -> eligible=False, blocking=True."""
    sanctioned = {
        "customer_id": "COMP-SAN",
        "company_name": "Công ty TNHH X",
        "tax_code": "0301111111",  # matches synthetic_watchlist.json
        "representative": {"name": "", "id_number": ""},
        "ubo_status": "missing",
    }
    req = type(
        "R",
        (),
        {
            "company_profile": sanctioned,
            "product_proposal": {"product_id": "PROD-PAYROLL"},
            "documents": [],
            "trace_id": "LGL-TRACE-2",
        },
    )()
    result = await legal_check(req)
    elig = EligibilityResult(**result)
    assert elig.eligible is False
    assert elig.blocking is True


@pytest.mark.asyncio
async def test_legal_check_missing_info():
    """LGL-03: missing representative -> pending_information (blocking)."""
    incomplete = {
        "customer_id": "COMP-INC",
        "company_name": "Công ty TNHH Y",
        "tax_code": "0302222222",
        "representative": {},  # no name/id_number
        "ubo_status": "unknown",
    }
    req = type(
        "R",
        (),
        {
            "company_profile": incomplete,
            "product_proposal": {"product_id": "PROD-PAYROLL"},
            "documents": [],
            "trace_id": "LGL-TRACE-3",
        },
    )()
    result = await legal_check(req)
    elig = EligibilityResult(**result)
    # missing representative triggers pending_information -> blocking
    assert elig.blocking is True
    assert any("đại diện" in fc.message.lower() or "representative" in fc.rule_id.lower() for fc in elig.failed_checks)


# ---------------------------------------------------------------------------
# kyc_ubo_screen contract
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_kyc_ubo_screen_clean(sample_company):
    """LGL-04: clean company -> no watchlist/PEP/sanction match."""
    req = type("R", (), {"company_profile": sample_company, "documents": []})()
    result = await kyc_ubo_screen(req)
    assert result["watchlist_match"] is False
    assert "screening_id" in result


# ---------------------------------------------------------------------------
# health_check contract
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_check():
    """LGL-05: health endpoint returns ok status."""
    result = await health_check()
    assert result["status"] == "ok"
    assert result["service"] == "legal-agent-v2"


# ---------------------------------------------------------------------------
# _map_to_eligibility mapping
# ---------------------------------------------------------------------------

def test_map_to_eligibility_passed():
    out = LegalCheckOutput(
        eligibility_status="passed",
        failed_checks=[],
        missing_documents=[],
        citations=[{"claim": "OK", "source_document_id": "R1", "source_location": "§1", "quote": "x"}],
    )
    elig = _map_to_eligibility(out)
    assert elig.eligible is True
    assert elig.blocking is False
    assert len(elig.evidence) == 1


def test_map_to_eligibility_failed():
    out = LegalCheckOutput(
        eligibility_status="failed",
        failed_checks=[{"rule_id": "R1", "severity": "blocking", "reason": "bad"}],
        missing_documents=["doc X"],
        citations=[],
    )
    elig = _map_to_eligibility(out)
    assert elig.eligible is False
    assert elig.blocking is True
    assert elig.missing_documents == ["doc X"]
