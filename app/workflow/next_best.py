"""Generate ranked, non-repetitive next questions and safe next actions."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Tuple

from app.schemas.v2.planning import NextBestAction, NextBestQuestion


DOCUMENT_LABELS = {
    "business_registration": "đăng ký doanh nghiệp hợp lệ",
    "financial_statements": "báo cáo tài chính năm gần nhất",
    "ubo_information": "thông tin chủ sở hữu hưởng lợi đã xác minh",
    "capital_use_plan": "phương án sử dụng vốn",
    "tax_declarations": "tờ khai thuế gần nhất",
    "collateral_profile": "hồ sơ tài sản bảo đảm",
}


class NextBestService:
    def build(self, eligibility_result: Dict[str, Any]) -> Tuple[List[NextBestQuestion], List[NextBestAction]]:
        questions: List[NextBestQuestion] = []
        actions: List[NextBestAction] = []
        seen: set[str] = set()
        for product in eligibility_result.get("products", []):
            for rule in product.get("rules", []):
                status = str(rule.get("status"))
                if status != "pending_information":
                    continue
                target = str(rule.get("expected")) if rule.get("field") == "documents" else str(rule.get("field"))
                if target in seen:
                    continue
                seen.add(target)
                label = DOCUMENT_LABELS.get(target, target.replace("_", " "))
                is_document = rule.get("field") == "documents"
                questions.append(
                    NextBestQuestion(
                        question_id=f"NBQ-{uuid.uuid4().hex[:10].upper()}",
                        question=f"RM có thể bổ sung {label} không?" if is_document else f"RM vui lòng xác nhận thông tin {label}?",
                        reason=f"Rule {rule.get('rule_id')} chưa thể kết luận cho {product.get('product_id')}",
                        target_field=f"documents.{target}" if is_document else f"customer.{target}",
                        source_gap=target,
                        decision_impact="high",
                        priority=1,
                        answer_type="document" if is_document else "value",
                        blocking_steps=["legal", "approval"],
                    )
                )
                actions.append(
                    NextBestAction(
                        action_id=f"NBA-{uuid.uuid4().hex[:10].upper()}",
                        action_type="collect_document" if is_document else "confirm_customer_field",
                        title=f"Thu thập {label}" if is_document else f"Xác nhận {label}",
                        rationale=f"Gỡ blocker {rule.get('failure_code') or rule.get('rule_id')}",
                        owner_role="RM",
                        sla_hours=24,
                        dependencies=[],
                        risk_level="low",
                        requires_approval=False,
                        payload_preview={"target": target, "product_id": product.get("product_id")},
                    )
                )
        outcome = str(eligibility_result.get("overall_status") or "pending_review")
        if outcome == "passed":
            actions.append(
                NextBestAction(
                    action_id=f"NBA-{uuid.uuid4().hex[:10].upper()}",
                    action_type="review_and_approve",
                    title="Kiểm tra action payload và phê duyệt",
                    rationale="Các rule blocking đã đạt; vẫn cần RM duyệt trước khi tạo dữ liệu mock/CRM",
                    owner_role="RM",
                    sla_hours=8,
                    risk_level="high",
                    requires_approval=True,
                    payload_preview={"action": "create_opportunity_and_tasks"},
                )
            )
        elif outcome in {"failed", "pending_review"}:
            actions.append(
                NextBestAction(
                    action_id=f"NBA-{uuid.uuid4().hex[:10].upper()}",
                    action_type="escalate_review",
                    title="Chuyển chuyên viên kiểm tra hoặc chọn phương án thay thế",
                    rationale="Không được tự phê duyệt khi rule failed hoặc evidence chưa đủ",
                    owner_role="RM",
                    sla_hours=8,
                    risk_level="medium",
                    requires_approval=False,
                )
            )
        questions.sort(key=lambda item: (item.priority, item.target_field))
        return questions, actions
