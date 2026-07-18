"""Governed multi-agent collaboration package."""

from .contracts import AgentType, ExpertFinding, TaskAssignment
from .credit_expert import CreditExpertAgent
from .legal_expert import LegalComplianceAgent
from .product_expert import ProductExpertAgent

__all__ = [
    "AgentType",
    "ExpertFinding",
    "TaskAssignment",
    "ProductExpertAgent",
    "LegalComplianceAgent",
    "CreditExpertAgent",
]
