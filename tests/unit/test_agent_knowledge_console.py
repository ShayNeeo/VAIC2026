"""HTTP-driven tests for the Agent Knowledge Console (app/api/v2/employee_router.py
knowledge_router): lets a department Specialist feed/update/retire the
knowledge their own domain's Agent (Product/Credit/Insurance) retrieves,
and see a metadata summary of what that Agent has been doing on cases in
their scope. Same isolation pattern as test_v2_specialist_review.py --
real HTTP calls via fastapi.testclient.TestClient against the real app,
per this project's "no bia" discipline.

DB/index isolation: isolated employee_db (V2_DB_PATH), isolated
VECTOR_DB_DIR so knowledge writes never touch the real shared
data/vector_db/*.sqlite3 files, and KNOWLEDGE_EMBEDDING_PROVIDER forced to
"local" so no test makes a real network embedding call regardless of what
.env sets (see app/knowledge/legal_service.py's __init__ comment for why
that matters in this repo).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

import app.config as app_config
import app.storage.employee_db as employee_db
from app.config import settings
from app.main import app
from app.schemas.v2.examples import FULL_CONTEXT_SNAPSHOT, MINIMAL_SHARED_CASE_STATE
from app.schemas.v2.shared_case_state import Evidence, SharedCaseState
from app.storage.repository import V2Repository


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    db_path = tmp_path / "agent_knowledge_test.sqlite3"
    monkeypatch.setattr(app_config.settings, "V2_DB_PATH", str(db_path))
    monkeypatch.setattr(app_config.settings, "VECTOR_DB_DIR", str(tmp_path / "vector_db"))
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_PROVIDER", "local")
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
INSURANCE = auth_headers("demo-spec-insurance-001")
MANAGER = auth_headers("demo-mgr-hn-01")


def _repo() -> V2Repository:
    return V2Repository(settings.V2_DB_PATH)


def _create_body(**overrides: Any) -> Dict[str, Any]:
    body = {
        "product_id": "SYNTH-PROD-WORKING-CAPITAL",
        "section_path": "dieu-kien-von-luu-dong",
        "text": "Von luu dong duoc cap toi da 70% gia tri hop dong dau vao co xac nhan.",
        "effective_from": "2026-01-01",
    }
    body.update(overrides)
    return body


def _seed_case_with_product_result(*, case_id: str, customer_id: str = "COMP-ABC") -> SharedCaseState:
    payload = deepcopy(MINIMAL_SHARED_CASE_STATE)
    payload["context"] = deepcopy(FULL_CONTEXT_SNAPSHOT)
    payload["context"]["customer"]["customer_id"] = customer_id
    payload["case_id"] = case_id
    payload["trace_id"] = f"TRACE-{case_id}"
    payload["status"] = "pending_review"
    state = SharedCaseState.model_validate(payload)
    state.product_result = {
        "recommendations": [{"product_id": "SYNTH-PROD-WORKING-CAPITAL", "match_score": 0.9, "evidences": []}],
    }
    state.evidences = [
        Evidence(
            claim_id=f"EV-{case_id}-1", module="Product", claim="claim", source_document_id="DOC-1",
            source_version="1", location="section-1", quote="quote text", is_valid=True,
        )
    ]
    state.ai_decision_log = [
        {"component": "ProductExpertAgent", "event": "products_retrieved_and_ranked", "output_summary": {}},
    ]
    _repo().save_case(state, expected_version=0)
    return state


# ---------------------------------------------------------------------------
# Role gating: a specialist only ever controls their OWN domain's Agent
# ---------------------------------------------------------------------------

def test_rm_has_no_agent_domain_to_manage(client):
    resp = client.get("/api/v2/me/agent-knowledge", headers=RM)
    assert resp.status_code == 403

    resp = client.post("/api/v2/me/agent-knowledge", json=_create_body(), headers=RM)
    assert resp.status_code == 403


def test_manager_has_no_agent_domain_to_manage(client):
    resp = client.get("/api/v2/me/agent-knowledge", headers=MANAGER)
    assert resp.status_code == 403


def test_unauthenticated_request_is_rejected(client):
    resp = client.get("/api/v2/me/agent-knowledge")
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Create / list -- feeding new knowledge to a domain's Agent
# ---------------------------------------------------------------------------

def test_product_specialist_can_feed_knowledge_to_product_agent(client):
    resp = client.post("/api/v2/me/agent-knowledge", json=_create_body(), headers=PRODUCT)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["domain"] == "product"
    assert body["contributed_by"] == "SPEC-PROD-001"
    assert body["is_superseded"] is False
    assert body["is_quarantined"] is False

    listed = client.get("/api/v2/me/agent-knowledge", headers=PRODUCT).json()
    assert any(item["chunk_id"] == body["chunk_id"] for item in listed)


def test_legal_specialist_cannot_feed_product_domain_knowledge(client):
    """There is no request field that lets a Legal Specialist target the
    Product Agent -- domain is derived purely from identity.roles, never
    from the request body -- so this just confirms a Legal Specialist's
    submission always lands in the legal domain, not product's."""
    resp = client.post("/api/v2/me/agent-knowledge", json=_create_body(), headers=LEGAL)
    assert resp.status_code == 201, resp.text
    assert resp.json()["domain"] == "legal"

    product_listed = client.get("/api/v2/me/agent-knowledge", headers=PRODUCT).json()
    assert not any(item["contributed_by"] == "SPEC-LEGAL-001" for item in product_listed)


