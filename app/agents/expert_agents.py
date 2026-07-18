"""Compatibility exports for the independently implemented expert runtimes."""

from app.agents.base import BaseExpertRuntime
from app.agents.credit_expert import CreditExpertAgent
from app.agents.legal_expert import LegalComplianceAgent
from app.agents.product_expert import ProductExpertAgent

# Keep the old base import usable for extensions without preserving the old
# CoT-oriented implementation.
BaseLLMAgent = BaseExpertRuntime

__all__ = [
    "BaseExpertRuntime",
    "BaseLLMAgent",
    "ProductExpertAgent",
    "LegalComplianceAgent",
    "CreditExpertAgent",
]
