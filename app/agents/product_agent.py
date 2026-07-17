"""Grounded deterministic Product Agent backed by ProductRAGService."""

from __future__ import annotations

from typing import Any, Dict, List

from app.rag.product_retriever import ProductRAGService
from app.schemas.state import EvidenceItem, SharedCaseState
from app.tools.product_tools import SHB_PRODUCT_CATALOG


class ProductAgent:
    owner = "Product"

    def __init__(self, rag: ProductRAGService | None = None) -> None:
        self.rag = rag or ProductRAGService()

    def run(self, state: SharedCaseState) -> Dict[str, Any]:
        request = self._request_text(state).lower()
        profile = state.company_profile
        selected: List[str] = []

        if self._has(request, "payroll", "chi lương", "trả lương") or int(profile.get("employees_count", 0)) >= 100:
            selected.append("PROD-PAYROLL")
        if (
            self._has(request, "dòng tiền", "cash management", "tài khoản phụ")
            or "phân tán" in str(profile.get("cash_flow_status", "")).lower()
        ) and float(profile.get("annual_revenue", 0)) >= 50_000_000_000:
            selected.append("PROD-CASH-MGMT")
        if self._has(request, "thu hộ", "chi hộ", "virtual account", "đối soát"):
            selected.append("PROD-COLLECTION")
        if self._has(request, "thấu chi", "vốn lưu động", "tín dụng", "cho vay", "credit"):
            selected.append("PROD-WORKING-CAPITAL")

        # Retrieval is used to ground selected products. Candidate expansion is
        # intentionally deterministic to prevent generic terms from adding an
        # unrelated financial product.
        retrieval = {item.product_id: item for item in self.rag.search(request, top_k=4)}
        selected = list(dict.fromkeys(selected))

        products: List[Dict[str, Any]] = []
        evidences: List[EvidenceItem] = []
        for product_id in selected:
            product = SHB_PRODUCT_CATALOG[product_id]
            score = self._matching_score(product_id, request, profile)
            products.append(
                {
                    "product_id": product_id,
                    "name": product["name"],
                    "match_score": score,
                    "matching_reason": self._matching_reason(product_id, profile),
                    "prerequisites": list(product["required_documents"]),
                    "retrieval_score": retrieval.get(product_id).score if product_id in retrieval else None,
                }
            )
            evidences.append(
                EvidenceItem(
                    agent="Product",
                    claim=f"{product['name']} có điều kiện: {product['eligibility_rules']}",
                    source_doc=product["source_metadata"]["document"],
                    page_or_section=product["source_metadata"]["section"],
                    quote=product["eligibility_rules"],
                )
            )

        result = {
            "recommended_bundle": {
                "bundle_name": "Gói giải pháp doanh nghiệp tổng hợp" if len(products) > 1 else "Giải pháp doanh nghiệp",
                "products": products,
            },
            "recommended_products": [item["product_id"] for item in products],
            "missing_parameters": [] if products else ["Nhu cầu sản phẩm cụ thể"],
            "retrieval_query": request,
            "citations": [item.model_dump() for item in evidences],
        }
        state.product_result = result
        state.evidences.extend(evidences)
        self._audit(state, "product.match", {"product_ids": result["recommended_products"]})
        return result

    @staticmethod
    def _request_text(state: SharedCaseState) -> str:
        if isinstance(state.customer_request, dict):
            return str(state.customer_request.get("text", " ".join(map(str, state.customer_request.values()))))
        return str(state.customer_request)

    @staticmethod
    def _has(text: str, *terms: str) -> bool:
        return any(term in text for term in terms)

    @staticmethod
    def _matching_score(product_id: str, request: str, profile: Dict[str, Any]) -> float:
        score = 0.65
        if product_id == "PROD-PAYROLL" and int(profile.get("employees_count", 0)) >= 10:
            score += 0.25
        if product_id == "PROD-CASH-MGMT" and float(profile.get("annual_revenue", 0)) >= 50_000_000_000:
            score += 0.25
        if product_id == "PROD-WORKING-CAPITAL" and any(term in request for term in ("thấu chi", "vốn lưu động", "tín dụng")):
            score += 0.25
        return round(min(score, 0.99), 2)

    @staticmethod
    def _matching_reason(product_id: str, profile: Dict[str, Any]) -> str:
        reasons = {
            "PROD-PAYROLL": f"Quy mô {profile.get('employees_count', 0)} nhân sự phù hợp dịch vụ chi lương.",
            "PROD-CASH-MGMT": "Dòng tiền phân tán và doanh thu đạt ngưỡng demo của giải pháp quản lý dòng tiền.",
            "PROD-COLLECTION": "Nhu cầu thu/chi hộ và đối soát giao dịch.",
            "PROD-WORKING-CAPITAL": "Nhu cầu vốn lưu động/thấu chi cần được Legal thẩm định tiếp.",
        }
        return reasons[product_id]

    @staticmethod
    def _audit(state: SharedCaseState, action: str, result: Dict[str, Any]) -> None:
        state.audit_log.append({"actor": "Product", "action": action, "result": result})
