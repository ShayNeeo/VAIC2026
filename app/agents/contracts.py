"""Typed, provider-neutral contracts for governed expert collaboration.

These models mirror ``plan_v2/contracts/agent_collaboration.schema.json``.
They deliberately expose concise rationale and provenance, never hidden
chain-of-thought or raw prompts.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


CONTRACT_VERSION = "1.0.0"


def canonical_hash(value: Any) -> str:
    """Return a stable, prefix-free SHA-256 used by collaboration contracts."""

    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AgentType(str, Enum):
    PLANNER_COORDINATOR = "PlannerCoordinator"
    PRODUCT_EXPERT = "ProductExpert"
    # LEGAL_EXPERT is kept for backward-compat with any persisted
    # TaskAssignment/ExpertFinding that still names it (and with
    # app/agents/legal_expert.py, not deleted -- see coordinator/graph
    # comments) but the live collaboration graph no longer dispatches to
    # it: eligibility is now a plain deterministic graph step, and
    # InsuranceExpert is the third independent expert alongside
    # Product/Credit.
    LEGAL_EXPERT = "LegalExpert"
    CREDIT_EXPERT = "CreditExpert"
    INSURANCE_EXPERT = "InsuranceExpert"
    EVIDENCE_VALIDATOR = "EvidenceValidator"


class StopReason(str, Enum):
    COMPLETED = "completed"
    NEEDS_ASSISTANCE = "needs_assistance"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    HARD_BLOCK = "hard_block"
    TIMEOUT = "timeout"
    FALLBACK = "fallback"


class SupportStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTRADICTED = "contradicted"
    STALE = "stale"
    UNAUTHORIZED = "unauthorized"
    MISSING = "missing"


class AgentManifest(BaseModel):
    """Immutable authorization identity; the model cannot edit this object."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    agent_type: AgentType
    manifest_version: str = "1.0.0"
    objective: str
    accepted_task_types: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    forbidden_decisions: tuple[str, ...]
    output_schema: str = "ExpertFinding/1.0.0"
    max_tool_calls: int = Field(default=6, ge=0, le=20)
    timeout_ms: int = Field(default=20_000, ge=100, le=120_000)
    fallback_policy: str


class ArtifactRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_id: str
    artifact_type: str
    schema_version: str
    content_hash: str = Field(pattern=r"^[a-fA-F0-9]{64}$")


class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: str
    chunk_id: str
    document_id: str
    document_version: str
    content_hash: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    location: Optional[str] = None
    quote: Optional[str] = None
    support_status: SupportStatus = SupportStatus.SUPPORTED


class ConfidenceBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_coverage: float = Field(ge=0.0, le=1.0)
    source_authority: Literal[
        "A_INTERNAL", "A_OFFICIAL", "B_LICENSED", "C_OPEN", "D_DERIVED", "E_SYNTHETIC", "UNKNOWN"
    ] = "UNKNOWN"
    freshness_status: Literal["current", "warning", "stale", "blocked", "unknown"] = "unknown"
    retrieval_quality: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    consistency_status: Literal["consistent", "conflicting", "unresolved", "not_checked"] = "not_checked"
    rule_certainty: Literal["deterministic", "not_applicable", "unknown"] = "unknown"
    input_completeness: float = Field(ge=0.0, le=1.0)
    display_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    calibration_policy_version: Optional[str] = None


