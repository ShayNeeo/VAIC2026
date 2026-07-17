"""V3 Product Matcher - deterministic need selection + scoring.

Decision logic only. No I/O, no duplication of catalog facts.

Pipeline contract:
    select_needs(request, profile) -> [ProductNeed]   # what the customer wants
    score(pid, request, profile)   -> ProductMatchScore
    reason(pid, profile)           -> str              # deterministic, Gemma optional
    detect_missing_parameters(...) -> [str]            # gaps that change ranking

All product facts come from ``catalog``; this module never hardcodes fees,
prerequisites or eligibility text.
"""

from __future__ import annotations

from typing import Any, Dict, List

from mcp_common.schemas import (
    EvidenceItem,
    ProductMatchScore,
    ProductPrerequisite,
    ProductRecommendation,
    ProductBundle,
    ValidationMethod,
)
from mcp_common.config import settings
from mcp_common.llm_client import get_gemma_client, deterministic_matching_reason

from servers.v3_product_agent.product.catalog import (
    V3_PRODUCT_CATALOG,
    ProductNeed,
    NEED_KEYWORDS,
    get_entry,
)
from servers.v3_product_agent.rag.retriever import ProductRetrievalResult


class ProductMatcher:
    """Deterministic product selection + scoring with optional LLM reason."""

    def __init__(self) -> None:
        self._gemma = get_gemma_client()

    # -- Need selection ----------------------------------------------------

    def select_needs(self, request_text: str, profile: Dict[str, Any]) -> List[ProductNeed]:
        """Resolve which product families the request implies.

        Order is preserved (deterministic); duplicates removed. A need is
        selected when a signal keyword appears in the request OR a hard
        profile rule holds (e.g. payroll for >=100 staff).
        """
        request = request_text.lower()
        employees = int(profile.get("employees_count", 0))
        revenue = float(profile.get("annual_revenue", 0))

        selected: List[ProductNeed] = []
        for need, keywords in NEED_KEYWORDS.items():
            if any(kw in request for kw in keywords):
                selected.append(need)
                continue
            # Hard profile rules (blueprint §7): payroll scales with headcount.
            if need is ProductNeed.PAYROLL and employees >= 100:
                selected.append(need)

        # De-dupe while preserving order.
        seen: set[ProductNeed] = set()
        return [n for n in selected if not (n in seen or seen.add(n))]

    # -- Scoring -----------------------------------------------------------

    def score(self, product_id: str, request: str, profile: Dict[str, Any]) -> float:
        """Single 0..0.99 fit score; decomposed in ``build_match_score``."""
        base = 0.65
        employees = int(profile.get("employees_count", 0))
        revenue = float(profile.get("annual_revenue", 0))
        if product_id == "PROD-PAYROLL" and employees >= 10:
            base += 0.25
        if product_id == "PROD-CASH-MGMT" and revenue >= 50_000_000_000:
            base += 0.25
        if product_id == "PROD-WORKING-CAPITAL" and any(
            t in request for t in ("thấu chi", "vốn lưu động", "tín dụng")
        ):
            base += 0.25
        return round(min(base, 0.99), 2)

    def build_match_score(
        self,
        total_score: float,
        product_id: str,
        request: str,
        profile: Dict[str, Any],
    ) -> ProductMatchScore:
        """Decompose total score into V3 components (§7)."""
        employees = int(profile.get("employees_count", 0))
        revenue = float(profile.get("annual_revenue", 0))
        use_cases = get_entry(product_id).get("use_cases", [])

        return ProductMatchScore(
            intent_fit=0.30 if any(kw in request for kw in use_cases) else 0.10,
            segment_fit=0.25 if employees >= 100 else 0.15,
            size_revenue_fit=0.25 if (
                (product_id == "PROD-CASH-MGMT" and revenue >= 50_000_000_000)
                or (product_id == "PROD-PAYROLL" and employees >= 10)
            ) else 0.10,
            workflow_signal=0.15,
            missing_prerequisites=0.0,
            legal_blocking=0.0,
            total=total_score,
        )

    # -- Reason ------------------------------------------------------------

    def reason(self, product_id: str, profile: Dict[str, Any]) -> str:
        """One-line Vietnamese rationale. Deterministic by default; Gemma polishes."""
        if settings.USE_GEMMA_FOR_REASON:
            try:
                product = get_entry(product_id)
                prompt = (
                    f"Viết lý do gợi ý sản phẩm {product_id} (1 câu, tiếng Việt, ≤ 50 từ).\n"
                    f"Profile: {profile}\n"
                    f"Sản phẩm: {product['name']} - {product['description']}"
                )
                return self._gemma.generate_sync(prompt, temperature=0.1, max_output_tokens=64)
            except Exception:
                pass
        return deterministic_matching_reason(product_id, profile)

    # -- Gap detection -----------------------------------------------------

    def detect_missing_parameters(
        self,
        request_text: str,
        profile: Dict[str, Any],
        needs: List[ProductNeed],
    ) -> List[str]:
        """Fields that, if unknown, change the recommendation (§6.1).

        We never guess amount/date/urgency. We only report what is genuinely
        missing for the selected needs.
        """
        gaps: List[str] = []
        request = request_text.lower()
        if ProductNeed.WORKING_CAPITAL in needs:
            if "amount_vnd" not in profile and not any(
                t in request for t in ("tỷ", "triệu", "vnd", "billion")
            ):
                gaps.append("funding_amount_vnd")
            if "tenor_months" not in profile:
                gaps.append("funding_tenor_months")
        if ProductNeed.CASH_MANAGEMENT in needs and not profile.get("cash_flow_status"):
            gaps.append("cash_flow_status")
        if not needs:
            gaps.append("product_need_unresolved")
        return gaps

    # -- Assembly ----------------------------------------------------------

    def run(
        self,
        request_text: str,
        profile: Dict[str, Any],
        retrieval_results: List[ProductRetrievalResult],
    ) -> Dict[str, Any]:
        """Build recommendations + citations for the resolved needs.

        Evidence items are constructed here exactly once and handed to the
        verifier by reference (no re-wrapping in the server).
        """
        request = request_text.lower()
        needs = self.select_needs(request_text, profile)
        selected_pids = [self._need_to_pid(n) for n in needs]

        retrieval = {item.product_id: item for item in retrieval_results}
        products: List[ProductRecommendation] = []
        evidences: List[EvidenceItem] = []

        for pid in selected_pids:
            product = get_entry(pid)
            meta = product["source_metadata"]
            total = self.score(pid, request, profile)
            retrieval_score = retrieval.get(pid).score if pid in retrieval else None

            products.append(ProductRecommendation(
                product_id=pid,
                name=product["name"],
                match_score=self.build_match_score(total, pid, request, profile),
                matching_reason=self.reason(pid, profile),
                prerequisites=product["prerequisites"],
                retrieval_score=retrieval_score,
            ))

            # One citation per product, grounded in the catalog eligibility text.
            evidences.append(EvidenceItem(
                agent="Product",
                claim=f"{product['name']} có điều kiện: {product['eligibility_rules']}",
                source_document_id=meta["document"],
                source_version=meta["effective_date"],
                section_or_page=meta["section"],
                quote=product["eligibility_rules"],
                validation_method=ValidationMethod.EXACT_MATCH,
                is_valid=False,  # set by EvidenceVerifier
            ))

        bundle_name = "Gói giải pháp doanh nghiệp tổng hợp" if len(products) > 1 else "Giải pháp doanh nghiệp"
        bundle_reason = (
            f"Dựa trên nhu cầu: {', '.join(p.name for p in products)}"
            if products else "Chưa xác định nhu cầu cụ thể"
        )

        return {
            "needs": [n.value for n in needs],
            "recommended_bundle": ProductBundle(
                bundle_name=bundle_name,
                products=products,
                bundle_reason=bundle_reason,
            ),
            "recommended_products": [p.product_id for p in products],
            "missing_parameters": self.detect_missing_parameters(request_text, profile, needs),
            "retrieval_query": request,
            "evidences": evidences,
            "citations": [e.model_dump() for e in evidences],
        }

    # -- Helpers -----------------------------------------------------------

    @staticmethod
    def _need_to_pid(need: ProductNeed) -> str:
        return {
            ProductNeed.PAYROLL: "PROD-PAYROLL",
            ProductNeed.CASH_MANAGEMENT: "PROD-CASH-MGMT",
            ProductNeed.COLLECTION: "PROD-COLLECTION",
            ProductNeed.WORKING_CAPITAL: "PROD-WORKING-CAPITAL",
        }[need]
