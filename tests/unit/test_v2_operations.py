"""Draft, checklist and dedup acceptance tests."""

from __future__ import annotations

from app.operations.service import OperationsService


PRODUCT = {
    "recommendations": [
        {
            "product_id": "PROD-WORKING-CAPITAL",
            "prerequisites": ["financial_statements", "capital_use_plan"],
        }
    ]
}
ELIGIBILITY = {
    "overall_status": "pending_information",
    "products": [
        {
            "product_id": "PROD-WORKING-CAPITAL",
            "rules": [
                {"rule_id": "RULE-CREDIT-FS-001", "field": "documents", "expected": "financial_statements", "status": "pending_information"},
                {"rule_id": "RULE-CREDIT-UBO-001", "field": "ubo_status", "expected": ["verified"], "status": "pending_information"},
            ],
        }
    ],
}


def prepare(**kwargs):
    return OperationsService().prepare(
        organization="HN01", customer_id="COMP-ABC", case_id="CASE-1",
        customer_name="Công ty ABC", product_result=PRODUCT, eligibility_result=ELIGIBILITY,
        **kwargs,
    )


def test_checklist_merges_duplicate_document_and_keeps_both_sources():
    result = prepare()
    financial = next(item for item in result["required_document_checklist"] if item["document_type_id"] == "financial_statements")
    assert financial["reasons"] == ["eligibility_rule", "product_prerequisite"]
    assert financial["source_rule_ids"] == ["RULE-CREDIT-FS-001"]
    assert len([item for item in result["required_document_checklist"] if item["document_type_id"] == "financial_statements"]) == 1


def test_message_contains_missing_items_and_no_approval_claim():
    body = prepare()["customer_message_draft"]["body"]
    assert "Báo cáo tài chính" in body
    assert "UBO" in body
    assert "không phải cam kết phê duyệt" in body


def test_existing_active_task_is_reused_and_prepare_has_no_side_effect():
    first = prepare()
    task = first["task_drafts"][0]
    replay = prepare(existing_artifacts=[{"dedup_key": task["dedup_key"], "status": "in_progress"}])
    assert replay["task_drafts"][0]["action"] == "reuse"
    assert replay["external_side_effects"] == []


def test_resume_updates_artifact_version_instead_of_creating_second_draft():
    first = prepare()
    updated = prepare(previous_result=first)
    assert updated["artifact_version"] == 2
    assert updated["crm_case_draft"]["case_id"] == first["crm_case_draft"]["case_id"]
    assert updated["content_hash"] != first["content_hash"]


def test_verified_context_document_is_not_reported_missing():
    result = prepare(
        available_documents=[
            {"document_type": "financial_statements", "status": "verified", "document_id": "DOC-FS"}
        ]
    )
    financial = next(
        item for item in result["required_document_checklist"]
        if item["document_type_id"] == "financial_statements"
    )
    assert financial["current_status"] == "verified"
    assert "financial_statements" not in result["missing_information"]
