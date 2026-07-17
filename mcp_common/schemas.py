"""Pydantic schemas mirroring V3 Data Blueprint contracts for MCP mesh."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Literal, Union
from pydantic import BaseModel, Field, field_validator
import uuid


# =============================================================================
# V3 Enums & Constants
# =============================================================================

from enum import Enum


class DataTier(str, Enum):
    """V3 Data tier classification."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class IntentType(str, Enum):
    """V3 Intent types from blueprint §5.1."""
    FIND_PRODUCT = "find_product"
    CHECK_ELIGIBILITY = "check_eligibility"
    PREPARE_CASE = "prepare_case"
    APPROVE_ACTIONS = "approve_actions"
    STATUS_LOOKUP = "status_lookup"
    OUT_OF_SCOPE = "out_of_scope"


class CaseStatus(str, Enum):
    """V3 Case status machine from blueprint §8.3."""
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


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ValidationMethod(str, Enum):
    EXACT_MATCH = "exact_match"
    SEMANTIC_SUPPORT = "semantic_support"
    NUMERIC_EXACT = "numeric_exact"
    HYBRID = "hybrid"


class ConfidenceSource(str, Enum):
    AUTHENTICATED_IAM = "authenticated_iam"
    WORKSPACE_SELECTED = "workspace_selected"
    FRESH_CRM_DMS = "fresh_crm_dms"
    USER_EXPLICIT = "user_explicit"
    WORKFLOW_STATE = "workflow_state"
    LLM_INFERENCE = "llm_inference"


# =============================================================================
# Core Contracts
# =============================================================================

class ResolvedValue(BaseModel):
    """Provenance contract for auto-filled/inferred fields (V3 §3)."""
    value: Any
    source_type: ConfidenceSource
    source_id: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    confirmed: bool = False
    observed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None


class EvidenceItem(BaseModel):
    """Evidence contract - every important claim must have one (V3 §3.4)."""
    claim_id: str = Field(default_factory=lambda: f"EVID-{uuid.uuid4().hex[:8]}")
    agent: Literal["Product", "Legal", "Operations"]
    claim: str
    source_document_id: str
    source_version: str
    section_or_page: str
    quote: str
    validation_method: ValidationMethod
    is_valid: bool = False
    validation_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ErrorContract(BaseModel):
    """Standardized error response across all MCP tools (V3 §3.5)."""
    error_code: str
    message: str
    retryable: bool
    safe_to_retry: bool
    correlation_id: str
    details: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Product Agent Contracts (V3 §5, §8.2)
# =============================================================================

class ProductPrerequisite(BaseModel):
    """Product prerequisite document."""
    document_type: str
    required: bool
    description: Optional[str] = None


class ProductFeeLimit(BaseModel):
    """Product fee or limit with unit."""
    name: str
    value: float
    unit: str  # "%", "VND", "bps", etc.
    condition: Optional[str] = None


class ProductCatalogEntry(BaseModel):
    """V3 Product catalog entry structure (§8.2, §9.3)."""
    product_id: str
    name: str
    description: str
    segment: str  # corporate, sme, retail
    category: str  # transaction_services, credit, cash_management, payroll
    fees_limits: List[ProductFeeLimit] = Field(default_factory=list)
    prerequisites: List[ProductPrerequisite] = Field(default_factory=list)
    eligibility_rules: str
    benefits: List[str] = Field(default_factory=list)
    # Metadata for citation & versioning
    source_document_id: str
    source_section: str
    effective_date: str
    expiry_date: Optional[str] = None
    owner: str = "Product Team"
    version: str = "1.0"
    data_tier: DataTier = DataTier.A  # V3 §9.2 Tier A


class ProductMatchScore(BaseModel):
    """Deterministic match score components (V3 §7)."""
    intent_fit: float = Field(ge=0.0, le=1.0)
    segment_fit: float = Field(ge=0.0, le=1.0)
    size_revenue_fit: float = Field(ge=0.0, le=1.0)
    workflow_signal: float = Field(ge=0.0, le=1.0)
    missing_prerequisites: float = Field(ge=0.0, le=1.0)
    legal_blocking: float = Field(ge=0.0, le=1.0)
    total: float = Field(ge=0.0, le=1.0)


class ProductRecommendation(BaseModel):
    """Single product recommendation with evidence."""
    product_id: str
    name: str
    match_score: ProductMatchScore
    matching_reason: str
    prerequisites: List[ProductPrerequisite]
    retrieval_score: Optional[float] = None
    evidence: List[EvidenceItem] = Field(default_factory=list)


class ProductBundle(BaseModel):
    """Recommended product bundle."""
    bundle_name: str
    products: List[ProductRecommendation]
    bundle_reason: str


