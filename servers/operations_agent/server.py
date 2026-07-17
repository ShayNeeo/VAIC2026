"""Operations Agent MCP Server — STUB for team to fill.

Contract only: returns OperationsResult schema.
"""

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


mcp = FastMCP("operations-agent")


class OpsPlanRequest(BaseModel):
    product_result: Dict[str, Any]
    legal_result: Dict[str, Any]
    sop: Dict[str, Any] = Field(default_factory=dict)


@mcp.tool()
async def ops_plan(request: OpsPlanRequest) -> Dict[str, Any]:
    """STUB: Return mock checklist, case/task draft, email draft."""
    return {
        "checklist": [
            {"item": "Giấy đăng ký kinh doanh", "status": "received"},
            {"item": "Danh sách nhân viên", "status": "pending"},
            {"item": "Quyết định ủy quyền", "status": "pending"},
            {"item": "Báo cáo tài chính", "status": "pending"},
        ],
        "case_task_draft": {
            "case_type": "Corporate_Onboarding",
            "priority": "normal",
            "products": ["PROD-PAYROLL", "PROD-CASH-MGMT"],
            "assigned_to": "Ops_Team",
        },
        "email_draft": "Kính gửi Quý khách,\n\nCảm ơn Quý khách đã quan tâm đến giải pháp Payroll & Cash Management của SHB...\n\nTrân trọng,\nSHB Operations",
        "sla_deadline": "2026-07-20T17:00:00Z",
        "schema_version": "2.0.0",
        "note": "STUB - replace with real SOP/checklist logic",
    }


@mcp.tool()
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "operations-agent", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    from mcp_common.config import settings
    uvicorn.run(mcp.http_app(), host=settings.BIND_HOST, port=settings.OPERATIONS_AGENT_PORT)