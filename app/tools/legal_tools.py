"""Synthetic legal/compliance tools for the hackathon MVP."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List


SYNTHETIC_COMPLIANCE_POLICIES: Dict[str, Dict[str, str]] = {
    "RULE-UBO": {
        "document": "SHB_KYC_AML_Demo_Policy_2026.pdf",
        "section": "Điều 8 - Chủ sở hữu hưởng lợi",
        "text": "Hồ sơ khách hàng doanh nghiệp phải có thông tin chủ sở hữu hưởng lợi cuối cùng (UBO).",
    },
    "RULE-CREDIT-FS": {
        "document": "SHB_Credit_Policy_Manual.pdf",
        "section": "Chương V - Hồ sơ tín dụng",
        "text": "Hồ sơ cấp tín dụng vốn lưu động phải có báo cáo tài chính năm gần nhất.",
    },
    "RULE-BUSINESS-REG": {
        "document": "SHB_KYC_AML_Demo_Policy_2026.pdf",
        "section": "Điều 3 - Định danh doanh nghiệp",
        "text": "Mã số thuế trên đăng ký doanh nghiệp phải khớp với hồ sơ khách hàng.",
    },
}


def validate_business_registration(document: Dict[str, Any], expected_tax_code: str) -> Dict[str, Any]:
    actual = str(document.get("tax_code", expected_tax_code))
    status = "valid" if actual == str(expected_tax_code) and document.get("status", "verified") != "invalid" else "invalid"
    return {"status": status, "tax_code": actual}


def check_document_expiry(expiry_date: Any) -> Dict[str, Any]:
    if not expiry_date or str(expiry_date).lower() in {"none", "null", "không thời hạn"}:
        return {"is_expired": False, "days_left": None}
    parsed = datetime.fromisoformat(str(expiry_date)).date()
    days = (parsed - date.today()).days
    return {"is_expired": days < 0, "days_left": days}


def search_compliance_policy(rule_ids: List[str]) -> List[Dict[str, str]]:
    return [dict(rule_id=rule_id, **SYNTHETIC_COMPLIANCE_POLICIES[rule_id]) for rule_id in rule_ids if rule_id in SYNTHETIC_COMPLIANCE_POLICIES]

