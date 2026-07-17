"""Product Matcher with deterministic scoring + LLM reason generation."""

from __future__ import annotations

from typing import Any, Dict, List

import uuid
from mcp_common.schemas import EvidenceItem
from mcp_common.llm_client import get_gemma_client, deterministic_matching_reason
from mcp_common.config import settings

SHB_PRODUCT_CATALOG = {
    "PROD-PAYROLL": {
        "name": "SHB Payroll",
        "description": "Giải pháp chi trả lương tự động, tích hợp kế toán.",
        "eligibility_rules": "Doanh nghiệp từ 10 nhân sự, có tài khoản SHB, đăng ký Dịch vụ Ngân hàng điện tử.",
        "benefits": ["Chi lương hàng loạt", "Tự động tính thuế TNCN", "Báo cáo tùy chỉnh"],
        "required_documents": ["Giấy đăng ký kinh doanh", "Danh sách nhân viên", "Quyết định ủy quyền"],
        "source_metadata": {"document": "Product_Catalog.pdf", "section": "Payroll", "effective_date": "2025-01-01"},
    },
    "PROD-CASH-MGMT": {
        "name": "SHB Cash Management",
        "description": "Quản lý dòng tiền, tài khoản phụ, đối soát tự động.",
        "eligibility_rules": "Doanh nghiệp doanh thu từ 50 tỷ VNĐ/năm, dòng tiền phân tán nhiều ngân hàng.",
        "benefits": ["Xem dòng tiền real-time", "Tài khoản phụ ảo", "Đối soát tự động"],
        "required_documents": ["Báo cáo tài chính", "Dòng tiền 6 tháng", "Hồ sơ pháp nhân"],
        "source_metadata": {"document": "Product_Catalog.pdf", "section": "Cash_Management", "effective_date": "2025-01-01"},
    },
    "PROD-COLLECTION": {
        "name": "SHB Collection",
        "description": "Dịch vụ thu hộ, chi hộ, Virtual Account, đối soát.",
        "eligibility_rules": "Cần thu/chi định kỳ, số lượng đối tác lớn, dùng Virtual Account.",
        "benefits": ["Thu hộ tự động", "Virtual Account", "Đối soát real-time"],
        "required_documents": ["Hợp đồng thu/chi hộ", "Danh sách đối tác", "Quyết định ủy quyền"],
        "source_metadata": {"document": "Product_Catalog.pdf", "section": "Collection", "effective_date": "2025-01-01"},
    },
    "PROD-WORKING-CAPITAL": {
        "name": "SHB Working Capital",
        "description": "Vốn lưu động, thấu chi, hạn mức overdraft.",
        "eligibility_rules": "Doanh nghiệp hoạt động ≥ 2 năm, BCTC kiểm toán, không nợ xấu, có tài sản đảm bảo.",
        "benefits": ["Hạn mức linh hoạt", "Lãi suất ưu đãi", "Giải ngân nhanh"],
        "required_documents": ["BCTC 2 năm gần nhất", "CIC", "Hồ sơ tài sản đảm bảo", "Kế hoạch kinh doanh"],
        "source_metadata": {"document": "Product_Catalog.pdf", "section": "Working_Capital", "effective_date": "2025-01-01"},
    },
}


class ProductMatcher:
    def __init__(self):
        self._gemma = get_gemma_client()

    def run(
        self,
        request_text: str,
        profile: Dict[str, Any],
        retrieval_results: List[Any],
    ) -> Dict[str, Any]:
        request = request_text.lower()
        profile_employees = int(profile.get("employees_count", 0))
        profile_revenue = float(profile.get("annual_revenue", 0))
        profile_cash_flow = str(profile.get("cash_flow_status", "")).lower()

        selected = []

        if self._has(request, "payroll", "chi lương", "trả lương") or profile_employees >= 100:
            selected.append("PROD-PAYROLL")
        if (self._has(request, "dòng tiền", "cash management", "tài khoản phụ") or "phân tán" in profile_cash_flow) and profile_revenue >= 50_000_000_000:
            selected.append("PROD-CASH-MGMT")
        if self._has(request, "thu hộ", "chi hộ", "virtual account", "đối soát"):
            selected.append("PROD-COLLECTION")
        if self._has(request, "thấu chi", "vốn lưu động", "tín dụng", "cho vay", "credit"):
            selected.append("PROD-WORKING-CAPITAL")

        selected = list(dict.fromkeys(selected))

        # Retrieval map for retrieval_score
        retrieval = {item.product_id: item for item in retrieval_results}

        products = []
        evidences = []
        for pid in selected:
            product = SHB_PRODUCT_CATALOG[pid]
            score = self._matching_score(pid, request, profile)
            reason = self._matching_reason(pid, profile)
            retrieval_score = retrieval.get(pid).score if pid in retrieval else None

            products.append({
                "product_id": pid,
                "name": product["name"],
                "match_score": score,
                "matching_reason": reason,
                "prerequisites": list(product["required_documents"]),
                "retrieval_score": retrieval_score,
            })

            evidences.append(EvidenceItem(
                claim_id=f"EVID-{uuid.uuid4().hex[:8]}",
                agent="Product",
                claim=f"{product['name']} có điều kiện: {product['eligibility_rules']}",
                source_document_id=product["source_metadata"]["document"],
                source_version=product["source_metadata"].get("effective_date", "v1"),
                section_or_page=product["source_metadata"]["section"],
                quote=product["eligibility_rules"],
                validation_method="exact_match",
                is_valid=False,
            ))

        bundle_name = "Gói giải pháp doanh nghiệp tổng hợp" if len(products) > 1 else "Giải pháp doanh nghiệp"

        return {
            "recommended_bundle": {"bundle_name": bundle_name, "products": products},
            "recommended_products": [p["product_id"] for p in products],
            "missing_parameters": [] if products else ["Nhu cầu sản phẩm cụ thể"],
            "retrieval_query": request,
            "citations": [e.model_dump() for e in evidences],
            "evidences": evidences,
        }

    @staticmethod
    def _has(text: str, *terms: str) -> bool:
        return any(term in text for term in terms)

    def _matching_score(self, product_id: str, request: str, profile: Dict[str, Any]) -> float:
        score = 0.65
        if product_id == "PROD-PAYROLL" and int(profile.get("employees_count", 0)) >= 10:
            score += 0.25
        if product_id == "PROD-CASH-MGMT" and float(profile.get("annual_revenue", 0)) >= 50_000_000_000:
            score += 0.25
        if product_id == "PROD-WORKING-CAPITAL" and any(t in request for t in ("thấu chi", "vốn lưu động", "tín dụng")):
            score += 0.25
        return round(min(score, 0.99), 2)

    def _matching_reason(self, product_id: str, profile: Dict[str, Any]) -> str:
        if settings.USE_GEMMA_FOR_REASON:
            try:
                prompt = f"""Viết lý do gợi ý sản phẩm {product_id} cho doanh nghiệp (1 câu, tiếng Việt, ≤ 50 từ).
Profile: {profile}
Sản phẩm: {SHB_PRODUCT_CATALOG[product_id]['name']} - {SHB_PRODUCT_CATALOG[product_id]['description']}"""
                return self._gemma.generate_sync(prompt, temperature=0.1, max_output_tokens=64)
            except Exception:
                pass
        return deterministic_matching_reason(product_id, profile)