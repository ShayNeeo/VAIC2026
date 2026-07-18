"""Typed contracts for sales-case document intake and confirmed customer snapshots."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class IntakeStatus(str, Enum):
    DRAFT = "draft"
    FILES_UPLOADED = "files_uploaded"
    DOCUMENT_PROCESSING = "document_processing"
    EXTRACTION_COMPLETED = "extraction_completed"
    PROFILE_REVIEW_REQUIRED = "profile_review_required"
    PROFILE_CONFIRMED = "profile_confirmed"
    PROCESSING_FAILED = "processing_failed"
    CANCELLED = "cancelled"


class DocumentJobStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    NEEDS_OCR = "needs_ocr"
    QUARANTINED = "quarantined"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class FieldValidationStatus(str, Enum):
    VALID = "valid"
    NEEDS_REVIEW = "needs_review"
    INVALID = "invalid"
    MISSING = "missing"


class ExtractedField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_id: str
    field_name: str
    value: Any = None
    normalized_value: Any = None
    source_document_id: str
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    source_text_span: str = ""
    extraction_method: str
    confidence: float = Field(ge=0.0, le=1.0)
    validation_status: FieldValidationStatus
    decision_impact: str = "low"
    confirmed_by_rm: bool = False
    original_value: Any = None
    edited_value: Any = None
    edited_by: Optional[str] = None
    edited_at: Optional[datetime] = None


class FieldConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conflict_id: str
    field_name: str
    candidates: List[Dict[str, Any]] = Field(min_length=2)
    decision_impact: str
    requires_confirmation: bool
    resolved_value: Any = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


class IntakeDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    case_id: str
    filename: str
    mime_type: str
    size_bytes: int = Field(ge=0)
    sha256: str
    document_type: str = "other"
    status: DocumentJobStatus
    quality: Dict[str, Any] = Field(default_factory=dict)
    error_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CustomerBusinessSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    schema_version: str = "1.0.0"
    revision: int = Field(ge=1)
    snapshot_hash: str
    company_identity: Dict[str, Any] = Field(default_factory=dict)
    business_profile: Dict[str, Any] = Field(default_factory=dict)
    operating_model: Dict[str, Any] = Field(default_factory=dict)
    transaction_profile: Dict[str, Any] = Field(default_factory=dict)
    collection_profile: Dict[str, Any] = Field(default_factory=dict)
    payment_profile: Dict[str, Any] = Field(default_factory=dict)
    payroll_profile: Dict[str, Any] = Field(default_factory=dict)
    cash_flow_profile: Dict[str, Any] = Field(default_factory=dict)
    technology_profile: Dict[str, Any] = Field(default_factory=dict)
    financing_profile: Dict[str, Any] = Field(default_factory=dict)
    legal_profile: Dict[str, Any] = Field(default_factory=dict)
    existing_bank_products: List[str] = Field(default_factory=list)
    explicit_needs: List[str] = Field(default_factory=list)
    inferred_candidate_needs: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    source_map: Dict[str, str] = Field(default_factory=dict)
    confidence_summary: Dict[str, float] = Field(default_factory=dict)
    rm_confirmed: bool = False
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime


class IntakeSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intake_id: str
    case_id: str
    employee_id: str
    session_id: str
    customer_id: Optional[str] = None
    status: IntakeStatus
    version: int = Field(default=1, ge=1)
    manual_input: Dict[str, Any]
    extracted_fields: List[ExtractedField] = Field(default_factory=list)
    conflicts: List[FieldConflict] = Field(default_factory=list)
    profile: Optional[CustomerBusinessSnapshot] = None
    audit_events: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ProfileChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_name: str
    value: Any
    reason: str = Field(min_length=3)

