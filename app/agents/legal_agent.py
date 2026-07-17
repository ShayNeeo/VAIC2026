"""Conservative KYC/UBO and product eligibility checks."""

from __future__ import annotations

from typing import Any, Dict, List

from app.schemas.state import EvidenceItem, SharedCaseState
from app.tools.legal_tools import SYNTHETIC_COMPLIANCE_POLICIES, check_document_expiry, validate_business_registration


class LegalAgent:
    owner = "Legal"

    def run(self, state: SharedCaseState) -> Dict[str, Any]:
        failed: List[Dict[str, str]] = []
        missing: List[str] = []
        evidences: List[EvidenceItem] = []
        profile = state.company_profile
        products = state.product_result.get("recommended_products", [])

        business_regs = [doc for doc in state.documents if "đăng ký" in str(doc.get("doc_type", "")).lower() or "dkkd" in str(doc.get("doc_type", "")).lower()]
        if not business_regs:
            missing.append("Giấy chứng nhận đăng ký doanh nghiệp")
            failed.append(self._failure("RULE-BUSINESS-REG", "Thiếu đăng ký doanh nghiệp", "blocking"))
        else:
            validation = validate_business_registration(business_regs[0], str(profile.get("tax_code", "")))
            expiry = check_document_expiry(business_regs[0].get("expiry_date"))
            if validation["status"] != "valid" or expiry["is_expired"]:
                failed.append(self._failure("RULE-BUSINESS-REG", "Đăng ký doanh nghiệp không hợp lệ hoặc hết hiệu lực", "blocking"))

        ubo_document = any("ubo" in str(doc.get("doc_type", "")).lower() or "chủ sở hữu hưởng lợi" in str(doc.get("doc_type", "")).lower() for doc in state.documents)
        ubo_complete = str(profile.get("ubo_status", "")).lower() in {"đầy đủ", "day du", "verified", "complete"} or ubo_document
        if not ubo_complete:
            missing.append("Thông tin chủ sở hữu hưởng lợi (UBO)")
            failed.append(self._failure("RULE-UBO", "Thiếu thông tin chủ sở hữu hưởng lợi cuối cùng (UBO)", "blocking"))

        financial_document = any("báo cáo tài chính" in str(doc.get("doc_type", "")).lower() or "bctc" in str(doc.get("doc_type", "")).lower() for doc in state.documents)
        if "PROD-WORKING-CAPITAL" in products and not (bool(profile.get("financial_reports", {}).get("has_recent")) or financial_document):
            missing.append("Báo cáo tài chính năm gần nhất")
            failed.append(self._failure("RULE-CREDIT-FS", "Thiếu báo cáo tài chính năm gần nhất cho thẩm định tín dụng", "blocking"))

        for rule_id in dict.fromkeys(item["rule_id"] for item in failed):
            policy = SYNTHETIC_COMPLIANCE_POLICIES[rule_id]
            evidences.append(
                EvidenceItem(
                    agent="Legal",
                    claim=next(item["reason"] for item in failed if item["rule_id"] == rule_id),
                    source_doc=policy["document"],
                    page_or_section=policy["section"],
                    quote=policy["text"],
                )
            )

        status = "pending_info" if any(item["severity"] == "blocking" for item in failed) else "passed"
        result = {
            "eligibility_status": status,
            "failed_checks": failed,
            "missing_documents": list(dict.fromkeys(missing)),
            "citations": [item.model_dump() for item in evidences],
        }
        state.legal_result = result
        state.missing_information = list(dict.fromkeys([*state.missing_information, *missing]))
        state.evidences.extend(evidences)
        state.risk_level = "high" if status == "pending_info" else "low"
        state.audit_log.append({"actor": "Legal", "action": "legal.audit", "result": status, "failed_checks": failed})
        return result

    @staticmethod
    def _failure(rule_id: str, reason: str, severity: str) -> Dict[str, str]:
        return {"rule_id": rule_id, "reason": reason, "severity": severity}
