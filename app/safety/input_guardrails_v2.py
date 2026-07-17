"""Deterministic input screening; retrieved text is always treated as untrusted data."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class InputSafetyResult:
    safe: bool
    flags: List[str]
    sanitized_text: str


_INJECTION = (
    r"ignore (all|previous) instructions",
    r"bỏ qua (mọi|tất cả|các) (chỉ dẫn|hướng dẫn)",
    r"system prompt",
    r"developer message",
    r"call .*tool",
)


def screen_input(text: str) -> InputSafetyResult:
    flags = ["PROMPT_INJECTION"] if any(re.search(pattern, text, re.IGNORECASE) for pattern in _INJECTION) else []
    sanitized = re.sub(r"\b\d{9,12}\b", "[REDACTED_ID]", text)
    sanitized = re.sub(r"\b\d{12,19}\b", "[REDACTED_ACCOUNT]", sanitized)
    return InputSafetyResult(safe=not flags, flags=flags, sanitized_text=sanitized)
