"""Pydantic schemas mirroring contracts/shared_case_state.schema.json for MCP mesh."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class ResolvedValue(BaseModel):
    """Provenance contract for auto-filled/inferred fields."""
    value: Any
    source_type: Literal[
        "user_explicit", "workspace", "sso", "iam", "crm", "document",
        "workflow", "conversation_confirmed", "cache", "llm_inference"
    ]
    source_id: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    confirmed: bool = False
    observed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None


class EvidenceItem(BaseModel):
    """Evidence contract - every important claim must have one."""
    claim_id: str
    agent: Literal["Product", "Legal", "Operations"]
    claim: str
    source_document_id: str
    source_version: str
    section_or_page: str
    quote: str
    validation_method: Literal["exact_match", "semantic_support", "numeric_exact", "hybrid"]
    is_valid: bool = False
    validation_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ErrorContract(BaseModel):
    """Standardized error response across all MCP tools."""
    error_code: str
    message: str
    retryable: bool
    safe_to_retry: bool
    correlation_id: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ProductResult(BaseModel):
    """Product Agent output contract."""
    recommended_bundle: Dict[str, Any]
    recommended_products: List[str]
    missing_parameters: List[str]
    retrieval_query: str
    citations: List[EvidenceItem]
    guardrail_verdict: Dict[str, Any]
    schema_version: str = "2.0.0"


class EligibilityResult(BaseModel):
    """Legal Agent output contract."""
    eligible: bool
    failed_checks: List[Dict[str, Any]]
    blocking: bool
    evidence: List[EvidenceItem]
    missing_documents: List[str]
    schema_version: str = "2.0.0"


class OperationsResult(BaseModel):
    """Operations Agent output contract."""
    checklist: List[Dict[str, Any]]
    case_task_draft: Dict[str, Any]
    email_draft: Optional[str] = None
    sla_deadline: Optional[str] = None
    schema_version: str = "2.0.0"


class ApprovalToken(BaseModel):
    """HMAC-signed approval token claims."""
    token_id: str
    case_id: str
    approver_id: str
    permissions: List[str]
    payload_hash: str
    issued_at: str
    expires_at: str
    nonce: str
    one_time_use: bool = True


class TaskItem(BaseModel):
    task_id: str
    owner: Literal["Product", "Legal", "Operations"]
    description: str
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    dependencies: List[str] = Field(default_factory=list)


class SharedCaseState(BaseModel):
    """Master state shared across all agents (mirrors contracts/shared_case_state.schema.json)."""
    case_id: str
    customer_id: str
    rm_id: str
    customer_request: Dict[str, Any] = Field(default_factory=dict)
    company_profile: Dict[str, Any] = Field(default_factory=dict)
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    execution_plan: List[TaskItem] = Field(default_factory=list)

    product_result: Dict[str, Any] = Field(default_factory=dict)
    legal_result: Dict[str, Any] = Field(default_factory=dict)
    operations_result: Dict[str, Any] = Field(default_factory=dict)

    missing_information: List[str] = Field(default_factory=list)
    evidences: List[EvidenceItem] = Field(default_factory=list)

    risk_level: Literal["low", "medium", "high"] = "low"
    approval_status: Literal["pending", "approved", "rejected"] = "pending"
    final_status: Literal["new", "understanding", "clarification_required", "planned", "in_analysis", "pending_information", "pending_review", "pending_approval", "executing", "completed", "rejected", "failed"] = "new"

    audit_log: List[Dict[str, Any]] = Field(default_factory=list)
    trace_id: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str = "2.0.0"


# DTOs for API
class CreateCaseRequest(BaseModel):
    customer_id: str
    rm_id: str
    request_text: str
    documents: List[Dict[str, Any]] = Field(default_factory=list)


class ResumeCaseRequest(BaseModel):
    rm_id: str
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    company_profile_updates: Dict[str, Any] = Field(default_factory=dict)


class ApproveCaseRequest(BaseModel):
    rm_id: str
    comments: Optional[str] = None


class RejectCaseRequest(BaseModel):
    rm_id: str
    reason: str