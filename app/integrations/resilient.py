"""Reliability wrappers for read-only upstream adapters."""

from __future__ import annotations

from app.integrations.enterprise import CRMPort, CustomerProfile
from app.integrations.errors import UpstreamTimeoutError, UpstreamUnavailableError
from app.reliability.patterns import CircuitBreaker, CircuitOpenError, retry_safe


class ResilientCRMAdapter:
    """Safe read retry + circuit breaker. It never converts failure into a successful profile."""

    def __init__(
        self,
        upstream: CRMPort,
        *,
        attempts: int = 2,
        failure_threshold: int = 3,
        recovery_seconds: float = 30.0,
    ) -> None:
        self.upstream = upstream
        self.attempts = attempts
        self.breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_seconds=recovery_seconds,
        )

    def get_customer_profile(self, customer_id: str, *, correlation_id: str) -> CustomerProfile:
        try:
            return self.breaker.call(
                lambda: retry_safe(
                    lambda: self.upstream.get_customer_profile(customer_id, correlation_id=correlation_id),
                    attempts=self.attempts,
                    retryable=(UpstreamTimeoutError, UpstreamUnavailableError),
                    idempotent=True,
                    base_delay=0.001,
                )
            )
        except CircuitOpenError as exc:
            raise UpstreamUnavailableError(
                correlation_id,
                upstream="crm",
                reason="circuit_open",
            ) from exc
