"""Deterministic-first document classification and field extraction for the MVP."""

from __future__ import annotations

import re
import unicodedata
import uuid
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.schemas.v2.intake import ExtractedField, FieldValidationStatus


def fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn").replace("đ", "d")


def classify_document(filename: str, text: str) -> Tuple[str, float]:
    haystack = fold_text(f"{filename} {text[:6000]}")
    rules = (
        ("financial_statements", ("bao cao tai chinh", "bang can doi", "doanh thu thuan", "financial statement")),
        ("business_registration", ("dang ky doanh nghiep", "ma so thue", "giay chung nhan", "business registration")),
        ("ubo_information", ("nguoi dai dien", "chu so huu huong loi", "ubo", "uy quyen", "cccd")),
        ("payment_process", ("quy trinh thanh toan", "nha cung cap", "dai ly", "doi soat", "payroll", "erp")),
        ("meeting_note", ("bien ban", "ghi chu cuoc hop", "noi dung trao doi", "meeting note", "pain point")),
    )
    for document_type, signals in rules:
        if any(signal in haystack for signal in signals):
            return document_type, 0.95 if any(signal in fold_text(filename) for signal in signals) else 0.86
    return "other", 0.5


def detect_needs(text: str) -> List[str]:
    folded = fold_text(text)
    mapping = (
        ("payroll", ("chi luong", "tra luong", "payroll")),
        ("supplier_payment", ("thanh toan nha cung cap", "chi ho", "nha cung cap")),
        ("collection", ("thu ho", "dai ly", "doi soat tien ve")),
        ("cash_management", ("quan ly dong tien", "tien phan tan", "cash management")),
        ("working_capital", ("von luu dong", "thau chi", "han muc tin dung")),
        ("erp_integration", ("erp", "ket noi api", "tich hop he thong")),
    )
    return [name for name, signals in mapping if any(signal in folded for signal in signals)]


def detect_pain_points(text: str) -> List[str]:
    points: List[str] = []
    for raw in re.split(r"[\n\r.;]+", text):
        item = raw.strip(" -•\t")
        folded = fold_text(item)
        if item and any(signal in folded for signal in ("thu cong", "kho doi soat", "phan tan", "mat thoi gian", "sai sot")):
            points.append(item[:240])
    return list(dict.fromkeys(points))[:10]


