from fastapi.testclient import TestClient

from app.database import db
from app.main import app


client = TestClient(app)


def setup_function():
    db.clear()


def test_health_and_complex_case_lifecycle():
    assert client.get("/health").json()["status"] == "ok"
    created = client.post(
        "/api/v1/cases",
        json={
            "customer_id": "COMP-ABC",
            "rm_id": "RM-999",
            "request_text": "Mở dịch vụ Payroll và xin thấu chi vốn lưu động",
            "documents": [{"doc_id": "DOC-REG", "doc_type": "Giấy chứng nhận đăng ký doanh nghiệp", "status": "verified"}],
        },
    )
    assert created.status_code == 201
    case = created.json()
    assert case["final_status"] == "pending_information"

    resumed = client.post(
        f"/api/v1/cases/{case['case_id']}/resume",
        json={
            "rm_id": "RM-999",
            "documents": [
                {"doc_id": "DOC-UBO", "doc_type": "Thông tin chủ sở hữu hưởng lợi UBO", "status": "verified"},
                {"doc_id": "DOC-FS", "doc_type": "Báo cáo tài chính năm gần nhất", "status": "verified"},
            ],
        },
    )
    assert resumed.status_code == 200
    assert resumed.json()["final_status"] == "pending_approval"

    issued = client.post(f"/api/v1/cases/{case['case_id']}/approval-token", json={"rm_id": "RM-999"})
    assert issued.status_code == 200
    approved = client.post(
        f"/api/v1/cases/{case['case_id']}/approve",
        headers={"X-Approval-Token": issued.json()["approval_token"]},
        json={"rm_id": "RM-999", "comments": "OK"},
    )
    assert approved.status_code == 200
    assert approved.json()["final_status"] == "completed"


def test_wrong_rm_cannot_access_approval_flow():
    created = client.post(
        "/api/v1/cases",
        json={"customer_id": "COMP-XYZ", "rm_id": "RM-001", "request_text": "Tra cứu Payroll"},
    ).json()
    response = client.post(f"/api/v1/cases/{created['case_id']}/approval-token", json={"rm_id": "RM-OTHER"})
    assert response.status_code == 403

