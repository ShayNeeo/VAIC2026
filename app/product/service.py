"""Grounded product recommendation; eligibility remains explicitly unknown."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from app.knowledge.models import RetrievalHit
from app.knowledge.service import ProductKnowledgeService


class ProductService:
    def __init__(self, knowledge: ProductKnowledgeService) -> None:
        self.knowledge = knowledge

    def recommend(
        self,
        query: str,
        *,
        branch: str,
        segment: Optional[str] = None,
        requested_product_ids: Optional[Sequence[str]] = None,
        customer_attributes: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
    ) -> Dict[str, Any]:
        # If the RM/customer explicitly named more products than the default
        # top_k=3 (e.g. the flagship "payroll + collections + cash management
        # + working capital" scenario), don't silently drop one of them --
        # a partial bundle defeats the whole "bộ giải pháp phù hợp" promise.
        # Unconstrained semantic search keeps the tighter default so a vague
        # query doesn't flood the bundle with low-relevance tail matches.
        effective_top_k = max(top_k, len(requested_product_ids)) if requested_product_ids else top_k
        hits = self.knowledge.search(
            query,
            branch=branch,
            segment=segment,
            product_ids=requested_product_ids,
            top_k=max(effective_top_k * 2, 5),
        )
        if not hits:
            # Graceful degradation: vector retrieval (key-free "local" provider
            # especially) can miss on a small synthetic corpus. Fall back to a
            # deterministic keyword match so a grounded recommendation still
            # surfaces instead of an empty bundle.
            hits = self.knowledge.keyword_search(query, top_k=max(effective_top_k * 2, 5))
        grouped: Dict[str, RetrievalHit] = {}
        for hit in hits:
            grouped.setdefault(hit.chunk.product_id, hit)
        recommendations: List[Dict[str, Any]] = []
        attrs = customer_attributes or {}
        for product_id, hit in list(grouped.items())[:effective_top_k]:
            context_bonus = self._context_bonus(product_id, attrs)
            match_score = round(min(1.0, 0.8 * hit.score + context_bonus), 6)
            chunk = hit.chunk
            # Safe-answer policy from the SHB manual (section 2.2 / safe-answer
            # rule): a recommendation is only whether the product is suitable to
            # advise on, NEVER whether the customer is approved. High-risk
            # products carry branch_behavior=REVIEW_REQUIRED and must not emit
            # any external action without human/Law/Credit sign-off.
            can_prepare = chunk.branch_behavior in {"READY_TO_PREPARE", "NEED_INFORMATION"}
            recommendations.append(
                {
                    "product_id": product_id,
                    "name": self._name_from_chunk(hit),
                    "match_score": match_score,
                    "score_components": {
                        "retrieval": hit.score,
                        "customer_context_bonus": context_bonus,
                    },
                    "matching_reason": self._reason(product_id, attrs),
                    "prerequisites": self._documents_from_chunk(hit),
                    "eligibility": "unknown",
                    "risk_level": chunk.risk_level,
                    "branch_behavior": chunk.branch_behavior,
                    "proceed": can_prepare,
                    "internal_required": chunk.internal_required,
                    "data_label": chunk.data_label,
                    "evidences": [self.knowledge.evidence(hit)],
                }
            )
        return {
            "status": "grounded" if recommendations else "no_grounded_product",
            "query": query,
            "recommendations": recommendations,
            "eligible_decision_deferred_to": "eligibility_module",
        }

    @staticmethod
    def _context_bonus(product_id: str, attrs: Dict[str, Any]) -> float:
        if product_id == "PROD-PAYROLL" and int(attrs.get("employees_count", 0)) >= 10:
            return 0.12
        if product_id == "PROD-CASH-MGMT" and float(attrs.get("annual_revenue", 0)) >= 50_000_000_000:
            return 0.12
        return 0.0

    @staticmethod
    def _name_from_chunk(hit: RetrievalHit) -> str:
        parts = hit.chunk.text.split(" | ")
        return parts[1] if len(parts) > 1 else hit.chunk.product_id

    @staticmethod
    def _documents_from_chunk(hit: RetrievalHit) -> List[str]:
        marker = "Hồ sơ: "
        if marker not in hit.chunk.text:
            return []
        return [item.strip() for item in hit.chunk.text.split(marker, 1)[1].split(";") if item.strip()]

    @staticmethod
    def _reason(product_id: str, attrs: Dict[str, Any]) -> str:
        if product_id == "PROD-PAYROLL" and attrs.get("employees_count"):
            return f"Nhu cầu khớp payroll và hồ sơ có {attrs['employees_count']} nhân sự."
        if product_id == "PROD-CASH-MGMT" and attrs.get("annual_revenue"):
            return "Nhu cầu dòng tiền khớp catalog và doanh thu hồ sơ đạt tín hiệu sàng lọc ban đầu."
        return "Nhu cầu khớp nội dung catalog còn hiệu lực; điều kiện sẽ được kiểm tra riêng."
