"""Legal Agent V2 — domain models.

All models here are NEW additions. They do not modify any existing models in
app/schemas/state.py. Agents/services that want the enriched legal output can
import from here; the existing orchestrator keeps reading state.legal_result
unchanged.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# L2 — Legal Profile
# ---------------------------------------------------------------------------

class RepresentativeInfo(BaseModel):
    """Thông tin người đại diện pháp luật hoặc người được ủy quyền."""
    name: str = Field(default="", description="Họ và tên")
    id_number: str = Field(default="", description="Số CCCD/Hộ chiếu")
    position: str = Field(default="", description="Chức danh")
    is_authorized: bool = Field(default=False, description="Có phải người được ủy quyền không")
    authorization_doc_present: bool = Field(default=False, description="Có giấy ủy quyền trong hồ sơ không")


class UBOInfo(BaseModel):
    """Thông tin chủ sở hữu hưởng lợi (UBO)."""
    status: Literal["complete", "missing", "partial", "unknown"] = Field(default="unknown")
    ubo_list: List[Dict[str, Any]] = Field(default_factory=list, description="Danh sách UBO nếu có")
    doc_present: bool = Field(default=False, description="Có tài liệu UBO trong hồ sơ không")


class LegalProfile(BaseModel):
    """Hồ sơ pháp lý tổng hợp của doanh nghiệp — L2."""
    customer_id: str = Field(default="")
    company_name: str = Field(default="")
    tax_code: str = Field(default="")
    legal_status: str = Field(default="unknown", description="active / inactive / suspended")
    representative: RepresentativeInfo = Field(default_factory=RepresentativeInfo)
    ubo: UBOInfo = Field(default_factory=UBOInfo)
    classified_documents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Danh sách tài liệu đã được phân loại bởi DocumentClassifier"
    )
    has_business_reg: bool = Field(default=False)
    business_reg_expired: bool = Field(default=False)
    business_reg_tax_mismatch: bool = Field(default=False)
    has_financial_reports: bool = Field(default=False)
    watchlist_screened: bool = Field(default=False)
    watchlist_result: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# L3 — Compliance Rule model
# ---------------------------------------------------------------------------

class ComplianceRule(BaseModel):
    """Rule model versioned — aligned with plan_v3 Section 11."""
    rule_id: str
    version: str = "2026.1"
    name: str = ""
    scope: List[str] = Field(default_factory=list, description="Danh sách product_id áp dụng; rỗng = tất cả")
    effective_from: date
    effective_to: Optional[date] = None
    severity: Literal["hard_block", "blocking", "warning", "info"] = "blocking"
    priority: int = Field(default=3, description="1=sanction, 2=legal block, 3=eligibility block, 4=missing info, 5=warning, 6=info")
    condition_type: Literal["deterministic", "heuristic"] = "deterministic"
    condition_description: str = ""
    required_inputs: List[str] = Field(default_factory=list)
    failure_code: str = ""
    failure_message: str = ""
    source_document_id: str = ""
    source_location: str = ""
    escalation_owner: Optional[str] = None
    action_on_failure: str = ""

    def is_effective(self, as_of: Optional[date] = None) -> bool:
        """Kiểm tra rule có đang effective không."""
        check_date = as_of or date.today()
        if self.effective_from > check_date:
            return False
        if self.effective_to is not None and self.effective_to < check_date:
            return False
        return True

    def applies_to(self, product_id: str) -> bool:
        """Kiểm tra rule có áp dụng cho product_id không."""
        return not self.scope or product_id in self.scope


# ---------------------------------------------------------------------------
# L5/L6 — Rule Evaluation Result
# ---------------------------------------------------------------------------

EligibilityStatus = Literal["passed", "failed", "pending_information", "pending_review"]


class RuleEvaluationResult(BaseModel):
    """Kết quả đánh giá từng rule — L5."""
    rule_id: str
    rule_name: str = ""
    rule_version: str = "2026.1"
    status: EligibilityStatus
    reason: str = ""
    severity: str = "blocking"
    priority: int = 3
    failure_code: str = ""
    source_document_id: str = ""
    source_location: str = ""
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence_quote: str = ""


# ---------------------------------------------------------------------------
# L6 — Per-product Eligibility Result
# ---------------------------------------------------------------------------

class ProductEligibilityResult(BaseModel):
    """Kết quả eligibility tổng hợp cho một product — L6."""
    product_id: str
    product_name: str = ""
    status: EligibilityStatus
    blocking_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    warning_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    passed_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    missing_documents: List[str] = Field(default_factory=list)
    citations: List[Dict[str, str]] = Field(default_factory=list)
    review_required: bool = False


# ---------------------------------------------------------------------------
# L9 — Full Legal Check Output
# ---------------------------------------------------------------------------

class LegalCheckOutput(BaseModel):
    """Output contract đầy đủ của LegalAgentV2 — L9.

    Backward compatible với format cũ (eligibility_status, failed_checks,
    missing_documents, citations) đồng thời cung cấp thông tin chi tiết hơn.
    """

    # --- Backward compatible fields (orchestrator cũ đọc được) ---
    eligibility_status: EligibilityStatus = "passed"
    failed_checks: List[Dict[str, Any]] = Field(default_factory=list)
    missing_documents: List[str] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)

    # --- Extended V2 fields ---
    document_validation: Dict[str, Any] = Field(default_factory=dict)
    ubo_check: Dict[str, Any] = Field(default_factory=dict)
    watchlist_screening: Dict[str, Any] = Field(default_factory=dict)
    rule_evaluations: List[RuleEvaluationResult] = Field(default_factory=list)
    per_product_eligibility: List[ProductEligibilityResult] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = "low"
    review_required: bool = False
    legal_profile: Optional[LegalProfile] = None
    schema_version: str = "2.0.0"
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
