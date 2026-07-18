"""Agent Knowledge Console contracts: lets a department Specialist feed,
update and retire the knowledge their own domain Agent (Product/Legal/
Credit) retrieves, and see what that Agent has been doing on cases in
their scope. Reuses the existing KnowledgeChunk/PersistentHybridIndex
storage (app/knowledge/index.py) and the existing three domain services
(ProductKnowledgeService/LegalKnowledgeService/OperationsKnowledgeService)
-- this module only adds the request/response shapes and the
role<->domain mapping; it does not introduce a new storage layer.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.v2.employee import RoleType

AgentDomain = Literal["product", "legal", "credit"]

# The one place role->domain->capability is decided. A specialist may only
# ever feed knowledge to their own domain's Agent -- never another
# department's -- matching this repo's existing pattern of a specialist's
# review_type having to equal their own role (see
# app/api/v2/employee_router.py::submit_specialist_review).
DOMAIN_BY_ROLE: Dict[RoleType, AgentDomain] = {
    RoleType.PRODUCT_SPECIALIST: "product",
    RoleType.LEGAL_SPECIALIST: "legal",
    RoleType.CREDIT_SPECIALIST: "credit",
}

MANAGE_CAPABILITY_BY_DOMAIN: Dict[AgentDomain, str] = {
    "product": "product:manage_knowledge",
    "legal": "legal:manage_knowledge",
    "credit": "credit:manage_knowledge",
}

_DEFAULT_CHUNK_TYPE: Dict[AgentDomain, str] = {
    "product": "product_overview",
    "legal": "legal_rule",
    "credit": "credit_policy_article",
}


def default_chunk_type(domain: AgentDomain) -> str:
    return _DEFAULT_CHUNK_TYPE[domain]


class KnowledgeEntryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1)
    section_path: str = Field(min_length=1)
    text: str = Field(min_length=3)
    document_id: Optional[str] = None
    chunk_type: Optional[str] = None
    effective_from: date
    effective_to: Optional[date] = None


class KnowledgeEntryUpdateRequest(BaseModel):
    """Updating `text` supersedes the existing chunk with a new versioned
    one (the old chunk is kept, marked is_superseded=True, and stays
    inspectable for audit -- never deleted). Setting `is_quarantined=True`
    retires an entry without creating a new version (the Agent must stop
    retrieving it, but nothing replaces it)."""

    model_config = ConfigDict(extra="forbid")

    text: Optional[str] = Field(default=None, min_length=3)
    effective_to: Optional[date] = None
    is_quarantined: Optional[bool] = None


class KnowledgeEntryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    domain: AgentDomain
    document_id: str
    document_version: str
    product_id: str
    section_path: str
    chunk_type: str
    text: str
    effective_from: date
    effective_to: Optional[date] = None
    is_superseded: bool
    is_quarantined: bool
    authority_tier: Optional[str] = None
    verification_status: Optional[str] = None
    contributed_by: Optional[str] = None
    contributed_at: Optional[datetime] = None


class AgentCaseActivityItem(BaseModel):
    """One case's summary of what this domain's Agent has produced on it
    -- deliberately a summary (counts/status), never the full grounding
    text, so this view stays a metadata dashboard and not a second copy of
    the case detail screen."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    case_status: str
    customer_id: str
    updated_at: datetime
    agent_has_run: bool
    agent_summary: Dict[str, Any] = Field(default_factory=dict)
    evidence_count: int
    last_ai_log_event: Optional[Dict[str, Any]] = None


class AgentActivitySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: AgentDomain
    generated_at: datetime
    knowledge_entry_count: int
    active_knowledge_entry_count: int
    cases: List[AgentCaseActivityItem]
