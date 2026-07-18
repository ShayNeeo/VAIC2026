"""Runtime adapter reliability tests."""

from __future__ import annotations

import pytest

from app.integrations.errors import UpstreamTimeoutError, UpstreamUnavailableError
from app.integrations.resilient import ResilientCRMAdapter


class TransientCRM:
    def __init__(self):
        self.calls = 0

    def get_customer_profile(self, customer_id: str, *, correlation_id: str):
        self.calls += 1
        if self.calls == 1:
            raise UpstreamTimeoutError(correlation_id, upstream="crm")
        return {
            "customer_id": customer_id,
            "profile_version": "v1",
            "attributes": {},
            "observed_at": "2026-07-17T00:00:00+00:00",
        }


class DownCRM:
    def get_customer_profile(self, customer_id: str, *, correlation_id: str):
        raise UpstreamTimeoutError(correlation_id, upstream="crm")


def test_transient_read_timeout_is_retried_safely():
    upstream = TransientCRM()
    profile = ResilientCRMAdapter(upstream).get_customer_profile("COMP-1", correlation_id="TRACE-1")
    assert profile["customer_id"] == "COMP-1"
    assert upstream.calls == 2


def test_open_circuit_surfaces_standard_fail_closed_error():
    adapter = ResilientCRMAdapter(DownCRM(), attempts=1, failure_threshold=1, recovery_seconds=60)
    with pytest.raises(UpstreamTimeoutError):
        adapter.get_customer_profile("COMP-1", correlation_id="TRACE-1")
    with pytest.raises(UpstreamUnavailableError) as error:
        adapter.get_customer_profile("COMP-1", correlation_id="TRACE-2")
    assert error.value.details["reason"] == "circuit_open"
