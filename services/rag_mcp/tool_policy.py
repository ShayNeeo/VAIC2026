"""Fail-closed MCP tool policy for each Expert Agent profile."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet

from services.rag_mcp.schemas import CallerPrincipal, ExpertAgentType, KnowledgeDomain


POLICY_VERSION = "2026.07-v2"


@dataclass(frozen=True)
class ToolRule:
    agent_type: ExpertAgentType
    domain: KnowledgeDomain
    permission: str
    purpose: str
    read_only: bool = True


TOOL_RULES: Dict[str, ToolRule] = {
    "product_search": ToolRule(
        "ProductExpert", "product", "knowledge:product:read", "Tìm sản phẩm, biểu phí và solution bundle."
    ),
    "product_get_chunk": ToolRule(
        "ProductExpert", "product", "knowledge:product:read", "Đọc lại một chunk sản phẩm đã được truy xuất."
    ),
    "product_list_sources": ToolRule(
        "ProductExpert", "product", "knowledge:product:read", "Liệt kê nguồn sản phẩm được phê duyệt."
    ),
    "legal_search": ToolRule(
        "LegalExpert", "legal", "knowledge:legal:read", "Tra cứu policy, KYC và evidence pháp lý."
    ),
    "legal_get_chunk": ToolRule(
        "LegalExpert", "legal", "knowledge:legal:read", "Đọc lại một chunk pháp lý đã được truy xuất."
    ),
    "legal_list_sources": ToolRule(
        "LegalExpert", "legal", "knowledge:legal:read", "Liệt kê nguồn pháp lý được phê duyệt."
    ),
    "operations_search": ToolRule(
        "OperationsExpert", "operations", "knowledge:operations:read", "Tra cứu SOP, checklist, SLA và template."
    ),
    "operations_get_chunk": ToolRule(
        "OperationsExpert", "operations", "knowledge:operations:read", "Đọc lại một chunk vận hành đã được truy xuất."
    ),
    "operations_list_sources": ToolRule(
        "OperationsExpert", "operations", "knowledge:operations:read", "Liệt kê nguồn vận hành được phê duyệt."
    ),
    "evidence_get_chunk": ToolRule(
        "EvidenceExpert", "all", "knowledge:evidence:read", "Đọc chính xác chunk được claim tham chiếu."
    ),
    "evidence_verify_citation": ToolRule(
        "EvidenceExpert", "all", "knowledge:evidence:read", "Đối chiếu ID, version và content hash của citation."
    ),
    "rag_search": ToolRule(
        "KnowledgeAdmin", "all", "knowledge:admin", "Tìm kiếm liên miền để kiểm thử/quản trị corpus."
    ),
    "rag_get_chunk": ToolRule(
        "KnowledgeAdmin", "all", "knowledge:admin", "Đọc chunk bất kỳ trong phạm vi quản trị."
    ),
    "rag_list_sources": ToolRule(
        "KnowledgeAdmin", "all", "knowledge:admin", "Kiểm kê toàn bộ nguồn đang serving."
    ),
    "rag_health": ToolRule(
        "KnowledgeAdmin", "all", "knowledge:admin", "Kiểm tra health, index và ingestion."
    ),
}


PROFILE_ENDPOINTS = {
    "ProductExpert": "/mcp/product",
    "LegalExpert": "/mcp/legal",
    "OperationsExpert": "/mcp/operations",
    "EvidenceExpert": "/mcp/evidence",
    "KnowledgeAdmin": "/mcp",
}


def tools_for(agent_type: ExpertAgentType) -> FrozenSet[str]:
    return frozenset(name for name, rule in TOOL_RULES.items() if rule.agent_type == agent_type)


def authorize_tool(principal: CallerPrincipal, tool_name: str) -> ToolRule:
    rule = TOOL_RULES.get(tool_name)
    if rule is None:
        raise PermissionError(f"tool is not registered in policy: {tool_name}")
    if principal.agent_type != rule.agent_type:
        raise PermissionError(
            f"{principal.agent_type} is not allowed to call {tool_name}; required={rule.agent_type}"
        )
    if rule.permission not in set(principal.permissions):
        raise PermissionError(f"missing exact permission {rule.permission} for {tool_name}")
    if principal.agent_type == "KnowledgeAdmin" and not {
        "KnowledgeAdmin",
        "DataSteward",
    }.intersection(principal.roles):
        raise PermissionError("KnowledgeAdmin tools require KnowledgeAdmin or DataSteward role")
    return rule
