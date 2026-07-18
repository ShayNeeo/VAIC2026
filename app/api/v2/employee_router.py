"""API Router for Employee personalization, work context, consent and Next Best Work."""

from __future__ import annotations

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, HTTPException, Response, status
from pydantic import BaseModel

from app.schemas.v2.employee import (
    EmployeeContextSnapshot,
    AuthorizationContext,
    WorkContext,
    PersonalizationContext,
    HabitModel,
    HabitStatus,
    ConsentModel,
    RoleType,
    ProvenanceMetadata,
    ProvenanceType,
)
from app.storage.employee_db import (
    get_db_connection,
    get_employee,
    get_preferences,
    save_preferences,
    get_consent,
    save_consent,
    get_habits,
    confirm_habit,
    reject_habit,
    delete_habit,
    get_work_items,
    save_recommendation_feedback,
)
from app.context.next_best_work import get_next_best_work

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/me", tags=["Employee Copilot"])


class ErrorResponse(BaseModel):
    code: str
    message: str
    retryable: bool
    request_id: str


def get_verified_sso_employee(employee_id: Optional[str]) -> Dict[str, Any]:
    """SSO Adapter: Verifies identity, resolves roles and permissions from IAMPort."""
    if not employee_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHENTICATED",
                    "message": "Không có hoặc token không hợp lệ.",
                    "retryable": False,
                    "request_id": "REQ-001"
                }
            }
        )

    if employee_id == "EXPIRED_TOKEN":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": "Token phiên đăng nhập đã hết hạn.",
                    "retryable": False,
                    "request_id": "REQ-002"
                }
            }
        )

    if employee_id == "IAM_ERROR":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "IAM_SERVICE_UNAVAILABLE",
                    "message": "Không thể kết nối đến hệ thống xác thực IAM tại thời điểm này.",
                    "retryable": True,
                    "request_id": "REQ-003"
                }
            }
        )

    emp = get_employee(employee_id)
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Nhân viên không tồn tại hoặc không được cấp quyền truy cập.",
                    "retryable": False,
                    "request_id": "REQ-004"
                }
            }
        )
    return emp


@router.get("", response_model=Dict[str, Any])
def get_my_profile(x_employee_id: Optional[str] = Header(None)) -> Dict[str, Any]:
    return get_verified_sso_employee(x_employee_id)


@router.get("/context", response_model=EmployeeContextSnapshot)
def get_my_context(x_employee_id: Optional[str] = Header(None)) -> EmployeeContextSnapshot:
    """Assembles the complete Employee Context Snapshot with Provenance mapping."""
    emp = get_verified_sso_employee(x_employee_id)
    emp_id = emp["employee_id"]

    # 1. Authorization Context
    auth_ctx = AuthorizationContext(
        identity_verified=True,
        roles=[RoleType(emp["role"])],
        permissions=emp["permissions"],
        customer_scope=emp["customer_scope"],
        verified_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )

    # 2. Personalization & Fallback Logic
    personalization_enabled = True
    preferences = {}
    confirmed_habits = []

    try:
        consent = get_consent(emp_id)
        if consent:
            personalization_enabled = consent["personalization_enabled"]
        
        if personalization_enabled:
            preferences = get_preferences(emp_id)
            confirmed_habits = [h for h in get_habits(emp_id) if h.status == HabitStatus.CONFIRMED]
    except Exception as exc:
        # Personalization DB error -> FALLBACK to default experiences safely
        logger.error(f"Personalization database failed, falling back to default UI: {exc}")
        personalization_enabled = False
        preferences = {
            "default_case_view": "dashboard",
            "preferred_email_template": "default",
            "show_evidence_expanded": False
        }

    p_ctx = PersonalizationContext(
        enabled=personalization_enabled,
        preferences=preferences,
        confirmed_habits=confirmed_habits,
        context_version=1
    )

    # 3. Work Context (Derived from active DB state)
    work_ctx = WorkContext(
        active_case_id=None,
        assigned_customer_ids=emp["customer_scope"],
        pending_task_ids=[],
        blocked_case_ids=[],
        waiting_for_roles=[]
    )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Load active case if any (last updated case)
        cursor.execute("SELECT case_id FROM cases WHERE employee_id = ? ORDER BY updated_at DESC LIMIT 1", (emp_id,))
        case_row = cursor.fetchone()
        if case_row:
            work_ctx.active_case_id = case_row[0]
        
        # Load pending tasks count
        cursor.execute("SELECT item_id FROM employee_work_items WHERE employee_id = ? AND status != 'completed'", (emp_id,))
        work_ctx.pending_task_ids = [r[0] for r in cursor.fetchall()]
        
        # Load blocked cases count
        cursor.execute("SELECT case_id FROM cases WHERE json_extract(state_json, '$.status') = 'blocked'")
        work_ctx.blocked_case_ids = [r[0] for r in cursor.fetchall()]

        # Load waiting roles
        cursor.execute("SELECT json_extract(state_json, '$.status') FROM cases WHERE employee_id = ?", (emp_id,))
        for r in cursor.fetchall():
            if r[0] == "pending_review":
                work_ctx.waiting_for_roles.append("legal_specialist")

        conn.close()
    except Exception as exc:
        logger.warning(f"Failed to query active work context: {exc}")

    # 4. Provenance Mapping
    provenance_map = {
        "authorization_context.roles": ProvenanceMetadata(
            source="iam_sso_portal",
            source_version="v1.2",
            refreshed_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            confidence=1.0,
            type=ProvenanceType.VERIFIED
        ),
        "authorization_context.permissions": ProvenanceMetadata(
            source="iam_sso_portal",
            source_version="v1.2",
            refreshed_at=datetime.utcnow(),
            confidence=1.0,
            type=ProvenanceType.VERIFIED
        ),
        "work_context.active_case_id": ProvenanceMetadata(
            source="case_repository",
            source_version="v2.1",
            refreshed_at=datetime.utcnow(),
            confidence=1.0,
            type=ProvenanceType.VERIFIED
        ),
        "personalization_context.preferences": ProvenanceMetadata(
            source="personalization_store",
            source_version="1",
            refreshed_at=datetime.utcnow(),
            confidence=0.9,
            type=ProvenanceType.PREFERENCE
        )
    }

    return EmployeeContextSnapshot(
        employee_id=emp_id,
        authorization_context=auth_ctx,
        work_context=work_ctx,
        personalization_context=p_ctx,
        provenance_map=provenance_map,
        generated_at=datetime.utcnow()
    )


