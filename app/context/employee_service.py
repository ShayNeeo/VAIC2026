"""Employee context: identity (SSO/HRIS) + permissions (IAM).

plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md section 9: "IAM timeout -> Fail
closed for sensitive reads/writes". This service does not catch IAM errors:
if IAM fails, no Employee is constructed at all, so no caller can
accidentally treat a failed permission lookup as "no permissions" (open) or
proceed as if the employee had valid access.
"""

from __future__ import annotations

from app.integrations.enterprise import EmployeeIdentity, IAMPort, PermissionGrant, SSOPort
from app.schemas.v2.context_snapshot import Employee


class EmployeeContextService:
    def __init__(self, sso: SSOPort, iam: IAMPort) -> None:
        self._sso = sso
        self._iam = iam

    def get(self, employee_id: str, *, correlation_id: str) -> Employee:
        identity = self._sso.get_employee_identity(employee_id, correlation_id=correlation_id)
        grant = self._iam.get_permissions(employee_id, correlation_id=correlation_id)
        return Employee(
            employee_id=identity["employee_id"],
            role=identity["role"],
            organization_unit=identity["organization_unit"],
            permissions=grant["permissions"],
            access_scope=grant["access_scope"],
        )
