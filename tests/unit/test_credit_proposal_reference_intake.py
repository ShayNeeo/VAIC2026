"""Verifies the existing generic document-intake pipeline accepts a real
RM-authored credit proposal memo (.docx) as a case attachment.

This is not a new document_type or extractor -- it exercises the same
/sales-cases/{case_id}/documents upload path already used for
business_registration/financial_statements uploads (see
tests/test_sales_cases_e2e.py), just with a real .docx payload instead of
a synthetic .txt string, to confirm parse_document_bytes + the document
assurance gate handle it end-to-end without special-casing."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v2.router import create_router
from app.observability.runtime import JsonEventLogger
from app.storage.repository import V2Repository

HEADERS = {"X-Employee-ID": "RM-999", "X-Session-ID": "SESS-MP"}

MOCK_PROPOSAL_PATH = (
    Path(__file__).resolve().parents[2] / "mock tờ trinh đề xuất của khách hàng.docx"
)


def _client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.include_router(
        create_router(
            repository=V2Repository(tmp_path / "state.sqlite3"),
            event_logger=JsonEventLogger(tmp_path / "events.jsonl"),
        )
    )
    return TestClient(app)


def test_rm_can_upload_real_credit_proposal_docx_as_case_document(tmp_path: Path):
    assert MOCK_PROPOSAL_PATH.exists(), f"missing fixture: {MOCK_PROPOSAL_PATH}"
    http = _client(tmp_path)
    draft = http.post(
        "/api/v2/sales-cases",
        headers={**HEADERS, "Idempotency-Key": "create-proposal-upload-test"},
        json={
            "company_name": "Công ty Cổ phần Thương mại và Công nghệ Bình Minh",
            "tax_code": "0101234567",
            "industry": "Bán buôn máy vi tính, thiết bị ngoại vi và phần mềm",
            "need_text": "Khách hàng cần vốn lưu động để nhập khẩu linh kiện điện tử.",
            "rm_note": "Đính kèm tờ trình đề xuất trước đó làm tài liệu tham khảo.",
            "priority": "normal",
            "current_products": [],
        },
    ).json()
    case_id = draft["case_id"]

    data = MOCK_PROPOSAL_PATH.read_bytes()
    response = http.post(
        f"/api/v2/sales-cases/{case_id}/documents",
        headers=HEADERS,
        files=[(
            "files",
            (
                "to_trinh_de_xuat_mau.docx",
                data,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        )],
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["documents"]) == 1
    receipt = payload["documents"][0]
    assert receipt["deduplicated"] is False
    # Must be readable (parsed) -- not rejected as MIME mismatch or
    # unsupported format. "quarantined" (held for RM review) is an
    # acceptable real outcome from the document-assurance gate; "failed"/
    # "dead_letter" would mean the docx itself could not be parsed at all.
    assert receipt["status"] not in {"failed", "dead_letter"}, receipt

    listed = http.get(f"/api/v2/sales-cases/{case_id}/documents", headers=HEADERS)
    assert listed.status_code == 200
    assert any(doc["document_id"] == receipt["document_id"] for doc in listed.json()["documents"])
