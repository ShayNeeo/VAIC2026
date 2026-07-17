"""Deterministic Vietnamese text and entity normalization."""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "").strip()
    return re.sub(r"\s+", " ", text)


def fold_text(text: str) -> str:
    value = unicodedata.normalize("NFD", normalize_text(text).lower())
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn").replace("đ", "d")


def normalize_entity(entity_type: str, value: str) -> Any:
    value = normalize_text(value)
    folded = fold_text(value)
    if entity_type == "product":
        if any(token in folded for token in ("luong", "payroll")):
            return "PROD-PAYROLL"
        if any(token in folded for token in ("dong tien", "cash management", "cash pooling")):
            return "PROD-CASH-MGMT"
        if any(token in folded for token in ("thu ho", "chi ho", "nha cung cap", "bulk payment")):
            return "PROD-BULK-PAYMENT"
        if any(token in folded for token in ("von luu dong", "hmtd", "thau chi", "working capital")):
            return "PROD-WORKING-CAPITAL"
        return value
    if entity_type == "urgency":
        if any(token in folded for token in ("gap", "ngay", "khan", "urgent")):
            return "urgent"
        if "cao" in folded or "high" in folded:
            return "high"
        return "normal"
    if entity_type == "document":
        aliases = {
            "ubo": "ubo_information",
            "bctc": "financial_statements",
            "bao cao tai chinh": "financial_statements",
            "dang ky kinh doanh": "business_registration",
        }
        return aliases.get(folded, value)
    return value


_AMOUNT_PATTERN = re.compile(
    r"(?P<number>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unit>tỷ|ty|triệu|trieu|million|billion)?\s*"
    r"(?P<currency>vnd|đ|đồng|dong)?",
    re.IGNORECASE,
)


def extract_amount(text: str) -> Optional[Dict[str, Any]]:
    """Extract an explicitly stated amount and preserve the source text."""

    for match in _AMOUNT_PATTERN.finditer(normalize_text(text)):
        raw = match.group(0).strip()
        unit = fold_text(match.group("unit") or "")
        currency = match.group("currency")
        if not unit and not currency:
            continue
        try:
            number = Decimal(match.group("number").replace(",", "."))
        except InvalidOperation:
            continue
        multiplier = Decimal("1")
        if unit in {"ty", "billion"}:
            multiplier = Decimal("1000000000")
        elif unit in {"trieu", "million"}:
            multiplier = Decimal("1000000")
        return {"amount": int(number * multiplier), "currency": "VND", "original_text": raw}
    return None


def extract_tenor_months(text: str) -> Optional[Dict[str, Any]]:
    normalized = normalize_text(text)
    month_match = re.search(r"\b(\d{1,3})\s*(tháng|thang|month|months)\b", normalized, re.IGNORECASE)
    if month_match:
        return {"months": int(month_match.group(1)), "original_text": month_match.group(0)}
    year_match = re.search(r"\b(\d{1,2})\s*(năm|nam|year|years)\b", normalized, re.IGNORECASE)
    if year_match:
        return {"months": int(year_match.group(1)) * 12, "original_text": year_match.group(0)}
    return None
