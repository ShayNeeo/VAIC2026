"""Test Operations Agent stub contract."""

import pytest
from servers.operations_agent.server import ops_plan, health_check


class TestOperationsAgentContract:
    @pytest.mark.asyncio
    async def test_ops_01_ops_plan_returns_operations_result(self):
        """OPS-01: ops_plan returns OperationsResult schema."""
        result = await ops_plan({
            "product_result": {"recommended_products": ["PROD-PAYROLL"]},
            "legal_result": {"eligible": True},
            "sop": {},
        })
        assert "result" in result
        res = result["result"]
        assert "checklist" in res
        assert "case_task_draft" in res
        assert "email_draft" in res
        assert "sla_deadline" in res
        assert res["schema_version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_health_check(self):
        result = await health_check()
        assert result["status"] == "ok"
        assert result["service"] == "operations-agent"