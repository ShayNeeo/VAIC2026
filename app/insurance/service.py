"""Insurance coverage readiness analysis without binding, pricing or
approving a policy. Mirrors app/credit/service.py::CreditReadinessService's
shape (deterministic facts -> risk flags -> hard blocks -> conclusion),
grounded in data/legal/policies/shb_insurance_policy_manual.json (see
app/knowledge/insurance_service.py for the retrieval side).

Independent of Credit/Product: this service only reads product_result and
customer_attributes/business_snapshot -- it never reads eligibility_result
or credit_result, matching the "3 Agent hoạt động độc lập" requirement.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Iterable, List, Optional


_LOGISTICS_INDUSTRY_KEYWORDS = ("logistic", "van tai", "vận tải", "giao nhan", "giao nhận", "kho van", "kho vận")


class InsuranceReadinessService:
    def analyze(
        self,
        *,
        product_result: Dict[str, Any],
        customer_attributes: Dict[str, Any],
        documents: Iterable[Dict[str, Any]],
        business_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        profile = self._profile(customer_attributes, business_snapshot or {})
        recommendations = list(product_result.get("recommendations", []))
        secured_products = [
            item for item in recommendations
            if item.get("credit_flag") is True
            or str(item.get("product_family", item.get("family", ""))).lower() == "credit"
        ]

        missing: List[str] = []
        risk_flags: List[Dict[str, Any]] = []
        hard_blocks: List[Dict[str, Any]] = []
        coverage_checks: List[Dict[str, Any]] = []

        # Điều 8: secured lending requires current property insurance with
        # SHB as first beneficiary. Only checked when a candidate product
        # actually needs collateral -- not a blanket requirement.
        if secured_products:
            has_property_insurance = profile.get("has_property_insurance")
            check = {
                "requirement": "property_insurance_for_collateral",
                "policy_ref": "SHB_Insurance_Policy_Manual/DIEU-8",
                "applies_because": "credit_flag sản phẩm đề xuất = true (tín dụng có khả năng cần tài sản đảm bảo)",
                "status": "unknown",
            }
            if has_property_insurance is None:
                missing.append("has_property_insurance")
                check["status"] = "unknown"
            elif has_property_insurance is False:
                hard_blocks.append(
                    {
                        "code": "MISSING_COLLATERAL_PROPERTY_INSURANCE",
                        "policy_ref": "SHB_Insurance_Policy_Manual/DIEU-8-K2",
                        "severity": "blocking",
                        "basis": "customer.has_property_insurance=false với sản phẩm tín dụng có bảo đảm được đề xuất.",
                    }
                )
                check["status"] = "missing"
            else:
                check["status"] = "present"
            coverage_checks.append(check)

        # Điều 19: logistics/cargo customers using guarantee/credit tied to
        # an in-transit shipment need cargo insurance on that shipment.
        industry = str(profile.get("industry") or "").lower()
        is_logistics = any(keyword in industry for keyword in _LOGISTICS_INDUSTRY_KEYWORDS)
        if is_logistics:
            has_cargo_insurance = profile.get("has_cargo_insurance")
            check = {
                "requirement": "cargo_insurance_for_logistics",
                "policy_ref": "SHB_Insurance_Policy_Manual/DIEU-19",
                "applies_because": f"industry='{profile.get('industry')}' khớp nhóm logistics/vận tải.",
                "status": "unknown" if has_cargo_insurance is None else ("present" if has_cargo_insurance else "missing"),
            }
            if has_cargo_insurance is None:
                missing.append("has_cargo_insurance")
            elif has_cargo_insurance is False:
                risk_flags.append(
                    {
                        "code": "MISSING_CARGO_INSURANCE",
                        "policy_ref": "SHB_Insurance_Policy_Manual/DIEU-19-K1",
                        "severity": "review",
                        "basis": "Doanh nghiệp logistics chưa xác nhận bảo hiểm hàng hóa vận chuyển cho lô hàng liên quan.",
                    }
                )
            coverage_checks.append(check)

        # Điều 28/29: recommended, never blocking -- flagged as an
        # advisory risk_flag only when the underlying signal is present.
        if profile.get("revenue_concentration_top_customer_pct") is not None:
            try:
                concentration = float(profile["revenue_concentration_top_customer_pct"])
            except (TypeError, ValueError):
                concentration = None
            if concentration is not None and concentration >= 0.4:
                risk_flags.append(
                    {
                        "code": "TRADE_CREDIT_CONCENTRATION_RISK",
                        "policy_ref": "SHB_Insurance_Policy_Manual/DIEU-29",
                        "severity": "advisory",
                        "basis": f"revenue_concentration_top_customer_pct={concentration} >= 0.4; khuyến nghị bảo hiểm tín dụng thương mại.",
                    }
                )

        if not secured_products and not is_logistics and not risk_flags:
            status = "not_applicable"
            conclusion = (
                "Phương án hiện tại không phát sinh yêu cầu bảo hiểm bắt buộc; "
                "Insurance Expert ghi nhận không áp dụng thay vì đưa ra kết luận sẵn sàng bảo hiểm."
            )
        elif hard_blocks:
            status = "hard_block_detected"
            conclusion = "Phát hiện thiếu bảo hiểm bắt buộc theo chính sách; Insurance Expert không được xác nhận sản phẩm có bảo đảm là sẵn sàng giải ngân."
        elif missing:
            status = "needs_information"
            conclusion = "Chưa đủ thông tin bảo hiểm để xác nhận mức độ sẵn sàng theo chính sách."
        else:
            status = "ready_for_insurance_review"
            conclusion = "Không phát hiện thiếu bảo hiểm bắt buộc từ dữ liệu hiện có; vẫn cần cán bộ nghiệp vụ xác nhận hồ sơ gốc."

        return {
            "status": status,
            "agent_run_id": f"ARUN-INSURANCE-{uuid.uuid4().hex[:8].upper()}",
            "insurance_product_ids": sorted({str(item.get("product_id")) for item in secured_products}),
            "known_facts": [{"industry": profile.get("industry"), "is_logistics_sector": is_logistics}],
            "missing_information": missing,
            "risk_flags": risk_flags,
            "hard_blocks": hard_blocks,
            "coverage_checks": coverage_checks,
            "conclusion": conclusion,
            "decision_authority": "insurance_officer_and_approval_workflow",
        }

    @staticmethod
    def _profile(customer_attributes: Dict[str, Any], snapshot: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(customer_attributes)
        for section in ("company_identity", "business_profile", "operating_model", "financing_profile", "legal_profile"):
            value = snapshot.get(section)
            if isinstance(value, dict):
                merged.update(value)
        return merged
