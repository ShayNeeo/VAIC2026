"""V3 Product Matcher - Deterministic scoring + LLM reason generation."""

from __future__ import annotations

from typing import Any, Dict, List

from mcp_common.schemas import (
    ProductMatchScore,
    ProductPrerequisite,
    ProductRecommendation,
    ProductBundle,
    ProductResult,
    EvidenceItem,
)
from mcp_common.config import settings
from mcp_common.llm_client import get_gemma_client, deterministic_matching_reason

from servers.v3_product_agent.product.catalog import V3_PRODUCT_CATALOG
from servers.v3_product_agent.rag.retriever import ProductRetrievalResult


class ProductMatcher:
    """Deterministic product selection + scoring with optional LLM reason generation."""

    def __init__(self):
        self._gemma = get_gemma_client()

    def run(
        self,
        request_text: str,
        profile: Dict[str, Any],
        retrieval_results: List[ProductRetrievalResult],
    ) -> Dict[str, Any]:
        request = request_text.lower()
        profile_employees = int(profile.get("employees_count", 0))
        profile_revenue = float(profile.get("annual_revenue", 0))
        profile_cash_flow = str(profile.get("cash_flow_status", "")).lower()

        selected = []

        # V3 deterministic rules (match blueprint §7)
        if self._has(request, "payroll", "chi lương", "trả lương") or profile_employees >= 100:
            selected.append("PROD-PAYROLL")
        if (self._has(request, "dòng tiền", "cash management", "tài khoản phụ") or "phân tán" in profile_cash_flow) and profile_revenue >= 50_000_000_000:
            selected.append("PROD-CASH-MGMT")
        if self._has(request, "thu hộ", "chi hộ", "virtual account", "đối soát"):
            selected.append("PROD-COLLECTION")
        if self._has(request, "thấu chi", "vốn lưu động", "tín dụng", "cho vay", "credit"):
            selected.append("PROD-WORKING-CAPITAL")

        selected = list(dict.fromkeys(selected))  # dedupe preserving order

        # Retrieval map for retrieval_score
        retrieval = {item.product_id: item for item in retrieval_results}

        products = []
        evidences = []

        for pid in selected:
            product = V3_PRODUCT_CATALOG[pid]
            score = self._matching_score(pid, request, profile)
            reason = self._matching_reason(pid, profile)
            retrieval_score = retrieval.get(pid).score if pid in retrieval else None

            products.append(ProductRecommendation(
                product_id=pid,
                name=product["name"],
                match_score=self._build_match_score(score, pid, request, profile),
                matching_reason=reason,
                prerequisites=product["prerequisites"],  # Already ProductPrerequisite objects
                retrieval_score=retrieval_score,
            ))

            # Create evidence item for this product
            evidences.append(EvidenceItem(
                claim_id=f"EVID-{pid}-{hash(product['eligibility_rules']) % 10000:04d}",
                agent="Product",
                claim=f"{product['name']} có điều kiện: {product['eligibility_rules']}",
                source_document_id=product["source_metadata"]["document"],
                source_version=product["source_metadata"]["effective_date"],
                section_or_page=product["source_metadata"]["section"],
                quote=product["eligibility_rules"],
                validation_method="exact_match",
                is_valid=False,  # Will be set by EvidenceVerifier
            ))

        bundle_name = "Gói giải pháp doanh nghiệp tổng hợp" if len(products) > 1 else "Giải pháp doanh nghiệp"

        return {
            "recommended_bundle": ProductBundle(
                bundle_name=bundle_name,
                products=products,
                bundle_reason=f"Dựa trên nhu cầu: {', '.join(p.name for p in products)}" if products else "Chưa xác định nhu cầu cụ thể",
            ),
            "recommended_products": [p.product_id for p in products],
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

    def _build_match_score(
        self,
        total_score: float,
        product_id: str,
        request: str,
        profile: Dict[str, Any],
    ) -> ProductMatchScore:
        """Decompose total score into V3 components (§7)."""
        profile_employees = int(profile.get("employees_count", 0))
        profile_revenue = float(profile.get("annual_revenue", 0))

        return ProductMatchScore(
            intent_fit=0.30 if self._has(request, *V3_PRODUCT_CATALOG[product_id]["use_cases"]) else 0.10,
            segment_fit=0.25 if profile_employees >= 100 else 0.15,
            size_revenue_fit=0.25 if (
                product_id == "PROD-CASH-MGMT" and profile_revenue >= 50_000_000_000
            ) or (
                product_id == "PROD-PAYROLL" and profile_employees >= 10
            ) else 0.10,
            workflow_signal=0.15,
            missing_prerequisites=0.0,
            legal_blocking=0.0,
            total=total_score,
        )

    def _matching_reason(self, product_id: str, profile: Dict[str, Any]) -> str:
        if settings.USE_GEMMA_FOR_REASON:
            try:
                prompt = f"""Viết lý do gợi ý sản phẩm {product_id} cho doanh nghiệp (1 câu, tiếng Việt, ≤ 50 từ).
Profile: {profile}
Sản phẩm: {V3_PRODUCT_CATALOG[product_id]['name']} - {V3_PRODUCT_CATALOG[product_id]['description']}"""
                return self._gemma.generate_sync(prompt, temperature=0.1, max_output_tokens=64)
            except Exception:
                pass
        return deterministic_matching_reason(product_id, profile)