def extract_document_fields(
    *,
    document_id: str,
    document_type: str,
    sections: Iterable[Dict[str, Any]],
) -> List[ExtractedField]:
    section_list = list(sections)
    joined = "\n".join(str(item.get("text") or "") for item in section_list)
    results: List[ExtractedField] = []

    def add(
        field_name: str,
        value: Any,
        match_text: str,
        *,
        confidence: float,
        impact: str = "medium",
        method: str = "regex",
    ) -> None:
        location, page = _find_location(section_list, match_text)
        results.append(
            ExtractedField(
                field_id=f"FIELD-{uuid.uuid4().hex[:12].upper()}",
                field_name=field_name,
                value=value,
                normalized_value=value,
                source_document_id=document_id,
                source_page=page,
                source_section=location,
                source_text_span=match_text[:300],
                extraction_method=method,
                confidence=confidence,
                validation_status=FieldValidationStatus.VALID if confidence >= 0.85 else FieldValidationStatus.NEEDS_REVIEW,
                decision_impact=impact,
                confirmed_by_rm=False,
            )
        )

    company = _search(joined, r"(?im)^\s*((?:công ty|cong ty)\s+(?:cổ phần|co phan|tnhh|trách nhiệm hữu hạn|trach nhiem huu han)[^\n,;]{2,120})")
    if company:
        add("company_identity.name", company[0].strip(), company[0], confidence=0.91, impact="high")

    tax = _search(joined, r"(?i)(?:mã số thuế|ma so thue|mst)\s*[:#-]?\s*([0-9]{10}(?:-[0-9]{3})?)")
    if tax:
        add("company_identity.tax_code", tax[0], tax[1], confidence=0.99, impact="high", method="regex_validated")

    employees = _search(joined, r"(?i)([0-9][0-9.,]{0,8})\s*(?:nhân viên|nhan vien|nhân sự|nhan su|người lao động|nguoi lao dong)")
    if employees:
        add("business_profile.employees_count", _integer(employees[0]), employees[1], confidence=0.94, impact="high")

    revenue = _search(joined, r"(?i)(?:doanh thu(?:\s+thuần)?|doanh thu nam|annual revenue)\s*[:：]?\s*([0-9][0-9.,]*)\s*(tỷ|ty|triệu|trieu|đồng|dong|vnd)?")
    if revenue:
        add("business_profile.annual_revenue", _money(revenue[0], revenue[2]), revenue[1], confidence=0.93, impact="high", method="table_or_regex")

    suppliers = _search(joined, r"(?i)([0-9][0-9.,]{0,8})\s*(?:nhà cung cấp|nha cung cap)")
    if suppliers:
        add("payment_profile.supplier_count", _integer(suppliers[0]), suppliers[1], confidence=0.91)

    # Distributors/dealers ("đại lý") and customers ("khách hàng") are
    # different business concepts and must not share one field -- a prior
    # version of this regex matched both under collection_profile.customer_count,
    # which meant e.g. "40 đại lý" was silently reported as a customer count.
    # Neither pattern matches "chi nhánh" (branch), which is a third concept.
    distributors = _search(
        joined, r"(?i)([0-9][0-9.,]{0,8})\s*(?:đại lý|dai ly|nhà phân phối|nha phan phoi|điểm phân phối|diem phan phoi)"
    )
    if distributors:
        add("collection_profile.distributor_count", _integer(distributors[0]), distributors[1], confidence=0.9)

    customers = _search(joined, r"(?i)([0-9][0-9.,]{0,8})\s*(?:khách hàng|khach hang)")
    if customers:
        add("collection_profile.customer_count", _integer(customers[0]), customers[1], confidence=0.9)

    accounts = _search(joined, r"(?i)([0-9][0-9.,]{0,8})\s*(?:tài khoản|tai khoan|đơn vị thành viên|don vi thanh vien)")
    if accounts:
        add("business_profile.account_or_unit_count", _integer(accounts[0]), accounts[1], confidence=0.9, impact="high")

    years = _search(joined, r"(?i)(?:hoạt động|hoat dong)\s*(?:liên tục|lien tuc)?\s*([0-9]{1,3})\s*năm")
    if years:
        add("business_profile.operating_years", int(years[0]), years[1], confidence=0.9, impact="high")

    # Legal representative name -- captures up to the next comma/period/
    # newline so a trailing title ("..., Giám đốc") is not folded into the
    # name itself. re.search takes the first (leftmost) match only: if a
    # document names multiple people, the first mention wins, consistent
    # with every other single-value field in this extractor.
    representative = _search(
        joined,
        r"(?i)(?:người đại diện theo pháp luật|nguoi dai dien theo phap luat|"
        r"người đại diện|nguoi dai dien|đại diện|dai dien)\s*[:\-]?\s*(?:ông|bà)?\s*([^\n,;.]{2,60})",
    )
    if representative:
        add("legal_profile.legal_representative", representative[0].strip(), representative[1], confidence=0.88, impact="high")

    folded = fold_text(joined)
    if document_type == "ubo_information" and any(term in folded for term in ("ubo da xac minh", "chu so huu huong loi da xac minh", "ubo verified")):
        add("legal_profile.ubo_status", "verified", "UBO đã xác minh", confidence=0.95, impact="high", method="keyword_validated")

    if document_type == "financial_statements":
        period = _search(joined, r"(?i)(?:năm tài chính|nam tai chinh|kỳ báo cáo|ky bao cao|financial year)\s*[:：]?\s*(20[0-9]{2})")
        if period:
            add("financing_profile.reporting_period", period[0], period[1], confidence=0.96, impact="high")

    needs = detect_needs(joined)
    if needs:
        add("explicit_needs", needs, ", ".join(needs), confidence=0.82 if document_type == "meeting_note" else 0.76, impact="medium", method="keyword")
    pain_points = detect_pain_points(joined)
    if pain_points:
        add("pain_points", pain_points, " | ".join(pain_points), confidence=0.8, impact="low", method="sentence_keyword")

    # Named, specific ERP products only -- the bare word "ERP" is a category,
    # not a system name. A prior version of this regex included "ERP" itself
    # in the capture group, so "muốn kết nối ERP nhưng chưa có hệ thống ERP
    # nào" (customer has NO system, just wants one) was reported as
    # technology_profile.erp_system="ERP", i.e. a fabricated current-system
    # fact. The *need* for ERP integration is still captured, correctly and
    # separately, via detect_needs()'s "erp_integration" signal below.
    erp = _search(joined, r"(?i)(?:hệ thống|he thong|phần mềm|phan mem)?\s*(SAP|Oracle|MISA|Odoo|NetSuite|Fast|Bravo)\b")
    if erp:
        add("technology_profile.erp_system", erp[0].upper(), erp[1], confidence=0.82, impact="low", method="keyword")
    return results


def _search(text: str, pattern: str) -> Optional[Tuple[str, str, str]]:
    match = re.search(pattern, text)
    if not match:
        return None
    groups = match.groups()
    first = groups[0] if groups else match.group(0)
    unit = groups[1] if len(groups) > 1 and groups[1] else ""
    return str(first), match.group(0), str(unit)


def _integer(value: str) -> int:
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits or "0")


def _money(value: str, unit: str) -> int:
    cleaned = value.strip().replace(" ", "")
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    elif cleaned.count(".") > 1 or cleaned.count(",") > 1:
        cleaned = re.sub(r"[^0-9]", "", cleaned)
    else:
        cleaned = cleaned.replace(",", "")
    amount = float(cleaned)
    folded_unit = fold_text(unit or "")
    if "ty" in folded_unit:
        amount *= 1_000_000_000
    elif "trieu" in folded_unit:
        amount *= 1_000_000
    return int(amount)


def _find_location(sections: List[Dict[str, Any]], needle: str) -> Tuple[str, Optional[int]]:
    folded_needle = fold_text(needle)[:80]
    for section in sections:
        if folded_needle and folded_needle in fold_text(str(section.get("text") or "")):
            location = str(section.get("location") or "document")
            page = section.get("metadata", {}).get("page")
            return location, int(page) if isinstance(page, int) else None
    return "document", None
