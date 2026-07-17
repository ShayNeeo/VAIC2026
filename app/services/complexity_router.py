"""Deterministic routing between direct product RAG and multi-agent workflow."""

from __future__ import annotations


class ComplexityRouter:
    SERVICE_TERMS = ("payroll", "chi lương", "dòng tiền", "thu hộ", "chi hộ", "thấu chi", "vốn lưu động", "tín dụng")

    def route(self, request_text: str) -> str:
        text = (request_text or "").lower()
        intents = sum(1 for term in self.SERVICE_TERMS if term in text)
        high_risk = any(term in text for term in ("thấu chi", "vốn lưu động", "tín dụng", "kyc", "ubo"))
        return "complex" if intents > 1 or high_risk else "simple"

