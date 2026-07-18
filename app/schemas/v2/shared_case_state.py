"""Pydantic mirror of plan_v2/contracts/shared_case_state.schema.json."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import SCHEMA_VERSION
from .context_snapshot import ContextSnapshot
from .intent_result import IntentResult

Score = Annotated[float, Field(ge=0.0, le=1.0)]


class CaseStatus(str, Enum):
    """plan_v2/INDEX.md section 6 - the only status values allowed anywhere."""

    NEW = "new"
    UNDERSTANDING = "understanding"
    CLARIFICATION_REQUIRED = "clarification_required"
    PLANNED = "planned"
    IN_ANALYSIS = "in_analysis"
    PENDING_INFORMATION = "pending_information"
    PENDING_REVIEW = "pending_review"
    PENDING_APPROVAL = "pending_approval"
    EXECUTING = "executing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONSUMED = "consumed"


class Task(BaseModel):
    """$defs/task. dedup_key backs V2-010 dedup and input_hash/output_ref back resume."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    task_type: str
    owner: str
    status: TaskStatus
    dependencies: List[str]
    dedup_key: str
    input_hash: Optional[str] = None
    output_ref: Optional[str] = None


class Evidence(BaseModel):
    """$defs/evidence. Required for every important Product/Legal claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str
    module: str
    claim: str
    source_document_id: str
    source_version: str
    location: str
    quote: str
    is_valid: bool
    validation_score: Optional[Score] = None
    # Set from app.safety.evidence_validator.ValidationStatus (see
    # V2WorkflowEngine._product_evidence/_legal_evidence): True only for a
    # citation/grounding mismatch (the source document is current and
    # exists, but the quoted text was not found in it) -- a specialist can
    # independently re-verify the underlying claim against the real
    # document. False (default, and always for is_valid=True) for a
    # structural document problem -- expired source, version mismatch,
    # source not found, conflicting quotes -- none of which a human
    # override should bypass. See app/workflow/risk_gate.py.
    human_review_allowed: bool = False


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: str
    text: str
    received_at: datetime


class Workflow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_version: str
    current_node: Optional[str]
    tasks: List[Task]
    loop_count: int = Field(ge=0, le=3)
    resume_from_nodes: List[str] = Field(default_factory=list)


class Approval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ApprovalStatus
    approver_id: Optional[str] = None
    payload_hash: Optional[str] = None
    expires_at: Optional[datetime] = None


class SharedCaseState(BaseModel):
    """contracts/shared_case_state.schema.json — the single cross-module case record.

    plan_v2/03_SHARED_CONTRACTS.md section 6 restricts which node may write
    which section; this model only defines shape, not write ownership.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION, pattern=r"^2\.0\.0$")
    case_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    status: CaseStatus
    context: ContextSnapshot
    request: Request
    intent_result: Optional[IntentResult] = None
    workflow: Workflow
    product_result: Optional[Dict[str, Any]] = None
    eligibility_result: Optional[Dict[str, Any]] = None
    risk_gate_result: Optional[Dict[str, Any]] = None
    operations_result: Optional[Dict[str, Any]] = None
    customer_business_snapshot: Optional[Dict[str, Any]] = None
    execution_plan: Optional[Dict[str, Any]] = None
    next_best_questions: List[Dict[str, Any]] = Field(default_factory=list)
    next_best_actions: List[Dict[str, Any]] = Field(default_factory=list)
    ai_decision_log: List[Dict[str, Any]] = Field(default_factory=list)
    evidences: List[Evidence]
    approval: Approval
    audit_events: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
