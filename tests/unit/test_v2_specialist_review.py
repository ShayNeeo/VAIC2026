"""HTTP-driven tests for the specialist-review action surface (Legal/Product/
Credit Specialist) added on top of the Role-Aware Employee Copilot layer,
plus the follow-up hardening round: human_review_allowed (block-override
classification), expected_case_version (optimistic concurrency), idempotent
RM notifications, and Operational Readiness (Operations' real, separate
action surface).

Context: docs/EMPLOYEE_ROLE_DESIGN_EVALUATION_REPORT.md found that Product,
Legal and Credit Specialist had correct identity/scope/queue isolation
but NO endpoint to ever act on a case -- every case-mutating endpoint in
app/api/v2/router.py is owned()-gated to the assigned RM only, and a
PENDING_REVIEW (need_review, risk_level=high) case had no defined human
resolver. A follow-up review then flagged that the first cut let ANY named
specialist clear ANY block, with no distinction between an absolute/factual
block and a genuine judgment call -- this file's first section exercises
that fix specifically. All via fastapi.testclient.TestClient against the
real app, per this project's "no bia" (no fabricated result) discipline --
every assertion here is a real HTTP response, not a direct Python function
call.

DB isolation: same isolated_employee_db fixture as test_v2_employee_context.py
-- a fresh temp SQLite file per test, never data/state/v2.sqlite3.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

import pytest
from fastapi.testclient import TestClient

import app.config as app_config
import app.storage.employee_db as employee_db
from app.config import settings
from app.main import app
from app.schemas.v2.examples import FULL_CONTEXT_SNAPSHOT, MINIMAL_SHARED_CASE_STATE
from app.schemas.v2.shared_case_state import ApprovalStatus, CaseStatus, Evidence, SharedCaseState
from app.storage.repository import V2Repository
from app.workflow.risk_gate import RiskGuardrailGate


@pytest.fixture(autouse=True)
def isolated_employee_db(tmp_path, monkeypatch):
    db_path = tmp_path / "specialist_review_test.sqlite3"
    monkeypatch.setattr(app_config.settings, "V2_DB_PATH", str(db_path))
    employee_db.init_employee_db()
    yield db_path


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def auth_headers(demo_token: str) -> dict:
    return {"Authorization": f"Bearer {demo_token}"}


RM = auth_headers("demo-rm-999")
LEGAL = auth_headers("demo-spec-legal-001")
PRODUCT = auth_headers("demo-spec-prod-001")
CREDIT = auth_headers("demo-spec-credit-001")
MANAGER = auth_headers("demo-mgr-hn-01")

A_FINDING = [{"code": "INDEPENDENTLY_VERIFIED", "severity": "medium", "message": "Da doi chieu voi tai lieu goc."}]


def _evidence(*, module: str, is_valid: bool, claim_id: str, human_review_allowed: bool = False) -> Dict[str, Any]:
    return Evidence(
        claim_id=claim_id, module=module, claim=f"claim-{claim_id}",
        source_document_id="DOC-1", source_version="1", location="section-1",
        quote="quote text", is_valid=is_valid, human_review_allowed=human_review_allowed,
    ).model_dump(mode="json")


def _seed_pending_review_case(
    repo: V2Repository,
    *,
    case_id: str,
    invalid_modules: List[str],
    employee_id: str = "RM-999",
    customer_id: str = "COMP-ABC",
    reviewable: bool = True,
) -> SharedCaseState:
    """Build a real SharedCaseState blocked exactly the way
    V2WorkflowEngine._analysis()/_apply_risk_gate() would have left it --
    invalid Evidence entries tagged by module (reviewable=True models a
    pure citation/grounding mismatch -- the only evidence sub-case
    V2WorkflowEngine ever marks human_review_allowed=True, see
    engine.py's _product_evidence/_legal_evidence), run through the REAL
    RiskGuardrailGate.evaluate() (not a hand-typed risk_gate_result) so
    required_reviewer_roles/human_review_allowed are genuine, then
    persisted via the same V2Repository the specialist-reviews endpoint
    reads from."""
    payload = deepcopy(MINIMAL_SHARED_CASE_STATE)
    payload["context"] = deepcopy(FULL_CONTEXT_SNAPSHOT)
    payload["context"]["employee"]["employee_id"] = employee_id
    payload["context"]["customer"]["customer_id"] = customer_id
    payload["case_id"] = case_id
    payload["trace_id"] = f"TRACE-{case_id}"
    payload["status"] = "pending_review"
    state = SharedCaseState.model_validate(payload)
    state.evidences = [
        Evidence.model_validate(
            _evidence(module=module, is_valid=False, claim_id=f"EV-{case_id}-{module}", human_review_allowed=reviewable)
        )
        for module in invalid_modules
    ]
    state.eligibility_result = {"overall_status": "passed", "products": []}
    state.product_result = {"recommendations": [{"product_id": "PROD-PAYROLL", "match_score": 0.9, "evidences": []}]}
    state.operations_result = None
    decision = RiskGuardrailGate.evaluate(eligibility_result=state.eligibility_result, evidences=state.evidences)
    state.risk_gate_result = decision.to_dict()
    repo.save_case(state, expected_version=0)
    return state


def _repo() -> V2Repository:
    return V2Repository(settings.V2_DB_PATH)


# ---------------------------------------------------------------------------
# Legal Specialist: real clearance power over an Eligibility/legal-domain block
# ---------------------------------------------------------------------------

def test_legal_specialist_can_clear_legal_block(client):
    _seed_pending_review_case(_repo(), case_id="CASE-LEGAL-1", invalid_modules=["Eligibility"])
    resp = client.post(
        "/api/v2/cases/CASE-LEGAL-1/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "UBO da xac minh du.", "findings": A_FINDING},
        headers=LEGAL,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["case_status_changed"] is True
    assert body["case_status"] == "pending_approval"
    assert body["advisory_only"] is False
    assert body["still_waiting_for"] == []

    case = _repo().get_case("CASE-LEGAL-1")
    assert case.state.status == CaseStatus.PENDING_APPROVAL
    assert case.state.approval.status == ApprovalStatus.PENDING
    assert case.state.operations_result is not None  # auto-prepared since it was None


def test_legal_specialist_can_request_more_information(client):
    _seed_pending_review_case(_repo(), case_id="CASE-LEGAL-2", invalid_modules=["Eligibility"])
    resp = client.post(
        "/api/v2/cases/CASE-LEGAL-2/specialist-reviews",
        json={
            "review_type": "legal_specialist", "decision": "needs_more_information",
            "summary": "Thieu ho so UBO.", "required_information": ["beneficial_owner_information"],
        },
        headers=LEGAL,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["case_status"] == "pending_information"
    case = _repo().get_case("CASE-LEGAL-2")
    assert case.state.status == CaseStatus.PENDING_INFORMATION
    assert any("beneficial_owner_information" in q["source_gap"] for q in case.state.next_best_questions)


def test_legal_specialist_clearing_does_not_itself_approve_or_execute(client):
    """Specialist review can clear the risk-gate block; it must NOT itself
    approve or execute anything -- that stays a separate, later RM-owned
    step (app/api/v2/router.py's owned()-gated /approve and /execute,
    untouched by this change). The case must land at PENDING_APPROVAL with
    approval.status still PENDING (never APPROVED/CONSUMED) -- i.e.
    clearing the block makes the case eligible for RM approval, it does
    not grant approval itself."""
    _seed_pending_review_case(_repo(), case_id="CASE-LEGAL-3", invalid_modules=["Eligibility"])
    clear = client.post(
        "/api/v2/cases/CASE-LEGAL-3/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING},
        headers=LEGAL,
    )
    assert clear.status_code == 201, clear.text
    case = _repo().get_case("CASE-LEGAL-3")
    assert case.state.status == CaseStatus.PENDING_APPROVAL
    assert case.state.approval.status == ApprovalStatus.PENDING
    assert case.state.approval.approver_id is None


# ---------------------------------------------------------------------------
# human_review_allowed: a specialist may only clear a block explicitly
# policy-flagged as override-able -- not any block in their own domain
# ---------------------------------------------------------------------------

def test_cannot_clear_a_block_that_is_not_human_review_allowed(client):
    """reviewable=False models a structural evidence problem (expired
    source, source not found, conflicting quotes) -- Legal owns the domain
    (required_reviewer_roles includes them) but must still be refused."""
    _seed_pending_review_case(_repo(), case_id="CASE-NONOVERRIDE-1", invalid_modules=["Eligibility"], reviewable=False)
    resp = client.post(
        "/api/v2/cases/CASE-NONOVERRIDE-1/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "Toi nghi la on.", "findings": A_FINDING},
        headers=LEGAL,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "BLOCK_NOT_OVERRIDABLE"
    case = _repo().get_case("CASE-NONOVERRIDE-1")
    assert case.state.status == CaseStatus.PENDING_REVIEW  # untouched


def test_cleared_decision_requires_findings_even_when_overridable(client):
    _seed_pending_review_case(_repo(), case_id="CASE-NOFINDING-1", invalid_modules=["Eligibility"])
    resp = client.post(
        "/api/v2/cases/CASE-NOFINDING-1/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "OK theo toi."},
        headers=LEGAL,
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "FINDINGS_REQUIRED"
    case = _repo().get_case("CASE-NOFINDING-1")
    assert case.state.status == CaseStatus.PENDING_REVIEW  # untouched


def test_hard_eligibility_rule_block_is_not_overridable_by_default(client):
    """A FAILED verdict driven by an absolute rule (bad-debt history, a
    numeric threshold, a missing mandatory document) must be refused even
    though Legal is the correctly-named domain owner -- only
    RULE-CREDIT-UBO-001 is policy-flagged human_review_allowed in
    data/synthetic/v2/eligibility_rules.json."""
    repo = _repo()
    payload = deepcopy(MINIMAL_SHARED_CASE_STATE)
    payload["context"] = deepcopy(FULL_CONTEXT_SNAPSHOT)
    payload["context"]["employee"]["employee_id"] = "RM-999"
    payload["context"]["customer"]["customer_id"] = "COMP-ABC"
    payload["case_id"] = "CASE-HARDRULE-1"
    payload["trace_id"] = "TRACE-CASE-HARDRULE-1"
    payload["status"] = "pending_review"
    state = SharedCaseState.model_validate(payload)
    state.eligibility_result = {
        "overall_status": "failed",
        "products": [
            {
                "product_id": "PROD-WORKING-CAPITAL",
                "rules": [{"rule_id": "RULE-CREDIT-BAD-DEBT-001", "severity": "blocking", "status": "failed", "human_review_allowed": False}],
            }
        ],
    }
    decision = RiskGuardrailGate.evaluate(eligibility_result=state.eligibility_result, evidences=[])
    state.risk_gate_result = decision.to_dict()
    repo.save_case(state, expected_version=0)

    resp = client.post(
        "/api/v2/cases/CASE-HARDRULE-1/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING},
        headers=LEGAL,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "BLOCK_NOT_OVERRIDABLE"


# ---------------------------------------------------------------------------
# Product Specialist: real clearance power, but only over Product evidence
# ---------------------------------------------------------------------------

def test_product_specialist_can_clear_product_evidence_block(client):
    _seed_pending_review_case(_repo(), case_id="CASE-PROD-1", invalid_modules=["Product"])
    resp = client.post(
        "/api/v2/cases/CASE-PROD-1/specialist-reviews",
        json={"review_type": "product_specialist", "decision": "cleared", "summary": "San pham phu hop.", "findings": A_FINDING},
        headers=PRODUCT,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["case_status"] == "pending_approval"


def test_product_specialist_cannot_submit_legal_review_type(client):
    """review_type must match the caller's own verified role -- claiming a
    different subtype must be rejected regardless of body content."""
    _seed_pending_review_case(_repo(), case_id="CASE-PROD-2", invalid_modules=["Eligibility"])
    resp = client.post(
        "/api/v2/cases/CASE-PROD-2/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING},
        headers=PRODUCT,
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "FORBIDDEN"
    case = _repo().get_case("CASE-PROD-2")
    assert case.state.status == CaseStatus.PENDING_REVIEW  # untouched


def test_specialist_cannot_review_case_not_waiting_for_their_role(client):
    """Product tries to clear a case that is blocked purely on an
    Eligibility(legal) reason -- must 409, not silently accept."""
    _seed_pending_review_case(_repo(), case_id="CASE-MISMATCH-1", invalid_modules=["Eligibility"])
    resp = client.post(
        "/api/v2/cases/CASE-MISMATCH-1/specialist-reviews",
        json={"review_type": "product_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING},
        headers=PRODUCT,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "SPECIALIST_REVIEW_NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# Credit Specialist: owns only Credit evidence/analysis review
# ---------------------------------------------------------------------------

def test_credit_specialist_can_clear_credit_evidence_block(client):
    _seed_pending_review_case(_repo(), case_id="CASE-CREDIT-1", invalid_modules=["Credit"])
    resp = client.post(
        "/api/v2/cases/CASE-CREDIT-1/specialist-reviews",
        json={"review_type": "credit_specialist", "decision": "cleared", "summary": "Da tham dinh dong tien.", "findings": A_FINDING},
        headers=CREDIT,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["advisory_only"] is False
    assert body["case_status_changed"] is True
    assert body["case_status"] == "pending_approval"


def test_credit_specialist_cannot_clear_legal_issue(client):
    _seed_pending_review_case(_repo(), case_id="CASE-CREDIT-2", invalid_modules=["Eligibility"])
    resp = client.post(
        "/api/v2/cases/CASE-CREDIT-2/specialist-reviews",
        json={"review_type": "credit_specialist", "decision": "cleared", "summary": "OK theo toi.", "findings": A_FINDING},
        headers=CREDIT,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "SPECIALIST_REVIEW_NOT_APPLICABLE"
    case = _repo().get_case("CASE-CREDIT-2")
    assert case.state.status == CaseStatus.PENDING_REVIEW


# ---------------------------------------------------------------------------
# Scope / security
# ---------------------------------------------------------------------------

def test_specialist_cannot_review_case_outside_customer_scope(client):
    _seed_pending_review_case(
        _repo(), case_id="CASE-SCOPE-1", invalid_modules=["Eligibility"], customer_id="COMP-NOT-IN-SCOPE",
    )
    resp = client.post(
        "/api/v2/cases/CASE-SCOPE-1/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING},
        headers=LEGAL,
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "FORBIDDEN"


def test_unknown_evidence_id_is_rejected(client):
    _seed_pending_review_case(_repo(), case_id="CASE-EV-1", invalid_modules=["Eligibility"])
    resp = client.post(
        "/api/v2/cases/CASE-EV-1/specialist-reviews",
        json={
            "review_type": "legal_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING,
            "evidence_ids": ["EV-DOES-NOT-EXIST"],
        },
        headers=LEGAL,
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "UNKNOWN_EVIDENCE_ID"


def test_manager_cannot_submit_specialist_review(client):
    _seed_pending_review_case(_repo(), case_id="CASE-MGR-1", invalid_modules=["Eligibility"])
    resp = client.post(
        "/api/v2/cases/CASE-MGR-1/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING},
        headers=MANAGER,
    )
    assert resp.status_code == 403


def test_blocked_decision_requires_findings(client):
    _seed_pending_review_case(_repo(), case_id="CASE-VAL-1", invalid_modules=["Eligibility"])
    resp = client.post(
        "/api/v2/cases/CASE-VAL-1/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "blocked", "summary": "Khong dat."},
        headers=LEGAL,
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "FINDINGS_REQUIRED"


# ---------------------------------------------------------------------------
# Blocked decision: terminal, no approval token ever issued
# ---------------------------------------------------------------------------

def test_blocked_review_does_not_issue_approval_token(client):
    _seed_pending_review_case(_repo(), case_id="CASE-BLOCK-1", invalid_modules=["Eligibility"])
    resp = client.post(
        "/api/v2/cases/CASE-BLOCK-1/specialist-reviews",
        json={
            "review_type": "legal_specialist", "decision": "blocked", "summary": "Vi pham quy dinh AML.",
            "findings": [{"code": "AML_RULE_VIOLATION", "severity": "high", "message": "Khong dat dieu kien AML."}],
        },
        headers=LEGAL,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["case_status"] == "rejected"

    case = _repo().get_case("CASE-BLOCK-1")
    assert case.state.status == CaseStatus.REJECTED
    assert case.state.approval.status == ApprovalStatus.REJECTED
    assert case.state.approval.payload_hash is None
    assert case.state.approval.approver_id is None


# ---------------------------------------------------------------------------
# Multi-domain block: BOTH named roles must clear before the case advances
# ---------------------------------------------------------------------------

def test_multi_domain_block_requires_both_roles_to_clear(client):
    _seed_pending_review_case(_repo(), case_id="CASE-MULTI-1", invalid_modules=["Product", "Eligibility"])

    first = client.post(
        "/api/v2/cases/CASE-MULTI-1/specialist-reviews",
        json={"review_type": "product_specialist", "decision": "cleared", "summary": "San pham OK.", "findings": A_FINDING},
        headers=PRODUCT,
    )
    assert first.status_code == 201, first.text
    assert first.json()["case_status_changed"] is False
    assert first.json()["still_waiting_for"] == ["legal_specialist"]
    case_after_first = _repo().get_case("CASE-MULTI-1")
    assert case_after_first.state.status == CaseStatus.PENDING_REVIEW

    second = client.post(
        "/api/v2/cases/CASE-MULTI-1/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "Phap ly OK.", "findings": A_FINDING},
        headers=LEGAL,
    )
    assert second.status_code == 201, second.text
    assert second.json()["case_status_changed"] is True
    assert second.json()["case_status"] == "pending_approval"
    case_after_second = _repo().get_case("CASE-MULTI-1")
    assert case_after_second.state.status == CaseStatus.PENDING_APPROVAL


# ---------------------------------------------------------------------------
# expected_case_version: optional optimistic concurrency
# ---------------------------------------------------------------------------

def test_expected_case_version_matching_succeeds(client):
    _seed_pending_review_case(_repo(), case_id="CASE-VER-1", invalid_modules=["Eligibility"])
    stored = _repo().get_case("CASE-VER-1")
    resp = client.post(
        "/api/v2/cases/CASE-VER-1/specialist-reviews",
        json={
            "review_type": "legal_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING,
            "expected_case_version": stored.version,
        },
        headers=LEGAL,
    )
    assert resp.status_code == 201, resp.text


def test_expected_case_version_mismatch_returns_409(client):
    _seed_pending_review_case(_repo(), case_id="CASE-VER-2", invalid_modules=["Eligibility"])
    stored = _repo().get_case("CASE-VER-2")
    resp = client.post(
        "/api/v2/cases/CASE-VER-2/specialist-reviews",
        json={
            "review_type": "legal_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING,
            "expected_case_version": stored.version + 1,
        },
        headers=LEGAL,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "CASE_VERSION_CONFLICT"
    case = _repo().get_case("CASE-VER-2")
    assert case.state.status == CaseStatus.PENDING_REVIEW  # untouched


# ---------------------------------------------------------------------------
# Return path to RM + human-resolution-path existence + notification idempotency
# ---------------------------------------------------------------------------

def test_specialist_review_returns_case_to_rm_work_queue(client):
    _seed_pending_review_case(_repo(), case_id="CASE-NOTIFY-1", invalid_modules=["Eligibility"])
    resp = client.post(
        "/api/v2/cases/CASE-NOTIFY-1/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING},
        headers=LEGAL,
    )
    assert resp.status_code == 201

    queue = client.get("/api/v2/me/work-queue", headers=RM)
    assert queue.status_code == 200
    matches = [item for item in queue.json() if item["work_item_id"].startswith("REVIEW-NOTIFY-CASE-NOTIFY-1-")]
    assert len(matches) == 1


def test_repeated_notification_for_same_outcome_does_not_duplicate_work_item(client):
    """Two DIFFERENT specialists finishing a multi-domain block within the
    same case_version must produce exactly one 'case returned to RM'
    notification, not one per clearer -- _notification_item_id is
    deterministic on (case_id, case_version, event_type, target, role_set),
    so create_work_item's INSERT OR REPLACE collapses to a single row."""
    _seed_pending_review_case(_repo(), case_id="CASE-NOTIFY-2", invalid_modules=["Product", "Eligibility"])
    client.post(
        "/api/v2/cases/CASE-NOTIFY-2/specialist-reviews",
        json={"review_type": "product_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING},
        headers=PRODUCT,
    )
    resp = client.post(
        "/api/v2/cases/CASE-NOTIFY-2/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING},
        headers=LEGAL,
    )
    assert resp.status_code == 201
    assert resp.json()["case_status_changed"] is True

    queue = client.get("/api/v2/me/work-queue", headers=RM)
    matches = [item for item in queue.json() if item["work_item_id"].startswith("REVIEW-NOTIFY-CASE-NOTIFY-2-")]
    assert len(matches) == 1


def test_high_risk_case_has_a_human_resolution_path(client):
    """The report's own gap #2: a PENDING_REVIEW case must always name at
    least one real, IAM-verifiable role that can act on it."""
    _seed_pending_review_case(_repo(), case_id="CASE-RESOLVE-1", invalid_modules=["Eligibility"])
    ctx = client.get("/api/v2/cases/CASE-RESOLVE-1/review-context", headers=LEGAL)
    assert ctx.status_code == 200
    required = ctx.json()["required_reviewer_roles"]
    assert required == ["legal_specialist"]
    resp = client.post(
        "/api/v2/cases/CASE-RESOLVE-1/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING},
        headers=LEGAL,
    )
    assert resp.status_code == 201
    assert resp.json()["case_status_changed"] is True


def test_get_specialist_reviews_history(client):
    _seed_pending_review_case(_repo(), case_id="CASE-HIST-1", invalid_modules=["Eligibility"])
    client.post(
        "/api/v2/cases/CASE-HIST-1/specialist-reviews",
        json={"review_type": "legal_specialist", "decision": "cleared", "summary": "OK.", "findings": A_FINDING},
        headers=LEGAL,
    )
    history = client.get("/api/v2/cases/CASE-HIST-1/specialist-reviews", headers=RM)
    assert history.status_code == 200
    records = history.json()
    assert len(records) == 1
    assert records[0]["review_type"] == "legal_specialist"
    assert records[0]["decision"] == "cleared"


# ---------------------------------------------------------------------------
# Operational Readiness: deterministic module remains RM-owned
# ---------------------------------------------------------------------------

def test_rm_can_set_operational_readiness(client):
    _seed_pending_review_case(_repo(), case_id="CASE-READY-1", invalid_modules=["Eligibility"])
    resp = client.put(
        "/api/v2/cases/CASE-READY-1/operational-readiness",
        json={
            "items": [
                {"code": "PAYLOAD_VALIDATED", "status": "completed"},
                {"code": "CUSTOMER_CONTACT_CONFIRMED", "status": "completed"},
            ],
            "summary": "San sang thuc thi.",
        },
        headers=RM,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "ready"
    assert body["updated_by"] == "RM-999"


def test_operational_readiness_not_ready_when_any_item_incomplete(client):
    _seed_pending_review_case(_repo(), case_id="CASE-READY-2", invalid_modules=["Eligibility"])
    resp = client.put(
        "/api/v2/cases/CASE-READY-2/operational-readiness",
        json={
            "items": [
                {"code": "PAYLOAD_VALIDATED", "status": "completed"},
                {"code": "CUSTOMER_CONTACT_CONFIRMED", "status": "blocked", "note": "Chua lien lac duoc."},
            ],
            "summary": "Con thieu xac nhan dau moi.",
        },
        headers=RM,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "not_ready"

    queue = client.get("/api/v2/me/work-queue", headers=RM)
    matches = [item for item in queue.json() if item["work_item_id"].startswith("REVIEW-NOTIFY-CASE-READY-2-")]
    assert len(matches) == 1


def test_operational_readiness_does_not_touch_case_status(client):
    state = _seed_pending_review_case(_repo(), case_id="CASE-READY-3", invalid_modules=["Eligibility"])
    client.put(
        "/api/v2/cases/CASE-READY-3/operational-readiness",
        json={"items": [{"code": "PAYLOAD_VALIDATED", "status": "completed"}], "summary": "OK."},
        headers=RM,
    )
    case = _repo().get_case("CASE-READY-3")
    assert case.state.status == CaseStatus.PENDING_REVIEW  # never touched by readiness tracker


def test_credit_specialist_cannot_set_operational_readiness(client):
    _seed_pending_review_case(_repo(), case_id="CASE-READY-4", invalid_modules=["Eligibility"])
    resp = client.put(
        "/api/v2/cases/CASE-READY-4/operational-readiness",
        json={"items": [{"code": "PAYLOAD_VALIDATED", "status": "completed"}], "summary": "OK."},
        headers=CREDIT,
    )
    assert resp.status_code == 403


def test_rm_can_read_operational_readiness(client):
    _seed_pending_review_case(_repo(), case_id="CASE-READY-5", invalid_modules=["Eligibility"])
    client.put(
        "/api/v2/cases/CASE-READY-5/operational-readiness",
        json={"items": [{"code": "PAYLOAD_VALIDATED", "status": "completed"}], "summary": "OK."},
        headers=RM,
    )
    resp = client.get("/api/v2/cases/CASE-READY-5/operational-readiness", headers=RM)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_operational_readiness_missing_returns_null(client):
    _seed_pending_review_case(_repo(), case_id="CASE-READY-6", invalid_modules=["Eligibility"])
    resp = client.get("/api/v2/cases/CASE-READY-6/operational-readiness", headers=RM)
    assert resp.status_code == 200
    assert resp.json() is None
