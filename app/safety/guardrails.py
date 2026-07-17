"""Input/output safety gates for prompt injection, PII and approval state."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from app.schemas.state import SharedCaseState


INJECTION_PATTERNS = (
    r"ignore\s+(all\s+)?previous",
    r"bỏ\s+qua\s+(mọi\s+)?chỉ\s+dẫn",
    r"system\s+prompt",
    r"gọi\s+(api\s+)?create[_ ]case",
    r"bypass\s+approval",
)


class GuardrailGate:
    def inspect_input(self, request_text: str, documents: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        document_text = " ".join(str(doc.get("text", "")) for doc in documents)
        combined = f"{request_text} {document_text}"
        flags = [pattern for pattern in INJECTION_PATTERNS if re.search(pattern, combined, re.IGNORECASE)]
        return {"allowed": not flags, "security_flags": flags, "sanitized_text": self.mask_pii(request_text)}

    @staticmethod
    def mask_pii(text: str) -> str:
        text = re.sub(r"\b\d{12,19}\b", "[SENSITIVE_NUMBER]", text or "")
        text = re.sub(r"(?i)\b(?:pin|mã pin)\s*[:=]?\s*\d{4,6}\b", "[PIN_REDACTED]", text)
        return text

    @staticmethod
    def can_execute(state: SharedCaseState) -> tuple[bool, str]:
        blocking = any(item.get("severity", "").lower() == "blocking" for item in state.legal_result.get("failed_checks", []))
        if blocking:
            return False, "Case còn lỗi pháp lý Blocking"
        if state.approval_status != "approved":
            return False, "Chưa có phê duyệt hợp lệ của RM"
        if not state.evidences or not all(item.is_valid for item in state.evidences):
            return False, "Bằng chứng chưa được xác minh đầy đủ"
        return True, "ok"

