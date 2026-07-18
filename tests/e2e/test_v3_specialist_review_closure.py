import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v2.router import create_router
from app.api.v2.employee_router import case_action_router
from app.observability.runtime import JsonEventLogger
from app.storage.repository import V2Repository
from app.workflow.engine import V2WorkflowEngine
from app.eligibility.engine import EligibilityEngine
from app.data_v3.adapters.rules_adapter import V3RuleRegistry
from app.product.service import ProductService
from app.knowledge.legal_service import LegalKnowledgeService
from app.knowledge.index import LocalEmbedding

import app.config as app_config
import app.storage.employee_db as employee_db

ROOT = Path(__file__).resolve().parents[2]
V3_RULES_PATH = ROOT / "data" / "synthetic" / "v3" / "legal" / "eligibility_rules.json"
V3_BANKING_DOCS_PATH = ROOT / "data" / "synthetic" / "v3" / "legal" / "banking_policy_documents.json"

HEADERS_RM = {"X-Employee-ID": "RM-999", "X-Session-ID": "SESS-MP"}
HEADERS_LEGAL = {"X-Employee-ID": "SPEC-LEGAL-001", "X-Session-ID": "SESS-MP"}


class MockProductService(ProductService):
    def __init__(self, expected_bundle):
        self.expected_bundle = expected_bundle

    def recommend(self, query: str, **kwargs) -> dict:
        return {
            "query": query,
            "recommendations": [
                {
                    "product_id": pid,
                    "name": pid,
                    "match_score": 0.99,
                    "score_components": {"retrieval": 0.99},
                    "features": ["V3 features"],
                    "conditions": ["V3 conditions"],
                    "reason": "V3 E2E test mock"
                }
                for pid in self.expected_bundle
            ]
        }

    @property
    def knowledge(self):
        import types
        catalog_chunks = [
            types.SimpleNamespace(product_id=pid, active=True) for pid in self.expected_bundle
        ]
        return types.SimpleNamespace(
            index=types.SimpleNamespace(
                provider=types.SimpleNamespace(name="dummy_provider"),
                exact_lookup_by_chunk_id=lambda chunk_id: None,
                list_chunks=lambda: catalog_chunks,
            )
        )


def make_client(tmp_path: Path, expected_bundle: list) -> TestClient:
    app = FastAPI()
    registry = V3RuleRegistry(V3_RULES_PATH)
    eligibility_engine = EligibilityEngine(registry=registry)
    product_service = MockProductService(expected_bundle)

    # Build tmp legal knowledge index
    legal_index_path = tmp_path / "v3_legal.sqlite3"
    legal_service = LegalKnowledgeService(index_path=legal_index_path, provider=LocalEmbedding())
    legal_service.ingest_v3_banking_documents(V3_BANKING_DOCS_PATH)

    workflow_engine = V2WorkflowEngine(
        eligibility=eligibility_engine,
        product=product_service,
        legal_knowledge=legal_service,
    )

    app.include_router(
        create_router(
            repository=V2Repository(tmp_path / "state.sqlite3"),
            event_logger=JsonEventLogger(tmp_path / "events.jsonl"),
            engine=workflow_engine,
        )
    )
    # Include case action router for specialist reviews endpoint
    app.include_router(case_action_router, prefix="/api/v2")
    return TestClient(app)


