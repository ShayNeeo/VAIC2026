"""Test Operations Agent stub contract (V3 signature)."""

import pytest
from servers.operations_agent.server import ops_plan, health_check, OpsPlanRequest


class TestOperationsAgentContract:
    @pytest.mark.asyncio
    async def test_ops_01_ops_plan_returns_operations_result(self):
        """OPS-01: ops_plan returns OperationsResult schema."""
        result = await ops_plan(OpsPlanRequest(
            product_result={"recommended_products": ["PROD-PAYROLL"]},
            legal_result={"eligible": True},
            sop={},
        ))
        assert "checklist" in result
        assert "case_task_draft" in result
        assert "email_draft" in result
        assert "sla_deadline" in result

    @pytest.mark.asyncio
    async def test_health_check(self):
        result = await health_check()
        assert result["status"] == "ok"
        assert result["service"] == "operations-agent"
