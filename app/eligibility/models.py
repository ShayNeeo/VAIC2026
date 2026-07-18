"""Eligibility rule registry and result contracts."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict


class RuleSeverity(str, Enum):
    BLOCKING = "blocking"
    WARNING = "warning"


class RuleStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING_INFORMATION = "pending_information"
    PENDING_REVIEW = "pending_review"


class EligibilityRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    version: str
    scope: List[str]
    effective_from: date
    effective_to: Optional[date] = None
    severity: RuleSeverity
    field: str
    operator: str
    expected: Any
    failure_code: str
    source_document_id: str
    source_version: str
    source_location: str
    source_quote: str


class RuleEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    rule_version: str
    status: RuleStatus
    severity: RuleSeverity
    field: str
    actual: Any = None
    expected: Any = None
    failure_code: Optional[str] = None
    source_document_id: str
    source_version: str
    source_location: str
    source_quote: str


class ProductEligibility(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    status: RuleStatus
    rules: List[RuleEvaluation]
    missing_information: List[str]
    evaluated_at: datetime
    registry_version: str
