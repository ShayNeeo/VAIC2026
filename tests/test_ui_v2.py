"""Regression tests for the RM Workspace information hierarchy."""

from fastapi.testclient import TestClient

from app.main import app


def test_workspace_contains_login_and_verified_role_controls():
    html = TestClient(app).get("/").text
    for marker in ("loginScreen", "loginEmployee", "loginPassword", "roleBadge", "logoutButton"):
        assert marker in html


def test_workspace_exposes_a_clear_decision_reading_order():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    html = response.text
    for label in (
        "Tóm tắt case",
        "Tiến trình xử lý",
        "Đầu vào",
        "Kết luận xử lý",
        "AI hiểu khách hàng cần gì?",
        "Sản phẩm nào phù hợp?",
        "Kết quả pháp lý theo sản phẩm",
        "Hành động ưu tiên",
        "Nguồn chứng minh kết luận",
        "Dữ liệu kỹ thuật JSON",
    ):
        assert label in html


def test_workspace_contains_four_guided_cases_and_expected_outputs():
    html = TestClient(app).get("/").text
    for label in (
        "Case 1 · Payroll đủ điều kiện sơ bộ",
        "Case 2 · Payroll + vốn lưu động thiếu hồ sơ",
        "Case 3 · Nhu cầu cần làm rõ",
        "Case 4 · Yêu cầu không an toàn",
        "Output kỳ vọng của case mẫu",
        "Bổ sung hồ sơ UBO và BCTC",
        "RM phê duyệt payload cụ thể",
    ):
        assert label in html
