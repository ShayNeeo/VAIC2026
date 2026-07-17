"""Pydantic mirror of plan_v2/contracts/context_snapshot.schema.json."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import SCHEMA_VERSION, DecisionImpact, ResolvedValue, ensure_unique


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    VERIFIED = "verified"
    INVALID = "invalid"
    EXPIRED = "expired"
    NEEDS_REVIEW = "needs_review"


class Employee(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: str
    role: str
    organization_unit: str
    permissions: List[str]
    access_scope: Dict[str, Any]
    preferences: Dict[str, Any] = Field(default_factory=dict)

    _check_permissions_unique = field_validator("permissions")(ensure_unique)


class Workspace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    current_screen: str
    selected_customer_id: Optional[str] = None
    active_case_id: Optional[str] = None
    active_task_id: Optional[str] = None
    selected_product_ids: List[str] = Field(default_factory=list)

    _check_products_unique = field_validator("selected_product_ids")(ensure_unique)


class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: Optional[str]
    profile_version: Optional[str]
    attributes: Dict[str, Any]
    source_observed_at: Optional[datetime]
    stale: bool


class Conversation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_goal: Optional[str]
    confirmed_facts: Dict[str, ResolvedValue]
    rejected_assumptions: List[str]
    open_questions: List[str]


class WorkspaceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    document_type: str
    version: str
    status: DocumentStatus
    effective_at: Optional[datetime] = None
    access_scope: Dict[str, Any]


class Conflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    candidate_values: List[ResolvedValue] = Field(min_length=2)
    decision_impact: DecisionImpact
    requires_confirmation: bool


class ContextSnapshot(BaseModel):
    """contracts/context_snapshot.schema.json"""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION, pattern=r"^2\.0\.0$")
    employee: Employee
    workspace: Workspace
    customer: Customer
    conversation: Conversation
    documents: List[WorkspaceDocument]
    conflicts: List[Conflict]
    assembled_at: datetime
