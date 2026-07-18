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
        "Đạt, không đạt hay còn thiếu?",
        "Hành động ưu tiên",
        "Nguồn chứng minh kết luận",
        "Dữ liệu kỹ thuật JSON",
    ):
        assert label in html


def test_workspace_contains_four_guided_cases_and_expected_outputs():
    """"Case mẫu có hướng dẫn" (app/static/index.html) is a dropdown
    (#scenario) plus two empty containers (#scenarioGuide, #expectedOutput)
    that app.js fills in at runtime from its SCENARIOS data object, once
    the user picks a case -- there is no default selection, so a
    server-rendered fetch of "/" legitimately shows empty guide/output
    boxes; that is correct behavior, not a bug (a real browser only shows
    guide text after a user picks a scenario, same as this page should).

    The 4 case labels and "Output kỳ vọng của case mẫu" are static page
    content (the <option> list and an <h3>), so they're checked against
    "/" like any other static text. "Bổ sung hồ sơ UBO và BCTC" and
    "RM phê duyệt tạo case/task" only exist as JS string literals inside
    app.js's SCENARIOS/renderActionButtons -- TestClient never executes
    JavaScript, so they can only be observed by fetching the script that a
    real browser would also fetch (referenced via <script src="/static/app.js">
    in index.html). This still verifies the exact same content is actually
    served to a client; it does not weaken what the test checks."""
    html = TestClient(app).get("/").text
    for label in (
        "Case 1 · Payroll đủ điều kiện sơ bộ",
        "Case 2 · Payroll + vốn lưu động thiếu hồ sơ",
        "Case 3 · Nhu cầu cần làm rõ",
        "Case 4 · Yêu cầu không an toàn",
        "Output kỳ vọng của case mẫu",
    ):
        assert label in html
    assert '<script src="/static/app.js"' in html

    app_js = TestClient(app).get("/static/app.js").text
    for label in (
        "Bổ sung hồ sơ UBO và BCTC",
        "RM phê duyệt tạo case/task",
    ):
        assert label in app_js
