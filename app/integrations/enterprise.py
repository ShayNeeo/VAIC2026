"""Enterprise SQLite Adapters for CRM, IAM, and SSO.
Replaces in-memory Mock adapters for production-ready persistence.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Protocol, TypedDict

from app.integrations.errors import UpstreamTimeoutError, UpstreamUnavailableError

class CustomerProfile(TypedDict):
    customer_id: str
    profile_version: str
    attributes: Dict[str, Any]
    observed_at: str

class CRMPort(Protocol):
    def get_customer_profile(self, customer_id: str, *, correlation_id: str) -> CustomerProfile: ...

class PermissionGrant(TypedDict):
    permissions: List[str]
    access_scope: Dict[str, Any]

class IAMPort(Protocol):
    def get_permissions(self, employee_id: str, *, correlation_id: str) -> PermissionGrant: ...

class EmployeeIdentity(TypedDict):
    employee_id: str
    role: str
    organization_unit: str

class SSOPort(Protocol):
    def get_employee_identity(self, employee_id: str, *, correlation_id: str) -> EmployeeIdentity: ...



class EnterpriseSQLiteBase:
    def __init__(self, db_path: Path | str | None = None, *, fail_for: set[str] | None = None):
        if db_path is None:
            self.db_path = Path(__file__).resolve().parents[2] / "data" / "mock_database" / "enterprise_core.sqlite3"
        else:
            self.db_path = Path(db_path)
        self._fail_for = fail_for or set()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


class SQLiteCRMAdapter(EnterpriseSQLiteBase):
    def get_customer_profile(self, customer_id: str, *, correlation_id: str) -> CustomerProfile:
        if customer_id in self._fail_for:
            raise UpstreamTimeoutError(correlation_id, upstream="crm")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT profile_version, attributes FROM customers WHERE customer_id = ?", (customer_id,))
            row = cursor.fetchone()
            
            if not row:
                raise UpstreamUnavailableError(correlation_id, upstream="crm", reason=f"unknown customer_id {customer_id}")
                
            return {
                "customer_id": customer_id,
                "profile_version": row["profile_version"],
                "attributes": json.loads(row["attributes"]),
                "observed_at": datetime.now(timezone.utc).isoformat(),
            }


class SQLiteIAMAdapter(EnterpriseSQLiteBase):
    def get_permissions(self, employee_id: str, *, correlation_id: str) -> PermissionGrant:
        if employee_id in self._fail_for:
            raise UpstreamTimeoutError(correlation_id, upstream="iam")
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT permissions, access_scope FROM permissions WHERE employee_id = ?", (employee_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"permissions": [], "access_scope": {"managed_customer_ids": [], "branch": None}}
                
            return {
                "permissions": json.loads(row["permissions"]),
                "access_scope": json.loads(row["access_scope"]),
            }


_EMPLOYEE_COPILOT_DEMO_PERSONAS: list[tuple[str, str, str, list[str], dict]] = [
    # (employee_id, coarse_role, organization_unit, permissions, access_scope)
    # RM-999 already exists in enterprise_core.sqlite3 from the original
    # seed; these four were only ever seeded into the newer, separate
    # employee_db.py (data/state/v2.sqlite3) SQLite file, which meant
    # SQLiteSSOAdapter/SQLiteIAMAdapter could never resolve them. Adding
    # them here (idempotently) makes IAMPort/SSOPort the single place that
    # knows about every demo employee, instead of two disconnected seed
    # sources for the same five-person demo cast.
    ("SPEC-LEGAL-001", "Specialist", "Legal & Compliance",
     ["case:read", "case:verify_evidence", "legal:check_issue", "legal:block_non_eligible"],
     {"managed_customer_ids": ["COMP-ABC", "COMP-MP", "COMP-XYZ"], "branch": "HN01"}),
    ("SPEC-PROD-001", "Specialist", "Product",
     ["case:read", "product:recommend", "product:verify_fit"],
     {"managed_customer_ids": ["COMP-ABC", "COMP-MP", "COMP-XYZ"], "branch": "HN01"}),
    ("SPEC-OPS-001", "Specialist", "Operations",
     ["case:read", "task:update", "ops:update_implementation"],
     {"managed_customer_ids": ["COMP-ABC", "COMP-MP", "COMP-XYZ"], "branch": "HN01"}),
    ("MGR-HN-01", "Manager", "Branch HN Management",
     ["team:view_workload", "case:read"],
     {"managed_customer_ids": ["COMP-ABC", "COMP-MP", "COMP-XYZ"], "branch": "HN01"}),
]


def ensure_employee_copilot_demo_personas(db_path: Path | str | None = None) -> None:
    """Idempotently add the Employee Copilot demo personas to the real
    enterprise IAM/SSO database, if they are not already present -- and keep
    their `permissions` JSON in sync with _EMPLOYEE_COPILOT_DEMO_PERSONAS
    above (an upsert, not INSERT OR IGNORE, specifically for that one
    column) so adding a new specialist-review capability to this list
    actually takes effect on the next process start instead of silently
    freezing at whatever was seeded the first time this ran. `employees`
    rows (identity/org unit) are still insert-or-ignore-only -- unlike
    scripts/init_enterprise_db.py (a one-time, now-broken migration that
    would wipe this table -- do not reuse that script), this never deletes
    a row and never touches any OTHER employee's permissions."""
    path = Path(db_path) if db_path is not None else (
        Path(__file__).resolve().parents[2] / "data" / "mock_database" / "enterprise_core.sqlite3"
    )
    conn = sqlite3.connect(path)
    try:
        cursor = conn.cursor()
        for employee_id, role, org_unit, permissions, access_scope in _EMPLOYEE_COPILOT_DEMO_PERSONAS:
            cursor.execute(
                "INSERT OR IGNORE INTO employees (employee_id, role, organization_unit) VALUES (?, ?, ?)",
                (employee_id, role, org_unit),
            )
            cursor.execute(
                """
                INSERT INTO permissions (employee_id, permissions, access_scope) VALUES (?, ?, ?)
                ON CONFLICT(employee_id) DO UPDATE SET permissions = excluded.permissions
                """,
                (employee_id, json.dumps(permissions), json.dumps(access_scope)),
            )
        conn.commit()
    finally:
        conn.close()


