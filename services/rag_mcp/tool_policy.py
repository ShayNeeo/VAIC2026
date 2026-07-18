"""Fail-closed MCP tool policy for each expert profile."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet

from services.rag_mcp.schemas import CallerPrincipal, ExpertAgentType, KnowledgeDomain


POLICY_VERSION = "2026.07-v3-credit"


@dataclass(frozen=True)
class ToolRule:
    agent_type: ExpertAgentType
    domain: KnowledgeDomain
    permission: str
    purpose: str
    read_only: bool = True


TOOL_RULES: Dict[str, ToolRule] = {
    "product_search": ToolRule(
        "ProductExpert", "product", "knowledge:product:read", "Tìm sản phẩm và solution bundle."
    ),
    "product_get_chunk": ToolRule(
        "ProductExpert", "product", "knowledge:product:read", "Đọc exact chunk sản phẩm."
    ),
    "product_list_sources": ToolRule(
        "ProductExpert", "product", "knowledge:product:read", "Liệt kê nguồn sản phẩm được duyệt."
    ),
    "legal_search": ToolRule(
        "LegalExpert", "legal", "knowledge:legal:read", "Tra policy, KYC và evidence pháp lý."
    ),
    "legal_get_chunk": ToolRule(
        "LegalExpert", "legal", "knowledge:legal:read", "Đọc exact chunk pháp lý."
    ),
    "legal_list_sources": ToolRule(
        "LegalExpert", "legal", "knowledge:legal:read", "Liệt kê nguồn pháp lý được duyệt."
    ),
    "credit_search": ToolRule(
        "CreditExpert", "credit", "knowledge:credit:read", "Tra chính sách cho vay và thẩm định tín dụng."
    ),
    "credit_get_chunk": ToolRule(
        "CreditExpert", "credit", "knowledge:credit:read", "Đọc exact chunk tín dụng."
    ),
    "credit_list_sources": ToolRule(
        "CreditExpert", "credit", "knowledge:credit:read", "Liệt kê nguồn tín dụng được duyệt."
    ),
    "evidence_get_chunk": ToolRule(
        "EvidenceExpert", "all", "knowledge:evidence:read", "Đọc exact chunk mà claim tham chiếu."
    ),
    "evidence_verify_citation": ToolRule(
        "EvidenceExpert", "all", "knowledge:evidence:read", "Đối chiếu ID, version và content hash."
    ),
    "rag_search": ToolRule(
        "KnowledgeAdmin", "all", "knowledge:admin", "Tìm kiếm liên miền cho corpus QA."
    ),
    "rag_get_chunk": ToolRule(
        "KnowledgeAdmin", "all", "knowledge:admin", "Đọc chunk bất kỳ trong phạm vi quản trị."
    ),
    "rag_list_sources": ToolRule(
        "KnowledgeAdmin", "all", "knowledge:admin", "Kiểm kê nguồn đang serving."
    ),
    "rag_health": ToolRule(
        "KnowledgeAdmin", "all", "knowledge:admin", "Kiểm tra health và ingestion."
    ),
}


PROFILE_ENDPOINTS = {
    "ProductExpert": "/mcp/product",
    "LegalExpert": "/mcp/legal",
    "CreditExpert": "/mcp/credit",
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

