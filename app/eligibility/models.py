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
    policy_id: str = ""
    section_id: str = ""
    source_document_id: str
    source_version: str
    source_location: str
    source_quote: str
    access_scope: Optional[dict] = None
    # Policy flag, not a technical property of the rule: may a human
    # specialist override a FAILED verdict on this specific rule after
    # independent verification (see app/workflow/risk_gate.py's
    # required_reviewer_roles/human_review_allowed and
    # app/api/v2/employee_router.py's specialist-reviews endpoint)? Defaults
    # False -- a rule is only overridable if a human explicitly marked it so
    # in this registry, never by default. Absolute/factual rules (minimum
    # document presence, numeric thresholds, bad-debt history) must stay
    # False; a rule whose failure can genuinely be a documentation/judgment
    # ambiguity a specialist can resolve through independent verification
    # (e.g. RULE-CREDIT-UBO-001) may be set True.
    human_review_allowed: bool = False


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
    human_review_allowed: bool = False


class ProductEligibility(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    status: RuleStatus
    rules: List[RuleEvaluation]
    missing_information: List[str]
    evaluated_at: datetime
    registry_version: str
