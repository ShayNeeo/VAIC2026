from fastapi.testclient import TestClient

from app.main import app


def test_login_issues_token_and_context_resolves_role():
    client = TestClient(app)
    response = client.post("/api/v2/auth/login", json={"employee_id": "MGR-HN-01", "password": "demo1234"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    context = client.get("/api/v2/me/context", headers={"Authorization": f"Bearer {token}"})
    assert context.status_code == 200
    assert context.json()["authorization_context"]["roles"] == ["manager"]


def test_login_rejects_bad_password():
    response = TestClient(app).post("/api/v2/auth/login", json={"employee_id": "RM-999", "password": "wrong"})
    assert response.status_code == 401


def test_tampered_session_token_is_rejected():
    client = TestClient(app)
    token = client.post("/api/v2/auth/login", json={"employee_id": "RM-999", "password": "demo1234"}).json()["access_token"]
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    response = client.get("/api/v2/me/context", headers={"Authorization": f"Bearer {tampered}"})
    assert response.status_code == 401
