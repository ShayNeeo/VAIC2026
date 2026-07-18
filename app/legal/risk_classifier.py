"""Risk Classifier (L8).

Phân loại rủi ro (low/medium/high) và xác định xem có cần sự can thiệp
(review) của con người không.
"""

from typing import Any, Dict, List

from .models import LegalCheckOutput, ProductEligibilityResult


class RiskClassifier:
    """Xác định mức độ rủi ro dựa trên tổng hợp các vi phạm."""

    def classify_risk(
        self, 
        eligibility_results: List[ProductEligibilityResult],
        conflicts: List[Dict[str, Any]],
        watchlist_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Tính toán risk_level và review_required."""
        
        risk_level = "low"
        review_required = False
        reasons = []

        # 1. Watchlist / Sanctions
        if watchlist_result and watchlist_result.get("match_found"):
            risk_level = "high"
            review_required = True
            reasons.append("Watchlist / Sanctions match")
            
        # 2. Conflicts
        if conflicts:
            risk_level = max(risk_level, "medium")  # At least medium
            for conflict in conflicts:
                if conflict.get("severity") == "high":
                    risk_level = "high"
                if conflict.get("action") == "pending_review":
                    review_required = True
            reasons.append(f"Có {len(conflicts)} data/policy conflict(s)")

        # 3. Rule Evaluations
        has_blocking = False
        has_pending_review = False
        
        for res in eligibility_results:
            for rule in res.blocking_rules:
                has_blocking = True
                if rule.status == "pending_review":
                    has_pending_review = True
                
                if rule.priority <= 2:  # Priority 1 (Sanction), 2 (Legal Block)
                    risk_level = "high"
                elif risk_level == "low" and rule.priority <= 4:
                    risk_level = "medium"
                    
        if has_pending_review:
            review_required = True
            reasons.append("Có rule yêu cầu manual review (pending_review)")
            
        if has_blocking and risk_level == "low":
            risk_level = "medium"

        return {
            "risk_level": risk_level,
            "review_required": review_required,
            "reasons": reasons
        }
