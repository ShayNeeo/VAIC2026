"""Orchestrator MCP Client Hub — calls agent servers via MCP.

Replaces in-process calls in app/services/orchestrator.py with MCP client calls.
Keeps in-process fallback for resilience.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from fastmcp import Client as MCPClient

from mcp_common.config import settings
from mcp_common.schemas import SharedCaseState, ProductResult, EligibilityResult, OperationsResult

logger = logging.getLogger(__name__)


class MCPClientHub:
    """Central hub for calling all agent MCP servers."""

    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}
        self._fallback_agents = {}  # In-process fallbacks

    async def _get_client(self, service: str) -> Optional[MCPClient]:
        """Get or create MCP client for service."""
        if service in self._clients:
            return self._clients[service]

        port_map = {
            "product": settings.PRODUCT_AGENT_PORT,
            "legal": settings.LEGAL_AGENT_PORT,
            "operations": settings.OPERATIONS_AGENT_PORT,
            "approval": settings.APPROVAL_AGENT_PORT,
        }

        port = port_map.get(service)
        if not port:
            return None

        # Connect to local server (in production: via SSH tunnel to VPS)
        url = f"http://localhost:{port}/mcp"
        try:
            client = MCPClient(url)
            await client.connect()
            self._clients[service] = client
            logger.info(f"Connected to {service}-agent MCP at {url}")
            return client
        except Exception as e:
            logger.warning(f"Failed to connect to {service}-agent MCP: {e}")
            return None

    async def close(self):
        for client in self._clients.values():
            try:
                await client.disconnect()
            except Exception:
                pass

    # ===== Product Agent =====
    async def product_analyze(
        self,
        request_text: str,
        company_profile: Dict[str, Any],
        documents: List[Dict[str, Any]],
        trace_id: str,
    ) -> Dict[str, Any]:
        """Call product-agent MCP tool."""
        client = await self._get_client("product")
        if client:
            try:
                result = await client.call_tool(
                    "product_analyze",
                    {
                        "request": {
                            "request_text": request_text,
                            "company_profile": company_profile,
                            "documents": documents,
                            "trace_id": trace_id,
                        }
                    },
                )
                return result
            except Exception as e:
                logger.warning(f"Product MCP call failed, using fallback: {e}")

        # Fallback: in-process
        return self._fallback_product_analyze(request_text, company_profile, documents, trace_id)

    def _fallback_product_analyze(
        self,
        request_text: str,
        company_profile: Dict[str, Any],
        documents: List[Dict[str, Any]],
        trace_id: str,
    ) -> Dict[str, Any]:
        """In-process fallback using original ProductAgent."""
        try:
            from app.agents.product_agent import ProductAgent
            from app.rag.product_retriever import ProductRAGService
            from app.safety.guardrails import GuardrailGate
            from app.safety.evidence_validator import EvidenceValidator
            from app.schemas.state import SharedCaseState

            state = SharedCaseState(
                case_id=f"CORP-{trace_id}",
                customer_id=company_profile.get("customer_id", "UNKNOWN"),
                rm_id="fallback",
                customer_request={"text": request_text},
                company_profile=company_profile,
                documents=documents,
            )

            rag = ProductRAGService()
            agent = ProductAgent(rag)
            result = agent.run(state)

            guardrails = GuardrailGate()
            gr_result = guardrails.inspect_input(request_text, documents)

            validator = EvidenceValidator()
            val_result = validator.validate(state)

            return {
                "allowed": val_result["all_valid"],
                "result": {
                    **result,
                    "guardrail_verdict": {
                        "input_allowed": gr_result["allowed"],
                        "input_flags": gr_result["security_flags"],
                        "output_allowed": val_result["all_valid"],
                        "evidence_valid": val_result["all_valid"],
                        "evidence_valid_count": val_result["valid"],
                        "evidence_invalid_count": val_result["invalid"],
                    },
                },
                "trace_id": trace_id,
            }
        except Exception as e:
            logger.error(f"Fallback product analyze failed: {e}")
            return {"allowed": False, "error": "FALLBACK_FAILED", "trace_id": trace_id}

    # ===== Legal Agent =====
    async def legal_check(
        self,
        company_profile: Dict[str, Any],
        product_proposal: Dict[str, Any],
        documents: List[Dict[str, Any]],
        trace_id: str,
    ) -> EligibilityResult:
        client = await self._get_client("legal")
        if client:
            try:
                result = await client.call_tool(
                    "legal_check",
                    {
                        "request": {
                            "company_profile": company_profile,
                            "product_proposal": product_proposal,
                            "documents": documents,
                        }
                    },
                )
                return EligibilityResult(**result)
            except Exception as e:
                logger.warning(f"Legal MCP call failed: {e}")

        # Fallback: return minimal eligible=false (blocking)
        return EligibilityResult(
            eligible=False,
            failed_checks=[{"severity": "blocking", "rule": "MCP_UNAVAILABLE", "message": "Legal agent unavailable"}],
            blocking=True,
            evidence=[],
            missing_documents=["Legal agent unavailable"],
        )

    async def kyc_ubo_screen(
        self,
        company_profile: Dict[str, Any],
        trace_id: str,
    ) -> Dict[str, Any]:
        client = await self._get_client("legal")
        if client:
            try:
                return await client.call_tool("kyc_ubo_screen", {"request": {"company_profile": company_profile}})
            except Exception as e:
                logger.warning(f"KYC MCP call failed: {e}")
        return {"watchlist_match": True, "note": "fallback - manual review required"}

    # ===== Operations Agent =====
    async def ops_plan(
        self,
        product_result: Dict[str, Any],
        legal_result: Dict[str, Any],
        sop: Dict[str, Any],
        trace_id: str,
    ) -> OperationsResult:
        client = await self._get_client("operations")
        if client:
            try:
                result = await client.call_tool(
                    "ops_plan",
                    {
                        "request": {
                            "product_result": product_result,
                            "legal_result": legal_result,
                            "sop": sop,
                        }
                    },
                )
                return OperationsResult(**result)
            except Exception as e:
                logger.warning(f"Ops MCP call failed: {e}")

        return OperationsResult(
            checklist=[{"item": "MCP unavailable", "status": "pending"}],
            case_task_draft={"error": "Operations agent unavailable"},
            email_draft=None,
            sla_deadline=None,
        )

    # ===== Approval Agent =====
    async def issue_approval_token(
        self,
        case_id: str,
        rm_id: str,
        permissions: List[str],
        payload: Dict[str, Any],
        trace_id: str,
    ) -> Dict[str, Any]:
        client = await self._get_client("approval")
        if client:
            try:
                return await client.call_tool(
                    "issue_token",
                    {"request": {"case_id": case_id, "rm_id": rm_id, "permissions": permissions, "payload": payload}},
                )
            except Exception as e:
                logger.warning(f"Approval MCP call failed: {e}")

        # Fallback: use in-process ApprovalService
        from app.services.approval import ApprovalService
        token = ApprovalService.issue(case_id, rm_id)
        return {"token": token, "expires_in": settings.APPROVAL_TOKEN_TTL_SECONDS}

    async def verify_approval_token(
        self,
        token: str,
        case_id: str,
        rm_id: str,
        payload: Dict[str, Any],
        trace_id: str,
    ) -> Dict[str, Any]:
        client = await self._get_client("approval")
        if client:
            try:
                return await client.call_tool(
                    "verify_token",
                    {"request": {"token": token, "case_id": case_id, "rm_id": rm_id, "payload": payload}},
                )
            except Exception as e:
                logger.warning(f"Approval verify MCP failed: {e}")

        from app.services.approval import ApprovalService, ApprovalTokenError
        try:
            ApprovalService.verify(token, case_id, rm_id)
            return {"valid": True}
        except ApprovalTokenError as e:
            return {"valid": False, "reason": str(e)}


# Global instance
_mcp_hub: Optional[MCPClientHub] = None


def get_mcp_hub() -> MCPClientHub:
    global _mcp_hub
    if _mcp_hub is None:
        _mcp_hub = MCPClientHub()
    return _mcp_hub