class AgentRunMetadata(BaseModel):
    """Sanitized operational metadata; excludes raw prompts, secrets and PII."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    model: str
    mode: Literal["llm", "deterministic_fallback"]
    prompt_version: str
    output_schema_version: str = CONTRACT_VERSION
    manifest_version: str
    tool_policy_version: str
    tools_called: tuple[str, ...] = ()
    denied_tools: tuple[str, ...] = ()
    latency_ms: int = Field(ge=0)
    fallback_reason: Optional[str] = None
    output_hash: str = Field(pattern=r"^[a-fA-F0-9]{64}$")


class TaskAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0"] = CONTRACT_VERSION
    message_type: Literal["TaskAssignment"] = "TaskAssignment"
    task_id: str
    case_id: str
    trace_id: str
    assigned_by: Literal["PlannerCoordinator"] = "PlannerCoordinator"
    assigned_to: AgentType
    task_type: str
    objective: str = Field(min_length=3)
    input_refs: tuple[ArtifactRef, ...] = ()
    constraints: tuple[str, ...] = ()
    allowed_tool_names: tuple[str, ...] = ()
    round: int = Field(default=0, ge=0, le=3)
    deadline_at: datetime
    input_hash: str = Field(pattern=r"^[a-fA-F0-9]{64}$")


class ExpertFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0"] = CONTRACT_VERSION
    message_type: Literal["ExpertFinding"] = "ExpertFinding"
    finding_id: str
    case_id: str
    trace_id: str
    task_id: str
    agent_type: AgentType
    agent_manifest_version: str
    revision: int = Field(ge=1, le=3)
    parent_finding_id: Optional[str] = None
    conclusion: str
    decision_rationale_summary: tuple[str, ...] = Field(default=(), max_length=8)
    known_facts: tuple[Dict[str, Any], ...] = ()
    inferences: tuple[Dict[str, Any], ...] = ()
    unknowns: tuple[Dict[str, Any], ...] = ()
    assumptions: tuple[Dict[str, Any], ...] = ()
    recommendations: tuple[Dict[str, Any], ...] = ()
    constraints: tuple[Dict[str, Any], ...] = ()
    evidence_refs: tuple[EvidenceReference, ...] = ()
    confidence: ConfidenceBreakdown
    assistance_request_ids: tuple[str, ...] = ()
    fallback_used: bool = False
    output_hash: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    stop_reason: StopReason
    agent_run: AgentRunMetadata
    domain_result: Dict[str, Any] = Field(default_factory=dict)


class AssistanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0"] = CONTRACT_VERSION
    message_type: Literal["AssistanceRequest"] = "AssistanceRequest"
    request_id: str
    case_id: str
    trace_id: str
    from_agent: AgentType
    target_agent: AgentType
    question_type: str
    question: str = Field(min_length=3)
    input_refs: tuple[ArtifactRef, ...] = ()
    constraints: tuple[str, ...] = ()
    expected_output: Literal["ExpertFinding"] = "ExpertFinding"
    priority: Literal["normal", "high"] = "normal"
    dedup_key: str
    round: int = Field(ge=1, le=3)


class ConstraintNotice(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0"] = CONTRACT_VERSION
    message_type: Literal["ConstraintNotice"] = "ConstraintNotice"
    constraint_id: str
    case_id: str
    trace_id: str
    issued_by: Literal["LegalExpert", "EvidenceValidator", "PlannerCoordinator"]
    constraint_type: Literal[
        "hard_rule", "missing_information", "access", "stale_source", "conflict", "operational_dependency"
    ]
    severity: Literal["blocking", "review", "warning"]
    description: str
    evidence_refs: tuple[EvidenceReference, ...] = ()
    overridable: bool
    effective_at: datetime


class CollaborationSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = CONTRACT_VERSION
    message_type: Literal["CollaborationSession"] = "CollaborationSession"
    session_id: str
    case_id: str
    trace_id: str
    status: Literal["planned", "running", "converged", "needs_human_review", "budget_exhausted", "failed"]
    current_round: int = Field(default=0, ge=0, le=3)
    max_rounds: Literal[3] = 3
    task_ids: List[str] = Field(default_factory=list)
    finding_ids: List[str] = Field(default_factory=list)
    assistance_request_ids: List[str] = Field(default_factory=list)
    constraint_ids: List[str] = Field(default_factory=list)
    convergence_hashes: List[str] = Field(default_factory=list, max_length=3)
    stop_reason: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class SynthesisResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0"] = CONTRACT_VERSION
    message_type: Literal["SynthesisResult"] = "SynthesisResult"
    synthesis_id: str
    case_id: str
    trace_id: str
    primary_solution: Optional[Dict[str, Any]] = None
    alternative_solutions: tuple[Dict[str, Any], ...] = Field(default=(), max_length=2)
    blocked_candidates: tuple[Dict[str, Any], ...] = ()
    unresolved_conflicts: tuple[Dict[str, Any], ...] = ()
    missing_information: tuple[Dict[str, Any], ...] = ()
    operations_plan: Optional[Dict[str, Any]] = None
    customer_draft: Optional[Dict[str, Any]] = None
    evidence_validation_summary: Dict[str, Any]
    human_review_requirements: tuple[Dict[str, Any], ...] = ()
    source_finding_ids: tuple[str, ...] = ()
    synthesis_policy_version: str
    output_hash: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