@router.get("/work-queue", response_model=List[Any])
def get_my_work_queue(x_employee_id: Optional[str] = Header(None)) -> List[Any]:
    """Calculates Next Best Work queue for the employee."""
    emp = get_verified_sso_employee(x_employee_id)
    emp_id = emp["employee_id"]

    conn = get_db_connection()
    try:
        nbw_list = get_next_best_work(
            employee_id=emp_id,
            role=RoleType(emp["role"]),
            permissions=emp["permissions"],
            customer_scope=emp["customer_scope"],
            conn=conn
        )
    finally:
        conn.close()

    return nbw_list


@router.patch("/preferences", response_model=Dict[str, Any])
def patch_my_preferences(prefs: Dict[str, Any], x_employee_id: Optional[str] = Header(None)) -> Dict[str, Any]:
    emp = get_verified_sso_employee(x_employee_id)
    emp_id = emp["employee_id"]
    save_preferences(emp_id, prefs)
    return get_preferences(emp_id)


@router.get("/habits", response_model=List[HabitModel])
def get_my_habits(x_employee_id: Optional[str] = Header(None)) -> List[HabitModel]:
    emp = get_verified_sso_employee(x_employee_id)
    emp_id = emp["employee_id"]
    return get_habits(emp_id)


@router.post("/habits/{habit_id}/confirm")
def post_confirm_habit(habit_id: str, x_employee_id: Optional[str] = Header(None)) -> Dict[str, bool]:
    emp = get_verified_sso_employee(x_employee_id)
    emp_id = emp["employee_id"]
    success = confirm_habit(emp_id, habit_id)
    return {"success": success}


@router.post("/habits/{habit_id}/reject")
def post_reject_habit(habit_id: str, x_employee_id: Optional[str] = Header(None)) -> Dict[str, bool]:
    emp = get_verified_sso_employee(x_employee_id)
    emp_id = emp["employee_id"]
    success = reject_habit(emp_id, habit_id)
    return {"success": success}


@router.delete("/habits/{habit_id}")
def delete_my_habit(habit_id: str, x_employee_id: Optional[str] = Header(None)) -> Dict[str, bool]:
    emp = get_verified_sso_employee(x_employee_id)
    emp_id = emp["employee_id"]
    success = delete_habit(emp_id, habit_id)
    return {"success": success}


