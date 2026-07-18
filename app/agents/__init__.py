"""Governed multi-agent collaboration package.

Deliberately does NOT eagerly import concrete agent runtimes
(CreditExpertAgent/ProductExpertAgent/LegalComplianceAgent/...) here.
Each of those pulls in its domain KnowledgeService, which imports
app.data_catalog.registry, which imports app.schemas.v2 (for
DataSourceCard) -- and app.schemas.v2.shared_case_state imports
app.agents.contracts, re-entering this package's __init__ before it has
finished running. That import cycle is real (see git history / any
standalone `import app.agents.X` that doesn't first warm up
app.schemas.v2), not hypothetical -- every call site in this repo already
imports concrete agents from their own submodule
(`from app.agents.credit_expert import CreditExpertAgent`, etc.), never
via this package's namespace, so re-exporting them here bought nothing.
"""

from .contracts import AgentType, ExpertFinding, TaskAssignment

__all__ = [
    "AgentType",
    "ExpertFinding",
    "TaskAssignment",
]
