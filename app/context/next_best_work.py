"""Next Best Work Engine. 

Performs 2-stage task prioritization:
1. Hard Eligibility Filters (filters out invalid/blocked tasks).
2. Priority Band Classification & Deterministic Score Ranking with Tie-Breaking.
"""

from __future__ import annotations

import sqlite3
import json
from typing import Any, Dict, List, Set
from app.reliability.capability_registry import has_capability
from app.schemas.v2.employee import NextBestWorkItem, RoleType


def get_task_status_in_db(cursor: sqlite3.Cursor, item_id: str) -> str:
    cursor.execute("SELECT status FROM employee_work_items WHERE item_id = ?", (item_id,))
    row = cursor.fetchone()
    return row[0] if row else "unknown"


def get_next_best_work(
    employee_id: str,
    role: RoleType,
    permissions: List[str],
    customer_scope: List[str],
    conn: sqlite3.Connection
) -> List[NextBestWorkItem]:
    """Calculate personalized, optimized work recommendations for an employee."""
    cursor = conn.cursor()

    # Load all work items
    cursor.execute("SELECT * FROM employee_work_items")
    rows = cursor.fetchall()

    eligible_items = []
    for r in rows:
        item_id = r["item_id"]
        item_employee_id = r["employee_id"]
        title = r["title"]
        status = r["status"]
        business_impact = r["business_impact"]
        urgency = r["urgency"]
        customer_commitment = r["customer_commitment"]
        risk_severity = r["risk_severity"]
        dependency_unblock = r["dependency_unblock"]
        ownership_match = r["ownership_match"]
        estimated_effort = r["estimated_effort"]
        created_at = r["created_at"]
        due_at = r["due_at"]
        dependency_ids = json_loads_safe(r["dependency_ids"])
        role_required = r["role_required"]
        customer_id = r["customer_id"]

        # === TẦNG 1: HARD ELIGIBILITY FILTERS ===

        # Rule 1: Item thuộc customer scope được giao
        if customer_id not in customer_scope:
            continue

        # Rule 2: Item chưa hoàn thành
        if status == "completed":
            continue

        # Rule 3: Quyền xử lý khớp (role nhân viên phải khớp chính xác với role_required của task)
        if role.value != role_required:
            continue

        # Rule 4: Item không bị dependency block (tất cả các dependency phải ở trạng thái completed)
        is_blocked = False
        for dep_id in dependency_ids:
            dep_status = get_task_status_in_db(cursor, dep_id)
            if dep_status != "completed":
                is_blocked = True
                break
        if is_blocked:
            continue

        eligible_items.append({
            "item_id": item_id,
            "title": title,
            "business_impact": business_impact,
            "urgency": urgency,
            "customer_commitment": customer_commitment,
            "risk_severity": risk_severity,
            "dependency_unblock": dependency_unblock,
            "ownership_match": ownership_match,
            "estimated_effort": estimated_effort,
            "created_at": created_at,
            "due_at": due_at,
            "role_required": role_required,
            "customer_id": customer_id
        })

    # === TẦNG 2: PRIORITY CLASSIFICATION & RANKING ===
    ranked_items = []
    for item in eligible_items:
        # 1. Tính toán raw score
        raw_score = (
            item["business_impact"] * 0.25
            + item["urgency"] * 0.25
            + item["customer_commitment"] * 0.15
            + item["risk_severity"] * 0.15
            + item["dependency_unblock"] * 0.10
            + item["ownership_match"] * 0.10
            - item["estimated_effort"] * 0.10
        )
        # Clamp score between 0.0 and 100.0
        priority_score = round(max(0.0, min(1.0, raw_score)) * 100, 2)

        # 2. Xếp loại vào Priority Bands
        # Band P0: Regulatory task hoặc Legal deadline khẩn cấp
        if "pháp lý" in item["title"].lower() or "regulatory" in item["title"].lower():
            band = 0
            band_name = "P0: Regulatory / Legal Deadline"
            rec_action = "review_evidence"
            ex_actions = ["execute_crm_action"]  # Khóa cấm execute trực tiếp
        # Band P1: SLA breach hoặc High risk
        elif item["urgency"] >= 0.8 or item["risk_severity"] >= 0.8:
            band = 1
            band_name = "P1: SLA Breach / High-Risk"
            rec_action = "resume_case_analysis"
            ex_actions = []
        # Band P2: Customer Commitment
        elif item["customer_commitment"] >= 0.7:
            band = 2
            band_name = "P2: Customer Commitment"
            rec_action = "prepare_proposal"
            ex_actions = []
        # Band P3: Normal opportunity
        else:
            band = 3
            band_name = "P3: Normal Work"
            rec_action = "update_profile"
            ex_actions = []

        # Generate reasons
        reasons = []
        if item["urgency"] >= 0.8:
            reasons.append("Task sắp quá hạn SLA trong ngày")
        if item["business_impact"] >= 0.8:
            reasons.append("Hồ sơ khách hàng phân khúc lớn có doanh số tiềm năng cao")
        if item["customer_commitment"] >= 0.8:
            reasons.append("Đã có lịch hẹn cam kết gửi đề xuất cho đối tác")
        if item["dependency_unblock"] >= 0.7:
            reasons.append("Hoàn thành task này sẽ mở khóa các bước thẩm định tiếp theo")
        if not reasons:
            reasons.append("Nhiệm vụ thông thường thuộc phạm vi chăm sóc được phân công")

        ranked_items.append({
            "item_id": item["item_id"],
            "title": item["title"],
            "priority_score": priority_score,
            "priority": "high" if band <= 1 else ("medium" if band == 2 else "low"),
            "band": band,
            "band_name": band_name,
            "reasons": reasons,
            "excluded_actions": ex_actions,
            "recommended_action": rec_action,
            # For tie-break
            "urgency_val": item["urgency"],
            "created_at": item["created_at"],
            "customer_commitment_val": item["customer_commitment"]
        })

    # Sort based on:
    # 1. Band asc (0 first, 1, 2, 3)
    # 2. Score desc (100 first)
    # 3. Tie-break: Urgency (desc), Commitment (desc), Created_at (asc), ID (asc)
    def sort_key(x):
        return (
            x["band"],
            -x["priority_score"],
            -x["urgency_val"],
            -x["customer_commitment_val"],
            x["created_at"],
            x["item_id"]
        )

    ranked_items.sort(key=sort_key)

    # Convert to NextBestWorkItem schemas
    results = []
    for item in ranked_items:
        results.append(NextBestWorkItem(
            work_item_id=item["item_id"],
            title=item["title"],
            priority_score=item["priority_score"],
            priority=item["priority"],
            reasons=item["reasons"],
            excluded_actions=item["excluded_actions"],
            recommended_action=item["recommended_action"]
        ))
    return results


def json_loads_safe(s: str) -> List[str]:
    try:
        return json.loads(s)
    except Exception:
        return []