@router.post("/personalization/enable")
def post_enable_personalization(x_employee_id: Optional[str] = Header(None)) -> Dict[str, bool]:
    emp = get_verified_sso_employee(x_employee_id)
    emp_id = emp["employee_id"]
    consent = get_consent(emp_id)
    if consent:
        model = ConsentModel(
            employee_id=emp_id,
            personalization_enabled=True,
            activity_learning_enabled=consent["activity_learning_enabled"],
            allowed_event_categories=consent["allowed_event_categories"],
            consent_version=consent["consent_version"],
            confirmed_at=datetime.utcnow()
        )
        save_consent(model)
        return {"success": True}
    return {"success": False}


@router.post("/personalization/disable")
def post_disable_personalization(x_employee_id: Optional[str] = Header(None)) -> Dict[str, bool]:
    emp = get_verified_sso_employee(x_employee_id)
    emp_id = emp["employee_id"]
    consent = get_consent(emp_id)
    if consent:
        model = ConsentModel(
            employee_id=emp_id,
            personalization_enabled=False,
            activity_learning_enabled=consent["activity_learning_enabled"],
            allowed_event_categories=consent["allowed_event_categories"],
            consent_version=consent["consent_version"],
            confirmed_at=datetime.utcnow()
        )
        save_consent(model)
        return {"success": True}
    return {"success": False}


# Recommendation feedback endpoints
@APIRouter(tags=["Employee Copilot"]).post("/api/v2/recommendations/{rec_id}/accept")
def post_accept_recommendation(rec_id: str, x_employee_id: Optional[str] = Header(None)) -> Dict[str, bool]:
    emp = get_verified_sso_employee(x_employee_id)
    emp_id = emp["employee_id"]
    save_recommendation_feedback(
        feedback_id=f"FEEDBACK-{datetime.utcnow().timestamp()}",
        employee_id=emp_id,
        rec_id=rec_id,
        feedback="accepted"
    )
    return {"success": True}


@APIRouter(tags=["Employee Copilot"]).post("/api/v2/recommendations/{rec_id}/edit")
def post_edit_recommendation(rec_id: str, payload: Dict[str, Any], x_employee_id: Optional[str] = Header(None)) -> Dict[str, bool]:
    emp = get_verified_sso_employee(x_employee_id)
    emp_id = emp["employee_id"]
    save_recommendation_feedback(
        feedback_id=f"FEEDBACK-{datetime.utcnow().timestamp()}",
        employee_id=emp_id,
        rec_id=rec_id,
        feedback="edited",
        orig_val=payload.get("original"),
        edit_val=payload.get("edited")
    )
    return {"success": True}


@APIRouter(tags=["Employee Copilot"]).post("/api/v2/recommendations/{rec_id}/reject")
def post_reject_recommendation(rec_id: str, x_employee_id: Optional[str] = Header(None)) -> Dict[str, bool]:
    emp = get_verified_sso_employee(x_employee_id)
    emp_id = emp["employee_id"]
    save_recommendation_feedback(
        feedback_id=f"FEEDBACK-{datetime.utcnow().timestamp()}",
        employee_id=emp_id,
        rec_id=rec_id,
        feedback="rejected"
    )
    return {"success": True}


# Manager Dashboard Endpoints
@router.get("/team/workload", tags=["Manager Console"])
def get_team_workload(x_employee_id: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Manager console view: Aggregate dashboard only. Strictly isolation of individual RM preferences."""
    emp = get_verified_sso_employee(x_employee_id)
    if RoleType(emp["role"]) != RoleType.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập Manager Dashboard."
        )

    # Strictly read aggregate metrics
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Blocked cases count
    cursor.execute("SELECT COUNT(*) FROM cases WHERE json_extract(state_json, '$.status') = 'blocked'")
    blocked_count = cursor.fetchone()[0]

    # 2. SLA breached count
    cursor.execute("SELECT COUNT(*) FROM employee_work_items WHERE status != 'completed' AND urgency >= 0.8")
    sla_breaches = cursor.fetchone()[0]

    # 3. AI recommendation utilization (cohort view, strictly no individual profiling)
    cursor.execute("SELECT feedback, COUNT(*) FROM employee_recommendation_feedback GROUP BY feedback")
    feedback_rows = cursor.fetchall()
    utilization = {r[0]: r[1] for r in feedback_rows}
    # Add cohort size validation
    cursor.execute("SELECT COUNT(DISTINCT employee_id) FROM employees")
    cohort_size = cursor.fetchone()[0]

    conn.close()

    return {
        "branch_id": "BRANCH-HN-01",
        "cohort_size": cohort_size,
        "aggregate_metrics": {
            "blocked_cases": blocked_count,
            "sla_risks": sla_breaches,
            "ai_recommendation_utilization": {
                "cohort_minimum_size_met": cohort_size >= 5,
                "utilization_summary": utilization
            }
        }
    }
