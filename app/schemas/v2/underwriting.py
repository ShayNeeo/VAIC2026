"""Underwriting schemas for Phase 9.

Models the Underwriting Submission Package.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from app.metadata.models import MetadataEnvelope


class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED_FOR_INFO = "returned_for_info"


class UnderwritingSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    submission_id: str
    case_id: str
    rm_employee_id: str
    status: SubmissionStatus
    submitted_at: Optional[datetime] = None
    meta: Optional[MetadataEnvelope] = None
    
    # Snapshot of the core case data at submission time
    customer_business_snapshot: Dict[str, Any]
    product_result: Dict[str, Any]
    eligibility_result: Dict[str, Any]
    risk_gate_result: Dict[str, Any]
    
    # Metadata pointers to collected documents
    documents: List[Dict[str, Any]]
    
    # The actual RM Approval token details
    rm_approval_record: Dict[str, Any]
