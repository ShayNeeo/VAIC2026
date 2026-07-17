"""Standardized service/tool error contract.

Mirrors plan_v2/03_SHARED_CONTRACTS.md section 5 ("Error contract") exactly so
every upstream failure (SSO/IAM/CRM/DMS/tool) surfaces the same shape instead
of ad hoc exceptions, and so no handler is tempted to leak a stack trace or
secret through an API response.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class ContextError(Exception):
    """Base class for every error raised out of app/context and app/integrations.

    Carries exactly the fields required by the module 03 error contract:
    error_code, message, retryable, safe_to_retry, correlation_id, details.
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        *,
        retryable: bool,
        safe_to_retry: bool,
        correlation_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.retryable = retryable
        self.safe_to_retry = safe_to_retry
        self.correlation_id = correlation_id
        self.details = details or {}

    def to_contract(self) -> Dict[str, Any]:
        """The exact dict shape the module 03 error contract defines."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "retryable": self.retryable,
            "safe_to_retry": self.safe_to_retry,
            "correlation_id": self.correlation_id,
            "details": self.details,
        }


class ContextAccessDeniedError(ContextError):
    """plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md section 3: selected customer
    not in the employee's scope must stop with CONTEXT_ACCESS_DENIED, never
    fall back to "closest" customer."""

    def __init__(self, correlation_id: str, *, employee_id: str, customer_id: str) -> None:
        super().__init__(
            "CONTEXT_ACCESS_DENIED",
            f"Employee {employee_id} khong duoc phep truy cap customer {customer_id}",
            retryable=False,
            safe_to_retry=False,
            correlation_id=correlation_id,
            details={"employee_id": employee_id, "customer_id": customer_id},
        )


class UpstreamTimeoutError(ContextError):
    """A named upstream (sso/iam/crm/workspace/dms) did not respond in time."""

    def __init__(self, correlation_id: str, *, upstream: str) -> None:
        super().__init__(
            f"{upstream.upper()}_TIMEOUT",
            f"Khong the ket noi {upstream} trong thoi gian cho phep",
            retryable=True,
            safe_to_retry=True,
            correlation_id=correlation_id,
            details={"upstream": upstream},
        )


class UpstreamUnavailableError(ContextError):
    """Upstream reachable but returned an error / no data (not a timeout)."""

    def __init__(self, correlation_id: str, *, upstream: str, reason: str) -> None:
        super().__init__(
            f"{upstream.upper()}_UNAVAILABLE",
            f"{upstream} khong tra ve du lieu hop le: {reason}",
            retryable=True,
            safe_to_retry=True,
            correlation_id=correlation_id,
            details={"upstream": upstream, "reason": reason},
        )
