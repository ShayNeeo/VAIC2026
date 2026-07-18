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