def test_credit_specialist_can_feed_credit_policy_knowledge(client):
    resp = client.post(
        "/api/v2/me/agent-knowledge",
        json=_create_body(
            product_id="PROD-WORKING-CAPITAL", section_path="phan-tich-kha-nang-tra-no",
            text="Can doi chieu dong tien tra no, nghia vu no hien huu va kich ban bien dong.",
        ),
        headers=CREDIT,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["domain"] == "credit"
    assert resp.json()["chunk_type"] == "credit_policy_article"


def test_insurance_specialist_can_feed_insurance_policy_knowledge(client):
    resp = client.post(
        "/api/v2/me/agent-knowledge",
        json=_create_body(
            product_id="PROD-INSURANCE-GENERAL", section_path="bao-hiem-tai-san-dam-bao",
            text="Tai san dam bao phai co bao hiem con hieu luc va SHB la ben thu huong.",
        ),
        headers=INSURANCE,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["domain"] == "insurance"
    assert resp.json()["chunk_type"] == "insurance_policy_article"


def test_create_rejects_short_text(client):
    resp = client.post("/api/v2/me/agent-knowledge", json=_create_body(text="ab"), headers=PRODUCT)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Update -- versioned supersede, and quarantine (retire without replacing)
# ---------------------------------------------------------------------------

def test_updating_text_supersedes_old_version_and_keeps_it_visible(client):
    created = client.post("/api/v2/me/agent-knowledge", json=_create_body(), headers=PRODUCT).json()
    chunk_id = created["chunk_id"]

    resp = client.patch(
        f"/api/v2/me/agent-knowledge/{chunk_id}",
        json={"text": "Von luu dong duoc cap toi da 80% gia tri hop dong (cap nhat 2026)."},
        headers=PRODUCT,
    )
    assert resp.status_code == 200, resp.text
    updated = resp.json()
    assert updated["chunk_id"] != chunk_id
    assert updated["is_superseded"] is False
    assert "80%" in updated["text"]

    listed = {item["chunk_id"]: item for item in client.get("/api/v2/me/agent-knowledge", headers=PRODUCT).json()}
    assert listed[chunk_id]["is_superseded"] is True
    assert listed[updated["chunk_id"]]["is_superseded"] is False


def test_quarantine_retires_entry_without_deleting_it(client):
    created = client.post("/api/v2/me/agent-knowledge", json=_create_body(), headers=LEGAL).json()
    chunk_id = created["chunk_id"]

    resp = client.patch(f"/api/v2/me/agent-knowledge/{chunk_id}", json={"is_quarantined": True}, headers=LEGAL)
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_quarantined"] is True

    listed = {item["chunk_id"]: item for item in client.get("/api/v2/me/agent-knowledge", headers=LEGAL).json()}
    assert chunk_id in listed
    assert listed[chunk_id]["is_quarantined"] is True


def test_update_unknown_chunk_id_is_404(client):
    resp = client.patch("/api/v2/me/agent-knowledge/DOES-NOT-EXIST", json={"is_quarantined": True}, headers=PRODUCT)
    assert resp.status_code == 404


def test_other_domain_specialist_cannot_update_a_chunk_they_did_not_own(client):
    created = client.post("/api/v2/me/agent-knowledge", json=_create_body(), headers=PRODUCT).json()
    resp = client.patch(
        f"/api/v2/me/agent-knowledge/{created['chunk_id']}", json={"is_quarantined": True}, headers=LEGAL,
    )
    # Legal's index is a different SQLite file entirely -- the chunk_id
    # simply does not exist there.
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Activity -- "what is my Agent working on"
# ---------------------------------------------------------------------------

def test_activity_reports_knowledge_count_and_case_summary(client):
    client.post("/api/v2/me/agent-knowledge", json=_create_body(), headers=PRODUCT)
    _seed_case_with_product_result(case_id="CASE-ACT-1", customer_id="COMP-ABC")

    resp = client.get("/api/v2/me/agent-knowledge/activity", headers=PRODUCT)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["domain"] == "product"
    assert body["knowledge_entry_count"] >= 1
    assert body["active_knowledge_entry_count"] >= 1

    case_item = next(item for item in body["cases"] if item["case_id"] == "CASE-ACT-1")
    assert case_item["agent_has_run"] is True
    assert case_item["agent_summary"]["recommendation_count"] == 1
    assert case_item["evidence_count"] == 1
    assert case_item["last_ai_log_event"]["event"] == "products_retrieved_and_ranked"


def test_activity_is_scoped_to_specialists_customer_scope(client):
    _seed_case_with_product_result(case_id="CASE-ACT-OUT-OF-SCOPE", customer_id="COMP-NOT-ASSIGNED")

    resp = client.get("/api/v2/me/agent-knowledge/activity", headers=PRODUCT)
    assert resp.status_code == 200, resp.text
    case_ids = [item["case_id"] for item in resp.json()["cases"]]
    assert "CASE-ACT-OUT-OF-SCOPE" not in case_ids


def test_credit_activity_reads_credit_agent_result(client):
    payload = deepcopy(MINIMAL_SHARED_CASE_STATE)
    payload["context"] = deepcopy(FULL_CONTEXT_SNAPSHOT)
    payload["context"]["customer"]["customer_id"] = "COMP-ABC"
    payload["case_id"] = "CASE-ACT-CREDIT-1"
    payload["trace_id"] = "TRACE-CASE-ACT-CREDIT-1"
    payload["status"] = "pending_review"
    state = SharedCaseState.model_validate(payload)
    state.credit_result = {
        "status": "needs_information",
        "credit_product_ids": ["PROD-WORKING-CAPITAL"],
        "hard_blocks": [],
        "missing_information": ["financial_statements"],
        "analysis_confidence": {"input_completeness": 0.6},
    }
    state.ai_decision_log = [
        {"component": "CreditExpert", "event": "expert_finding_committed", "output_summary": {}}
    ]
    _repo().save_case(state, expected_version=0)

    resp = client.get("/api/v2/me/agent-knowledge/activity", headers=CREDIT)
    assert resp.status_code == 200, resp.text
    assert resp.json()["domain"] == "credit"
    case_item = next(item for item in resp.json()["cases"] if item["case_id"] == "CASE-ACT-CREDIT-1")
    assert case_item["evidence_count"] == 0
    assert case_item["agent_summary"]["status"] == "needs_information"
    assert case_item["agent_summary"]["missing_information_count"] == 1
    assert case_item["last_ai_log_event"]["component"] == "CreditExpert"


def test_insurance_activity_reads_insurance_agent_result(client):
    payload = deepcopy(MINIMAL_SHARED_CASE_STATE)
    payload["context"] = deepcopy(FULL_CONTEXT_SNAPSHOT)
    payload["context"]["customer"]["customer_id"] = "COMP-MP"
    payload["case_id"] = "CASE-ACT-INSURANCE-1"
    payload["trace_id"] = "TRACE-CASE-ACT-INSURANCE-1"
    payload["status"] = "pending_information"
    state = SharedCaseState.model_validate(payload)
    state.insurance_result = {
        "status": "needs_information",
        "insurance_product_ids": ["PROD-INSURANCE-GENERAL"],
        "coverage_checks": [{"requirement": "property_insurance", "status": "unknown"}],
        "hard_blocks": [],
        "missing_information": ["has_property_insurance"],
    }
    state.ai_decision_log = [
        {"component": "InsuranceExpert", "event": "expert_finding_committed", "output_summary": {}}
    ]
    _repo().save_case(state, expected_version=0)

    resp = client.get("/api/v2/me/agent-knowledge/activity", headers=INSURANCE)
    assert resp.status_code == 200, resp.text
    assert resp.json()["domain"] == "insurance"
    case_item = next(item for item in resp.json()["cases"] if item["case_id"] == "CASE-ACT-INSURANCE-1")
    assert case_item["agent_summary"]["coverage_check_count"] == 1
    assert case_item["agent_summary"]["missing_information_count"] == 1
    assert case_item["last_ai_log_event"]["component"] == "InsuranceExpert"
