"""Select at most one clarification with the highest decision value."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from app.schemas.v2.context_snapshot import ContextSnapshot
from app.schemas.v2.intent_result import IntentResult


@dataclass(frozen=True)
class Clarification:
    field: str
    question: str
    reason: str


_QUESTIONS: Dict[str, str] = {
    "customer_id": "Anh/chị xác nhận khách hàng doanh nghiệp cần xử lý là đơn vị nào?",
    "case_id": "Anh/chị muốn tiếp tục case nào?",
    "product_ids": "Anh/chị muốn kiểm tra nhóm sản phẩm nào trước?",
    "changed_artifacts": "Tài liệu hoặc thông tin nào vừa được bổ sung?",
    "recipient": "Phản hồi này dự kiến gửi cho người nhận nào?",
    "action_payload": "Anh/chị vui lòng mở bản xem trước hành động cần phê duyệt.",
    "objective": "Mục tiêu kinh doanh ưu tiên của khách hàng là gì?",
    "purpose": "Mục đích của phản hồi hoặc tác vụ này là gì?",
    "task_type": "Anh/chị muốn chuẩn bị loại task nào?",
}

_PRIORITY = {
    "customer_id": 100,
    "case_id": 95,
    "recipient": 90,
    "action_payload": 90,
    "product_ids": 80,
    "changed_artifacts": 75,
    "objective": 60,
    "purpose": 55,
    "task_type": 50,
}


def select_clarification(result: IntentResult, context: ContextSnapshot) -> Optional[Clarification]:
    high_conflicts = [item for item in context.conflicts if item.requires_confirmation]
    if high_conflicts:
        field = sorted(
            high_conflicts,
            key=lambda item: _PRIORITY.get(item.field, 0),
            reverse=True,
        )[0].field
        return Clarification(
            field=field,
            question=_QUESTIONS.get(field, f"Anh/chị xác nhận lại {field}?"),
            reason="Nguồn dữ liệu đang mâu thuẫn và trường này ảnh hưởng đến quyết định.",
        )

    missing: Iterable[str] = result.missing_information
    ranked = sorted(set(missing), key=lambda item: _PRIORITY.get(item, 0), reverse=True)
    if not ranked:
        return None
    field = ranked[0]
    return Clarification(
        field=field,
        question=_QUESTIONS.get(field, f"Anh/chị vui lòng bổ sung {field}."),
        reason=(
            "Thiếu dữ liệu cần cho bước hiện tại; hệ thống chỉ hỏi trường có tác động "
            "cao nhất để tránh RM nhập lặp lại."
        ),
    )