class ProductResult(BaseModel):
    """Product Agent output contract (V3 §8.2)."""
    recommended_bundle: ProductBundle
    recommended_products: List[str]
    missing_parameters: List[str]
    retrieval_query: str
    citations: List[EvidenceItem]
    guardrail_verdict: Dict[str, Any]
    schema_version: str = "3.0.0"


# =============================================================================
# Legal Agent Contracts (V3 §8.2)
# =============================================================================

class EligibilityIssue(BaseModel):
    """Single eligibility check result."""
    rule_id: str
    rule_name: str
    severity: Literal["blocking", "warning", "info"]
    passed: bool
    message: str
    evidence_ref: Optional[str] = None


class EligibilityResult(BaseModel):
    """Legal Agent output contract."""
    eligible: bool
    failed_checks: List[EligibilityIssue]
    blocking: bool
    evidence: List[EvidenceItem]
    missing_documents: List[str]
    schema_version: str = "3.0.0"


# =============================================================================
# Operations Agent Contracts (V3 §8.2)
# =============================================================================

class ChecklistItem(BaseModel):
    """Operations checklist item."""
    item: str
    required: bool
    status: Literal["received", "pending", "missing", "waived"]
    source_document_id: Optional[str] = None


class CaseTaskDraft(BaseModel):
    """Draft case/task for CRM."""
    case_type: str
    priority: Literal["low", "normal", "high", "critical"]
    products: List[str]
    assigned_to: str
    sla_deadline: Optional[str] = None


class OperationsResult(BaseModel):
    """Operations Agent output contract."""
    checklist: List[ChecklistItem]
    case_task_draft: CaseTaskDraft
    email_draft: Optional[str] = None
    sla_deadline: Optional[str] = None
    deduplication_applied: bool = False
    reused_artifacts: List[str] = Field(default_factory=list)
    schema_version: str = "3.0.0"


# =============================================================================
# Intent & Context Contracts (V3 §4, §5)
# =============================================================================

class IntentSlot(BaseModel):
    """Single intent slot with provenance."""
    name: str
    value: Optional[Any] = None
    source: ConfidenceSource
    confidence: float = Field(ge=0.0, le=1.0)
    confirmed: bool = False
    evidence_span: Optional[str] = None


class IntentResult(BaseModel):
    """Structured intent output (V3 §5.1)."""
    intent_type: IntentType
    sub_intents: List[IntentType] = Field(default_factory=list)
    target_entities: List[str] = Field(default_factory=list)
    action_required: Optional[str] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)
    success_criteria: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    missing_slots: List[str] = Field(default_factory=list)
    ambiguity_notes: List[str] = Field(default_factory=list)
    evidence_spans: List[str] = Field(default_factory=list)
    field_confidence: Dict[str, float] = Field(default_factory=dict)
    risk_level: RiskLevel = "low"


class ContextSnapshot(BaseModel):
    """V3 Context Snapshot - 8 layers (§4.3)."""
    # Layer 1: Employee Identity
    employee_id: ResolvedValue
    role: ResolvedValue
    scope: ResolvedValue
    # Layer 2: UI Screen State
    screen: ResolvedValue
    selected_customer_id: ResolvedValue
    selected_case_id: ResolvedValue
    selected_task_id: ResolvedValue
    selected_product_id: ResolvedValue
    # Layer 3: Customer/Case Context
    customer_profile: ResolvedValue
    segment: ResolvedValue
    kyc_status: ResolvedValue
    products: ResolvedValue
    # Layer 4: Workflow State
    current_node: ResolvedValue
    open_questions: ResolvedValue
    task_artifact: ResolvedValue
    # Layer 5: Document Context
    documents: ResolvedValue
    # Layer 6: Conversation State
    goal: ResolvedValue
    confirmed_facts: ResolvedValue
    rejected_assumptions: ResolvedValue
    # Layer 7: Session/Preference
    language: ResolvedValue
    format_preference: ResolvedValue
    # Layer 8: User Settings
    brief_style: ResolvedValue
    email_format: ResolvedValue
    trace_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])


# =============================================================================
# Shared Case State (V3 §8.3)
# =============================================================================

class TaskItem(BaseModel):
    task_id: str
    owner: Literal["Product", "Legal", "Operations"]
    description: str
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    dependencies: List[str] = Field(default_factory=list)


class SharedCaseState(BaseModel):
    """Master state shared across all agents (V3 §8.3)."""
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

    risk_level: RiskLevel = "low"
    approval_status: Literal["pending", "approved", "rejected"] = "pending"
    final_status: CaseStatus = "new"
    audit_log: List[Dict[str, Any]] = Field(default_factory=list)
    trace_id: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str = "3.0.0"


# =============================================================================
# DTOs for API
# =============================================================================

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


class ApprovalToken(BaseModel):
    """HMAC-signed approval token claims (V3 §11)."""
    token_id: str
    case_id: str
    approver_id: str
    permissions: List[str]
    payload_hash: str
    issued_at: str
    expires_at: str
    nonce: str
    one_time_use: bool = True