"""Canonical example payloads for the V2 contracts.

These are the single source used by contract tests (JSON Schema + Pydantic),
and are meant to be reused as-is for `/api/v2` OpenAPI response examples once
V2-013 exists (plan_v2/14_BUILD_ORDER.md). Reusing the same dict in all three
places is what makes "JSON/Pydantic/API examples dong nhat" true by
construction instead of by manual bookkeeping.
"""

from __future__ import annotations

from typing import Any, Dict

MINIMAL_CONTEXT_SNAPSHOT: Dict[str, Any] = {
    "schema_version": "2.0.0",
    "employee": {
        "employee_id": "EMP-001",
        "role": "RM",
        "organization_unit": "Corporate Banking HN",
        "permissions": [],
        "access_scope": {},
    },
    "workspace": {
        "session_id": "SESS-001",
        "current_screen": "case_detail",
    },
    "customer": {
        "customer_id": None,
        "profile_version": None,
        "attributes": {},
        "source_observed_at": None,
        "stale": True,
    },
    "conversation": {
        "current_goal": None,
        "confirmed_facts": {},
        "rejected_assumptions": [],
        "open_questions": [],
    },
    "documents": [],
    "conflicts": [],
    "assembled_at": "2026-07-17T10:00:00Z",
}

FULL_CONTEXT_SNAPSHOT: Dict[str, Any] = {
    "schema_version": "2.0.0",
    "employee": {
        "employee_id": "EMP-001",
        "role": "RM",
        "organization_unit": "Corporate Banking HN",
        "permissions": ["case:read", "case:write", "approval:request"],
        "access_scope": {"branch": "HN01"},
        "preferences": {"locale": "vi-VN"},
    },
    "workspace": {
        "session_id": "SESS-001",
        "current_screen": "case_detail",
        "selected_customer_id": "COMP-ABC",
        "active_case_id": "CASE-001",
        "active_task_id": "T1",
        "selected_product_ids": ["PROD-PAYROLL"],
    },
    "customer": {
        "customer_id": "COMP-ABC",
        "profile_version": "v3",
        "attributes": {"employees_count": 500, "annual_revenue": 120000000000},
        "source_observed_at": "2026-07-17T09:00:00Z",
        "stale": False,
    },
    "conversation": {
        "current_goal": "Mo dich vu payroll va kiem tra thau chi",
        "confirmed_facts": {
            "customer_id": {
                "value": "COMP-ABC",
                "source_type": "workspace",
                "source_id": "selected_customer_id",
                "confidence": 1.0,
                "confirmed": True,
                "observed_at": "2026-07-17T10:00:00Z",
            }
        },
        "rejected_assumptions": ["khach hang khong phai la XYZ"],
        "open_questions": ["Bao cao tai chinh nam gan nhat co chua?"],
    },
    "documents": [
        {
            "document_id": "DOC-REG-001",
            "document_type": "business_registration",
            "version": "1",
            "status": "verified",
            "effective_at": "2020-05-12T00:00:00Z",
            "access_scope": {"branch": "HN01"},
        }
    ],
    "conflicts": [
        {
            "field": "annual_revenue",
            "candidate_values": [
                {
                    "value": 120000000000,
                    "source_type": "crm",
                    "source_id": "crm_profile",
                    "confidence": 0.9,
                    "confirmed": False,
                    "observed_at": "2026-07-17T08:00:00Z",
                },
                {
                    "value": 95000000000,
                    "source_type": "document",
                    "source_id": "DOC-FS-2025",
                    "confidence": 0.6,
                    "confirmed": False,
                    "observed_at": "2026-07-16T08:00:00Z",
                },
            ],
            "decision_impact": "high",
            "requires_confirmation": True,
        }
    ],
    "assembled_at": "2026-07-17T10:00:00Z",
}

MINIMAL_INTENT_RESULT: Dict[str, Any] = {
    "schema_version": "2.0.0",
    "primary_intent": "check_missing_information",
    "sub_intents": [],
    "user_goal": "Kiem tra con thieu gi",
    "entities": {},
    "resolved_slots": {},
    "missing_information": [],
    "ambiguities": [],
    "evidence_spans": [],
    "field_confidence": {},
    "overall_confidence": 0.5,
    "recommended_action": "continue_workflow",
}