def test_v3_specialist_review_closure_reaches_approval(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "state.sqlite3"
    monkeypatch.setattr(app_config.settings, "V2_DB_PATH", str(db_path))
    employee_db.init_employee_db()

    # Bypass clarification
    from app.intent.slot_resolver import SlotResolver
    orig_resolve = SlotResolver.resolve
    from app.schemas.v2.intent_result import RecommendedAction
    def mock_resolve(self, result, context, *, stage=None):
        res = orig_resolve(self, result, context, stage=stage)
        res.recommended_action = RecommendedAction.CONTINUE_WORKFLOW
        res.missing_information = []
        return res
    monkeypatch.setattr(SlotResolver, "resolve", mock_resolve)

    expected_bundle = ["SYNTH-PROD-WORKING-CAPITAL"]
    http = make_client(tmp_path, expected_bundle)

    # 1. Create Case
    response = http.post(
        "/api/v2/sales-cases",
        headers={**HEADERS_RM, "Idempotency-Key": "create-v3-closure"},
        json={
            "company_name": "Công ty Cổ phần Đóng gói MP",
            "tax_code": "0109988665",
            "industry": "packaging",
            "need_text": "Cần cấp hạn mức vốn lưu động vay mua nguyên vật liệu.",
            "rm_note": "Synthetic V3 Case Closure",
            "priority": "normal",
            "current_products": [],
        },
    )
    assert response.status_code == 201, response.text
    case_id = response.json()["case_id"]

    # 2. Upload Business Registration, Financial Statement and UBO declaration
    # This fulfills all missing document rules, so only bad_debt rules can fail/need review.
    files = [
        ("files", ("business_registration.txt", "Hồ sơ đăng ký doanh nghiệp hợp lệ. Hồ sơ doanh nghiệp phải có đăng ký kinh doanh hợp lệ.".encode("utf-8"), "text/plain")),
        ("files", ("financial_statement.txt", "BCTC kiểm toán năm 2025. Hồ sơ tín dụng phải có báo cáo tài chính năm gần nhất.".encode("utf-8"), "text/plain")),
        ("files", ("ubo_declaration.txt", "Tuyên bố chủ sở hữu hưởng lợi. hồ sơ cấp tín dụng phải có thông tin chủ sở hữu hưởng lợi đã xác minh.".encode("utf-8"), "text/plain")),
    ]
    upload_resp = http.post(f"/api/v2/sales-cases/{case_id}/documents", headers=HEADERS_RM, files=files)
    assert upload_resp.status_code == 200, upload_resp.text

    from tests.test_sales_cases_e2e import process_and_resolve
    # 3. Process documents and resolve conflicts
    profile = process_and_resolve(http, case_id)

    # Override context with:
    # - employees_count = 50 (passes WC rules)
    # - operating_years = 5 (passes WC years rule)
    # - ubo_status = complete (passes WC UBO rule)
    # - has_bad_debt_12m = True (violates WC BADDEBT rule -> failed status -> PENDING_REVIEW because reviewable)
    patch_resp = http.patch(f"/api/v2/sales-cases/{case_id}/extracted-profile", headers=HEADERS_RM, json={
        "expected_version": profile["version"],
        "changes": [
            {"field_name": "business_profile.employees_count", "value": 50, "reason": "v3 test"},
            {"field_name": "business_profile.operating_years", "value": 5, "reason": "v3 test"},
            {"field_name": "legal_profile.ubo_status", "value": "complete", "reason": "v3 test"},
            {"field_name": "financing_profile.has_bad_debt_12m", "value": True, "reason": "v3 test override"},
        ]
    })
    assert patch_resp.status_code == 200, patch_resp.text
    new_version = patch_resp.json()["version"]

    # 4. Confirm profile
    confirm_resp = http.post(f"/api/v2/sales-cases/{case_id}/confirm-profile", headers=HEADERS_RM, json={"expected_version": new_version, "attestation": True})
    assert confirm_resp.status_code == 200, confirm_resp.text
    confirmed_version = confirm_resp.json()["version"]

    # 5. Run analysis -> expect PENDING_REVIEW
    analysis_resp = http.post(f"/api/v2/sales-cases/{case_id}/run-analysis", headers=HEADERS_RM, json={"expected_version": confirmed_version})
    assert analysis_resp.status_code == 200, analysis_resp.text
    analysis = analysis_resp.json()
    assert analysis["case"]["status"] == "pending_review"
    case_version = analysis["state_version"]

    # Verify risk gate result permits human override
    rg_result = analysis["case"]["risk_gate_result"]
    assert rg_result["outcome"] == "need_review"
    assert rg_result["human_review_allowed"] is True
    assert "legal_specialist" in rg_result["required_reviewer_roles"]
    assert "SYNTH-RULE-WC-BADDEBT-001" in rg_result["triggered_rules"]

    # 6. Specialist clears the case
    review_resp = http.post(
        f"/api/v2/cases/{case_id}/specialist-reviews",
        headers={**HEADERS_LEGAL, "X-Session-ID": "SESS-MP"},
        json={
            "review_type": "legal_specialist",
            "decision": "cleared",
            "summary": "Bad debt is historical and has been fully restructured. Business is eligible.",
            "findings": [{"code": "BADDEBT_RESTRUCTURED", "severity": "medium", "message": "Nợ xấu đã tất toán và tái cơ cấu."}],
            "expected_case_version": case_version,
        }
    )
    assert review_resp.status_code == 201, review_resp.text
    review_result = review_resp.json()
    assert review_result["case_status_changed"] is True
    assert review_result["case_status"] == "pending_approval"
