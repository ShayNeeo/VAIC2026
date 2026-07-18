"""Versioned taxonomy for the Corporate RM workspace."""

from __future__ import annotations

from typing import Any, Dict

TAXONOMY_VERSION = "2.0.0"

INTENT_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "find_product": {
        "description": "Tìm sản phẩm hoặc bộ giải pháp phù hợp",
        "required_slots": ["customer_id", "objective"],
        "risk": "low",
    },
    "compare_products": {
        "description": "So sánh các sản phẩm ứng viên",
        "required_slots": ["product_ids"],
        "risk": "low",
    },
    "check_eligibility": {
        "description": "Kiểm tra điều kiện sản phẩm, tín dụng hoặc pháp lý",
        "required_slots": ["customer_id", "product_ids"],
        "risk": "high",
    },
    "check_missing_documents": {
        "description": "Kiểm tra hồ sơ còn thiếu cho case hoặc sản phẩm",
        "required_slots": ["customer_id"],
        "risk": "medium",
    },
    "resume_case": {
        "description": "Tiếp tục case sau khi có dữ liệu hoặc tài liệu mới",
        "required_slots": ["case_id", "changed_artifacts"],
        "risk": "medium",
    },
    "prepare_customer_response": {
        "description": "Chuẩn bị phản hồi nháp cho khách hàng",
        "required_slots": ["customer_id", "purpose"],
        "risk": "medium",
    },
    "prepare_case_task": {
        "description": "Chuẩn bị case hoặc task nháp",
        "required_slots": ["customer_id", "task_type"],
        "risk": "medium",
    },
    "approve_actions": {
        "description": "Phê duyệt payload hành động đã đóng băng",
        "required_slots": ["case_id", "action_payload"],
        "risk": "high",
    },
    "reject_actions": {
        "description": "Từ chối hành động đang chờ duyệt",
        "required_slots": ["case_id", "reason"],
        "risk": "high",
    },
    "status_lookup": {
        "description": "Xem trạng thái case hoặc task",
        "required_slots": ["case_id"],
        "risk": "low",
    },
    "out_of_scope": {
        "description": "Yêu cầu ngoài phạm vi workspace RM doanh nghiệp",
        "required_slots": [],
        "risk": "low",
    },
}

ALLOWED_RECOMMENDED_ACTIONS = [
    "continue_workflow",
    "call_context_tool",
    "defer_missing_field",
    "ask_clarification",
    "request_confirmation",
    "reject_out_of_scope",
    "escalate_human",
]


def is_known_intent(intent_id: str) -> bool:
    return intent_id in INTENT_TAXONOMY