def map_enterprise_role_to_role_type(role: str, organization_unit: str) -> str:
    """Bridge the coarse IAM role ("RM"/"Specialist"/"Manager"/"DataSteward")
    to the fine-grained RoleType the Next Best Work / role-routing layer
    needs. Returns a RoleType.value string (caller wraps in RoleType()) to
    avoid a schemas -> integrations import cycle."""
    role_lower = role.lower()
    unit_lower = organization_unit.lower()
    if role_lower == "rm":
        return "relationship_manager"
    if role_lower == "manager":
        return "manager"
    if role_lower == "specialist":
        if "legal" in unit_lower:
            return "legal_specialist"
        if "product" in unit_lower:
            return "product_specialist"
        if "operations" in unit_lower or "credit" in unit_lower:
            return "operations_specialist"
        return "operations_specialist"
    if role_lower == "datasteward":
        return "auditor"
    return "auditor"


class SQLiteSSOAdapter(EnterpriseSQLiteBase):
    def get_employee_identity(self, employee_id: str, *, correlation_id: str) -> EmployeeIdentity:
        if employee_id in self._fail_for:
            raise UpstreamTimeoutError(correlation_id, upstream="sso")
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, organization_unit FROM employees WHERE employee_id = ?", (employee_id,))
            row = cursor.fetchone()
            
            if not row:
                raise UpstreamUnavailableError(correlation_id, upstream="sso", reason=f"unknown employee_id {employee_id}")
                
            return {
                "employee_id": employee_id,
                "role": row["role"],
                "organization_unit": row["organization_unit"],
            }
