"""Test Legal Agent stub contract."""

import pytest
from servers.legal_agent.server import legal_check, kyc_ubo_screen, health_check


class TestLegalAgentContract:
    @pytest.mark.asyncio
    async def test_lgl_01_legal_check_returns_eligibility_result(self):
        """LGL-01: legal_check returns EligibilityResult schema."""
        result = await legal_check({
            "company_profile": {"customer_id": "COMP-ABC"},
            "product_proposal": {"recommended_products": ["PROD-PAYROLL"]},
            "documents": [],
        })
        assert result["allowed"] is True
        assert "result" in result
        res = result["result"]
        assert "eligible" in res
        assert "failed_checks" in res
        assert "missing_documents" in res
        assert "evidence" in res
        assert res["schema_version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_lgl_02_kyc_ubo_screen_returns_status(self):
        """LGL-02: kyc_ubo_screen returns watchlist/PEP status."""
        result = await kyc_ubo_screen({"company_profile": {}})
        assert "kyc_status" in result
        assert "pep_match" in result
        assert "sanction_match" in result
        assert "watchlist_hits" in result

    @pytest.mark.asyncio
    async def test_health_check(self):
        result = await health_check()
        assert result["status"] == "ok"
        assert result["service"] == "legal-agent"