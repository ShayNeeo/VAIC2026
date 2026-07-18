"""End-to-end regression test driving the specialist-review action surface
through the REAL async V2WorkflowEngine pipeline (intent extraction ->
product matching -> eligibility -> evidence validation -> risk gate), not
the hand-built SharedCaseState fixture every test in
tests/unit/test_v2_specialist_review.py uses (_seed_pending_review_case()).

Why this file exists: docs/SPECIALIST_REVIEW_FOCUSED_AUDIT.md section 2
found that the one path connecting "RM corrects a field via the real
PATCH /cases/{case_id}/context endpoint" to "case reaches PENDING_REVIEW
with human_review_allowed=True" had never been exercised end-to-end -- the
audit's own probe script could not get past the PATCH step because
app/workflow/impact.py routed 4 of the 8 declared-correctable fields
(including ubo_status, the only field with a human_review_allowed=True
rule attached) into a full re-run that V2WorkflowEngine.resume() always
rejects. That bug is fixed in app/workflow/impact.py (see
CONTEXT_CORRECTION_POLICIES); this test proves the full path now works,
via real HTTP calls through the real app, matching this project's "no
bia" (no fabricated result) discipline.

DB isolation: same pattern as tests/unit/test_v2_specialist_review.py and
tests/unit/test_v2_router_db_isolation.py -- a fresh temp SQLite file per
test via monkeypatch, never data/state/v2.sqlite3.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.config as app_config
import app.storage.employee_db as employee_db
from app.main import app

WORKING_CAPITAL_MESSAGE = (
    "Doanh nghiệp cần vay vốn lưu động để mở rộng sản xuất, đã hoạt động nhiều năm."
)

BUSINESS_REGISTRATION = {
    "document_id": "DOC-REG",
    "document_type": "business_registration",
    "version": "1",
    "status": "verified",
    "access_scope": {"branch": "HN01"},
}

# A genuinely FAILED (not missing) ubo_status: RULE-CREDIT-UBO-001's
# operator is one_of(["complete", "verified"]); app/eligibility/engine.py's
# _execute() only treats a value as "missing" (-> PENDING_INFORMATION) when
# it is None or normalizes to one of a specific set of "not yet verified"
# strings. This value is neither, so it must normalize to FAILED.
UBO_DISPUTED_VALUE = "Có xung đột thông tin chưa giải quyết"


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "specialist_review_e2e.sqlite3"
    monkeypatch.setattr(app_config.settings, "V2_DB_PATH", str(db_path))
    employee_db.init_employee_db()
    yield db_path


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def rm_headers(employee="RM-999", session="SESS-ABC") -> dict:
    return {"X-Employee-ID": employee, "X-Session-ID": session}


def bearer(demo_token: str) -> dict:
    return {"Authorization": f"Bearer {demo_token}"}


LEGAL = bearer("demo-spec-legal-001")


def _create_working_capital_case(client: TestClient) -> dict:
    response = client.post(
        "/api/v2/cases",
        headers=rm_headers(),
        json={"message": WORKING_CAPITAL_MESSAGE, "documents": [BUSINESS_REGISTRATION]},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["case"]["product_result"]["recommendations"][0]["product_id"] == "PROD-WORKING-CAPITAL"
    return body


def test_ubo_context_correction_reaches_downstream_eligibility_not_rejected(client):
    """The narrow regression for the impact.py bug itself: correcting
    ubo_status must resolve to the eligibility branch (not be rejected),
    and must not be forced through collect_context."""
    created = _create_working_capital_case(client)
    case_id = created["case"]["case_id"]

    response = client.patch(
        f"/api/v2/cases/{case_id}/context",
        headers=rm_headers(),
        json={
            "field": "customer.attributes.ubo_status",
            "new_value": UBO_DISPUTED_VALUE,
            "reason": "RM doi chieu ho so UBO, phat hien xung dot chua giai quyet.",
            "expected_state_version": created["state_version"],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["impacted_nodes"] == ["evaluate_eligibility", "validate_evidence", "prepare_operations"]


@pytest.mark.parametrize(
    "field_name",
    [
        "employees_count",
        "annual_revenue",
        "cash_flow_status",
        "account_or_unit_count",
        "operating_years",
        "has_bad_debt_12m",
        "ubo_status",
        "name",
    ],
)
def test_every_declared_correctable_field_is_actually_accepted(client, field_name):
    """Acceptance criterion (P0, per code-review response #4): all eight
    fields app/api/v2/router.py::correct_context declares correctable via
    CONTEXT_CORRECTION_POLICIES must be genuinely correctable through the
    real endpoint -- none may 409 CONTEXT_CORRECTION_REJECTED. Before the
    fix, exactly operating_years/has_bad_debt_12m/ubo_status/name failed
    this (see docs/SPECIALIST_REVIEW_FOCUSED_AUDIT.md section 2.1)."""
    created = _create_working_capital_case(client)
    case_id = created["case"]["case_id"]

    new_value = {
        "employees_count": 42,
        "annual_revenue": 120_000_000_000,
        "cash_flow_status": "on_dinh",
        "account_or_unit_count": 5,
        "operating_years": 7,
        "has_bad_debt_12m": False,
        "ubo_status": UBO_DISPUTED_VALUE,
        "name": "Cong ty TNHH ABC (da xac minh ten)",
    }[field_name]

    response = client.patch(
        f"/api/v2/cases/{case_id}/context",
        headers=rm_headers(),
        json={
            "field": f"customer.attributes.{field_name}",
            "new_value": new_value,
            "reason": "Acceptance probe for CONTEXT_CORRECTION_POLICIES coverage.",
            "expected_state_version": created["state_version"],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["impacted_nodes"], "must resolve to a non-empty resume plan, not silently no-op"


def test_ubo_block_flows_through_real_pipeline_to_legal_clearance_approval_and_execution(client):
    """The full acceptance scenario from the code-review response: create ->
    engine routes PROD-WORKING-CAPITAL -> PATCH ubo_status to a real FAILED
    value -> engine resume -> pending_review with legal_specialist required
    and human_review_allowed=True -> Legal Specialist clears with findings
    -> pending_approval -> RM approves -> RM executes -> audit trail
    records every step. No step here seeds SharedCaseState by hand."""
    created = _create_working_capital_case(client)
    case_id = created["case"]["case_id"]
    version = created["state_version"]

    corrected = client.patch(
        f"/api/v2/cases/{case_id}/context",
        headers=rm_headers(),
        json={
            "field": "customer.attributes.ubo_status",
            "new_value": UBO_DISPUTED_VALUE,
            "reason": "RM doi chieu ho so UBO, phat hien xung dot chua giai quyet.",
            "expected_state_version": version,
        },
    )
    assert corrected.status_code == 200, corrected.text
    corrected_body = corrected.json()
    version = corrected_body["state_version"]
    case_after_correction = corrected_body["case"]

    assert case_after_correction["status"] == "pending_review"
    risk_result = case_after_correction["risk_gate_result"]
    assert risk_result["outcome"] == "need_review"
    assert "legal_specialist" in risk_result["required_reviewer_roles"]
    assert risk_result["human_review_allowed"] is True
    assert "RULE-CREDIT-UBO-001" in risk_result["triggered_rules"]

    review_context = client.get(f"/api/v2/cases/{case_id}/review-context", headers=LEGAL)
    assert review_context.status_code == 200, review_context.text
    assert "legal_specialist" in review_context.json()["required_reviewer_roles"]

    # Stale expected_case_version must 409, not silently apply against a
    # different version than the reviewer actually looked at.
    stale = client.post(
        f"/api/v2/cases/{case_id}/specialist-reviews",
        headers=LEGAL,
        json={
            "review_type": "legal_specialist",
            "decision": "cleared",
            "summary": "Da doi chieu doc lap voi ho so UBO goc.",
            "findings": [{"code": "UBO_INDEPENDENTLY_VERIFIED", "severity": "medium", "message": "Xac minh qua ho so goc."}],
            "expected_case_version": version + 1,
        },
    )
    assert stale.status_code == 409, stale.text
    assert stale.json()["error"]["code"] == "CASE_VERSION_CONFLICT"

    cleared = client.post(
        f"/api/v2/cases/{case_id}/specialist-reviews",
        headers=LEGAL,
        json={
            "review_type": "legal_specialist",
            "decision": "cleared",
            "summary": "Da doi chieu doc lap voi ho so UBO goc.",
            "findings": [{"code": "UBO_INDEPENDENTLY_VERIFIED", "severity": "medium", "message": "Xac minh qua ho so goc."}],
            "expected_case_version": version,
        },
    )
    assert cleared.status_code == 201, cleared.text
    cleared_body = cleared.json()
    assert cleared_body["case_status_changed"] is True
    assert cleared_body["case_status"] == "pending_approval"
    version = cleared_body["case_version"]

    history = client.get(f"/api/v2/cases/{case_id}/specialist-reviews", headers=rm_headers())
    assert history.status_code == 200, history.text
    assert [item["decision"] for item in history.json()] == ["cleared"]

    preview = client.post(f"/api/v2/cases/{case_id}/approval-preview", headers=rm_headers())
    assert preview.status_code == 200, preview.text

    approved = client.post(
        f"/api/v2/cases/{case_id}/approve",
        headers=rm_headers(),
        json={"expected_state_version": version},
    )
    assert approved.status_code == 200, approved.text
    approved_body = approved.json()
    token = approved_body["approval_token"]
    version = approved_body["state_version"]

    executed = client.post(
        f"/api/v2/cases/{case_id}/execute",
        headers={**rm_headers(), "X-Approval-Token": token},
        json={"idempotency_key": f"{case_id}:create_crm_case:1", "expected_state_version": version},
    )
    assert executed.status_code == 200, executed.text
    executed_body = executed.json()
    assert executed_body["status"] == "completed"
    assert executed_body["result"]["crm_case_id"].startswith("SHB-CRM-")

    trace = client.get(f"/api/v2/cases/{case_id}/trace", headers=rm_headers())
    assert trace.status_code == 200, trace.text
    trace_body = trace.json()
    assert trace_body["audit_chain_valid"] is True
    persistent_actions = [item["action"] for item in trace_body["persistent_events"]]
    assert persistent_actions == [
        "case_created",
        "context_corrected",
        "specialist_review_cleared",
        "payload_approved",
        "actions_executed",
    ]