FULL_INTENT_RESULT: Dict[str, Any] = {
    "schema_version": "2.0.0",
    "primary_intent": "open_payroll_service",
    "sub_intents": ["check_overdraft_eligibility"],
    "user_goal": "Mo dich vu payroll va xin thau chi von luu dong",
    "entities": {"product_hint": "payroll"},
    "resolved_slots": {
        "customer_id": {
            "value": "COMP-ABC",
            "source_type": "workspace",
            "source_id": "selected_customer_id",
            "confidence": 1.0,
            "confirmed": True,
            "observed_at": "2026-07-17T10:00:00Z",
        }
    },
    "constraints": ["employees_count >= 10"],
    "success_criteria": ["payroll case created", "overdraft eligibility checked"],
    "missing_information": ["ubo_information"],
    "ambiguities": [
        {
            "field": "product_scope",
            "hypotheses": ["payroll_only", "payroll_and_overdraft"],
            "decision_impact": "medium",
        }
    ],
    "evidence_spans": [
        {"field": "primary_intent", "text": "mo dich vu payroll", "message_id": "m1"}
    ],
    "field_confidence": {"primary_intent": 0.95, "sub_intents": 0.7},
    "overall_confidence": 0.86,
    "recommended_action": "continue_workflow",
}

MINIMAL_SHARED_CASE_STATE: Dict[str, Any] = {
    "schema_version": "2.0.0",
    "case_id": "CASE-001",
    "trace_id": "TRACE-001",
    "status": "new",
    "context": MINIMAL_CONTEXT_SNAPSHOT,
    "request": {
        "message_id": "MSG-001",
        "text": "Kiem tra con thieu gi",
        "received_at": "2026-07-17T10:00:00Z",
    },
    "intent_result": None,
    "workflow": {
        "workflow_version": "v1",
        "current_node": None,
        "tasks": [],
        "loop_count": 0,
    },
    "evidences": [],
    "approval": {"status": "not_required"},
    "audit_events": [],
    "created_at": "2026-07-17T10:00:00Z",
    "updated_at": "2026-07-17T10:00:00Z",
}

FULL_SHARED_CASE_STATE: Dict[str, Any] = {
    "schema_version": "2.0.0",
    "case_id": "CASE-001",
    "trace_id": "TRACE-001",
    "status": "pending_approval",
    "context": FULL_CONTEXT_SNAPSHOT,
    "request": {
        "message_id": "MSG-001",
        "text": "Mo dich vu payroll va xin thau chi von luu dong",
        "received_at": "2026-07-17T10:00:00Z",
    },
    "intent_result": FULL_INTENT_RESULT,
    "workflow": {
        "workflow_version": "v1",
        "current_node": "operations",
        "tasks": [
            {
                "task_id": "T1",
                "task_type": "product_matching",
                "owner": "Product",
                "status": "completed",
                "dependencies": [],
                "dedup_key": "CASE-001:product_matching",
                "input_hash": "sha256:abc123",
                "output_ref": "product_result",
            }
        ],
        "loop_count": 1,
        "resume_from_nodes": ["eligibility"],
    },
    "product_result": {"recommended_products": ["PROD-PAYROLL"]},
    "eligibility_result": {"eligibility_status": "pending_info"},
    "operations_result": {"missing_documents": ["ubo_information"]},
    "evidences": [
        {
            "claim_id": "EVID-001",
            "module": "Product",
            "claim": "Payroll ap dung cho doanh nghiep tu 10 nhan su",
            "source_document_id": "SHB_Product_Catalog_2026",
            "source_version": "2026.1",
            "location": "section-3.1",
            "quote": "Doanh nghiep co so luong nhan su toi thieu tu 10 nguoi tro len.",
            "is_valid": True,
            "validation_score": 1.0,
        }
    ],
    "approval": {
        "status": "pending",
        "approver_id": "EMP-001",
        "payload_hash": "sha256:def456",
        "expires_at": "2026-07-17T10:10:00Z",
    },
    "audit_events": [
        {"actor": "Planner", "action": "create_plan", "at": "2026-07-17T10:00:05Z"}
    ],
    "created_at": "2026-07-17T10:00:00Z",
    "updated_at": "2026-07-17T10:05:00Z",
}

VALID_ACTION_INPUT: Dict[str, Any] = {
    "payload": {"case_id": "CASE-001"},
    "approval_token": "signed-token-abc",
    "idempotency_key": "CASE-001:create_crm_case:1",
}

ACTION_INPUT_MISSING_APPROVAL: Dict[str, Any] = {
    "payload": {"case_id": "CASE-001"},
    "idempotency_key": "CASE-001:create_crm_case:1",
}
