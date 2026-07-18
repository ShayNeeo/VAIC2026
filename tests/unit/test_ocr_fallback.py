"""Local OCR fallback for scanned/image PDFs (app/knowledge/ocr.py,
app/knowledge/parsers.py::ocr_pdf_sections, and the NEEDS_OCR path in
app/intake/service.py::add_document). Skips entirely when the OCR
toolchain (Tesseract binary + language data) is not usable on the machine
running the suite -- OCR is a real, environment-dependent capability (a
native binary, not a pip package alone), not something to fake with a
mock, and the rest of this repo's test suite must stay runnable on a
machine without Tesseract installed.

Synthetic test PDFs are built by rendering real business-domain sentences
(lending/cho vay, cash management/quản lý dòng tiền, guarantee for
logistics clients/bảo lãnh logistics, digital banking/ngân hàng số -- the
product scope this workspace focuses on) into a PNG with a real
Vietnamese-capable system font, then embedding that PNG as the only
content of a PDF page (no text layer) via PyMuPDF -- i.e. a real "scanned
document" shape, not a mock object.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v2.router import create_router
from app.knowledge.ocr import is_ocr_available
from app.knowledge.parsers import extraction_quality, ocr_pdf_sections
from app.observability.runtime import JsonEventLogger
from app.storage.repository import V2Repository

pytestmark = pytest.mark.skipif(
    not is_ocr_available(),
    reason="Tesseract OCR toolchain (binary + tessdata) not available in this environment",
)

HEADERS = {"X-Employee-ID": "RM-999", "X-Session-ID": "SESS-MP"}

_FONT_CANDIDATES = [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\tahoma.ttf", r"C:\Windows\Fonts\segoeui.ttf"]


def _render_scanned_pdf(lines: list[str]) -> bytes:
    """A PDF whose only page content is a rasterized PNG of `lines` --
    pypdf's extract_text() finds nothing on it (no text layer), exactly
    like a real scanned business document."""
    import fitz
    from PIL import Image, ImageDraw, ImageFont

    font = None
    for candidate in _FONT_CANDIDATES:
        if Path(candidate).exists():
            font = ImageFont.truetype(candidate, 28)
            break
    if font is None:
        font = ImageFont.load_default()

    width, height = 1200, 90 + 50 * len(lines)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    for i, line in enumerate(lines):
        draw.text((30, 30 + i * 50), line, fill="black", font=font)
    buf = io.BytesIO()
    image.save(buf, format="PNG")

    doc = fitz.open()
    page = doc.new_page(width=width, height=height)
    page.insert_image(page.rect, stream=buf.getvalue())
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _blank_scanned_pdf() -> bytes:
    import fitz
    from PIL import Image

    image = Image.new("RGB", (600, 400), "white")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    doc = fitz.open()
    page = doc.new_page(width=600, height=400)
    page.insert_image(page.rect, stream=buf.getvalue())
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


LENDING_DOC_LINES = [
    "HOP DONG TIN DUNG CHO VAY VON LUU DONG",
    "Han muc bao lanh danh cho doanh nghiep logistics",
    "Dich vu quan ly dong tien va ngan hang so SHB",
]


def test_is_ocr_available_reports_true_when_pytest_marker_ran():
    assert is_ocr_available() is True


def test_ocr_pdf_sections_extracts_text_from_scanned_lending_document():
    pdf_bytes = _render_scanned_pdf(LENDING_DOC_LINES)
    sections = ocr_pdf_sections(pdf_bytes)
    assert len(sections) == 1
    text_upper = sections[0].text.upper()
    assert "TIN DUNG" in text_upper or "CHO VAY" in text_upper
    assert sections[0].metadata["type"] == "pdf_ocr"
    assert 0.0 <= sections[0].metadata["ocr_confidence"] <= 1.0

    report = extraction_quality(sections)
    assert report["publishable"] is True


def test_ocr_pdf_sections_on_blank_scan_yields_unpublishable_quality():
    pdf_bytes = _blank_scanned_pdf()
    sections = ocr_pdf_sections(pdf_bytes)
    report = extraction_quality(sections)
    assert report["publishable"] is False


def _client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.include_router(
        create_router(
            repository=V2Repository(tmp_path / "state.sqlite3"),
            event_logger=JsonEventLogger(tmp_path / "events.jsonl"),
        )
    )
    return TestClient(app)


def _create_case(http: TestClient) -> dict:
    response = http.post(
        "/api/v2/sales-cases",
        headers={**HEADERS, "Idempotency-Key": "create-ocr-test"},
        json={
            "company_name": "Cong ty Logistics Minh Phat",
            "tax_code": "0109988665",
            "industry": "Logistics",
            "need_text": "Can bao lanh hop dong va han muc von luu dong.",
            "rm_note": "Synthetic OCR E2E",
            "priority": "normal",
            "current_products": [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_scanned_lending_document_upload_is_ocr_accepted_end_to_end(tmp_path):
    http = _client(tmp_path)
    case = _create_case(http)
    pdf_bytes = _render_scanned_pdf(LENDING_DOC_LINES)

    response = http.post(
        f"/api/v2/sales-cases/{case['case_id']}/documents",
        headers=HEADERS,
        files=[("files", ("scanned_lending_contract.pdf", pdf_bytes, "application/pdf"))],
    )
    assert response.status_code == 200, response.text
    receipt = response.json()["documents"][0]
    assert receipt["status"] == "uploaded"
    assert receipt["quality"]["ocr_used"] is True
    assert receipt["quality"]["ocr_mean_confidence"] > 0


def test_blank_scanned_document_upload_still_needs_ocr_review(tmp_path):
    """OCR must not manufacture text where there is none -- a genuinely
    blank scan stays NEEDS_OCR/blocked exactly as it did before OCR
    existed, now carrying ocr_attempted metadata for observability."""
    http = _client(tmp_path)
    case = _create_case(http)
    pdf_bytes = _blank_scanned_pdf()

    response = http.post(
        f"/api/v2/sales-cases/{case['case_id']}/documents",
        headers=HEADERS,
        files=[("files", ("blank_scan.pdf", pdf_bytes, "application/pdf"))],
    )
    assert response.status_code == 200, response.text
    receipt = response.json()["documents"][0]
    assert receipt["status"] == "needs_ocr"
    assert receipt["error_code"] == "OCR_REQUIRED"
    assert receipt["quality"].get("ocr_attempted") is True
