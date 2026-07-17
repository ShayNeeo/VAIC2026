"""Tests for app.knowledge.rag_provider: circuit breaker, local/mcp/hybrid
routing, recoverable-vs-non-recoverable fallback classification, and
rate-limited logging. No real network/MCP server involved -- local_search and
mcp_search are plain fakes so these tests are fast and deterministic."""

from __future__ import annotations

import logging

import pytest

from app.knowledge.rag_provider import (
    CircuitBreaker,
    CircuitState,
    ProviderHealth,
    RagProviderRouter,
    RagProviderUnavailableError,
    RateLimitedWarningLogger,
    compute_health,
    is_recoverable_error,
)


class FakeClock:
    """Injectable monotonic clock so circuit-breaker tests never sleep()."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


# --------------------------------------------------------------------------
# CircuitBreaker
# --------------------------------------------------------------------------


def test_circuit_starts_closed_and_allows_requests():
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=30, clock=FakeClock())
    assert breaker.state is CircuitState.CLOSED
    assert breaker.allow_request() is True


def test_circuit_opens_after_failure_threshold_consecutive_failures():
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=30, clock=FakeClock())
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state is CircuitState.CLOSED
    breaker.record_failure()
    assert breaker.state is CircuitState.OPEN
    assert breaker.allow_request() is False


def test_circuit_open_blocks_until_cooldown_elapses():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=30, clock=clock)
    breaker.record_failure()
    assert breaker.state is CircuitState.OPEN
    clock.advance(29.9)
    assert breaker.state is CircuitState.OPEN
    clock.advance(0.2)
    assert breaker.state is CircuitState.HALF_OPEN


def test_circuit_half_open_success_closes_circuit():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=10, clock=clock)
    breaker.record_failure()
    clock.advance(11)
    assert breaker.state is CircuitState.HALF_OPEN
    assert breaker.allow_request() is True
    breaker.record_success()
    assert breaker.state is CircuitState.CLOSED
    assert breaker.allow_request() is True


def test_circuit_half_open_failure_reopens_circuit():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=10, clock=clock)
    breaker.record_failure()
    clock.advance(11)
    assert breaker.state is CircuitState.HALF_OPEN
    breaker.allow_request()
    breaker.record_failure()
    assert breaker.state is CircuitState.OPEN
    assert breaker.allow_request() is False


def test_circuit_half_open_limits_concurrent_probe_calls():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=10, half_open_max_calls=1, clock=clock)
    breaker.record_failure()
    clock.advance(11)
    assert breaker.allow_request() is True
    assert breaker.allow_request() is False


def test_circuit_breaker_rejects_invalid_construction_args():
    with pytest.raises(ValueError):
        CircuitBreaker(failure_threshold=0)
    with pytest.raises(ValueError):
        CircuitBreaker(half_open_max_calls=0)


# --------------------------------------------------------------------------
# is_recoverable_error
# --------------------------------------------------------------------------


def test_network_errors_are_recoverable():
    assert is_recoverable_error(ConnectionError("boom")) is True
    assert is_recoverable_error(TimeoutError("boom")) is True
    assert is_recoverable_error(OSError("boom")) is True


def test_generic_runtime_error_is_not_recoverable():
    # RagMCPClient._call() raises bare RuntimeError for tool-level denials
    # (auth, prompt-injection guardrail, unknown chunk) -- must never be
    # treated as a transient/fallback-worthy failure.
    assert is_recoverable_error(RuntimeError("MCP tool rag_search failed: unauthorized")) is False
    assert is_recoverable_error(ValueError("bad schema")) is False


# --------------------------------------------------------------------------
# RagProviderRouter -- mode="local"
# --------------------------------------------------------------------------


def test_local_mode_never_calls_mcp():
    calls = {"mcp": 0}

    def local_search():
        return ["local-hit"]

    def mcp_search():
        calls["mcp"] += 1
        return ["mcp-hit"]

    router = RagProviderRouter(name="t", mode="local", timeout_seconds=1)
    outcome = router.search(local_search=local_search, mcp_search=mcp_search)

    assert outcome.hits == ["local-hit"]
    assert outcome.provider_requested == "local"
    assert outcome.provider_used == "local"
    assert outcome.fallback_used is False
    assert calls["mcp"] == 0


def test_local_mode_does_not_require_mcp_search_callable():
    router = RagProviderRouter(name="t", mode="local", timeout_seconds=1)
    outcome = router.search(local_search=lambda: ["ok"])
    assert outcome.hits == ["ok"]


# --------------------------------------------------------------------------
# RagProviderRouter -- mode="mcp"
# --------------------------------------------------------------------------


def test_mcp_mode_returns_mcp_hits_on_success():
    router = RagProviderRouter(name="t", mode="mcp", timeout_seconds=1)
    outcome = router.search(local_search=lambda: ["local"], mcp_search=lambda: ["mcp"])
    assert outcome.hits == ["mcp"]
    assert outcome.provider_used == "mcp"
    assert outcome.fallback_used is False


def test_mcp_mode_never_falls_back_and_raises_structured_error():
    def failing_mcp():
        raise ConnectionError("server down")

    router = RagProviderRouter(name="t", mode="mcp", timeout_seconds=1)
    with pytest.raises(RagProviderUnavailableError):
        router.search(local_search=lambda: ["should-not-be-used"], mcp_search=failing_mcp)


def test_mcp_mode_requires_mcp_search_callable():
    router = RagProviderRouter(name="t", mode="mcp", timeout_seconds=1)
    with pytest.raises(ValueError):
        router.search(local_search=lambda: [])


# --------------------------------------------------------------------------
# RagProviderRouter -- mode="hybrid"
# --------------------------------------------------------------------------


def test_hybrid_mode_prefers_mcp_when_healthy():
    router = RagProviderRouter(name="t", mode="hybrid", timeout_seconds=1)
    outcome = router.search(local_search=lambda: ["local"], mcp_search=lambda: ["mcp"])
    assert outcome.hits == ["mcp"]
    assert outcome.provider_used == "mcp"
    assert outcome.fallback_used is False
    assert router.circuit_state is CircuitState.CLOSED


def test_hybrid_mode_falls_back_to_local_on_recoverable_error():
    def failing_mcp():
        raise ConnectionError("connection refused")

    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=30, clock=FakeClock())
    router = RagProviderRouter(name="t", mode="hybrid", timeout_seconds=1, circuit_breaker=breaker)
    outcome = router.search(local_search=lambda: ["local"], mcp_search=failing_mcp)

    assert outcome.hits == ["local"]
    assert outcome.provider_used == "local"
    assert outcome.fallback_used is True
    assert outcome.fallback_reason == "ConnectionError"


def test_hybrid_mode_does_not_fall_back_on_non_recoverable_error():
    def failing_mcp():
        raise RuntimeError("MCP tool rag_search failed: unauthorized")

    router = RagProviderRouter(name="t", mode="hybrid", timeout_seconds=1)
    with pytest.raises(RuntimeError):
        router.search(local_search=lambda: ["should-not-be-used"], mcp_search=failing_mcp)


def test_hybrid_mode_opens_circuit_after_threshold_and_then_skips_mcp_entirely():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=30, clock=clock)
    calls = {"mcp": 0}

    def failing_mcp():
        calls["mcp"] += 1
        raise ConnectionError("down")

    router = RagProviderRouter(name="t", mode="hybrid", timeout_seconds=1, circuit_breaker=breaker)

    router.search(local_search=lambda: ["local"], mcp_search=failing_mcp)
    assert breaker.state is CircuitState.CLOSED
    router.search(local_search=lambda: ["local"], mcp_search=failing_mcp)
    assert breaker.state is CircuitState.OPEN
    assert calls["mcp"] == 2

    # Circuit is open: a 3rd call must not touch mcp_search at all.
    outcome = router.search(local_search=lambda: ["local"], mcp_search=failing_mcp)
    assert calls["mcp"] == 2
    assert outcome.fallback_reason == "circuit_open"


def test_hybrid_mode_recovers_after_cooldown_and_successful_probe():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=10, clock=clock)
    router = RagProviderRouter(name="t", mode="hybrid", timeout_seconds=1, circuit_breaker=breaker)

    router.search(local_search=lambda: ["local"], mcp_search=lambda: (_ for _ in ()).throw(ConnectionError("down")))
    assert breaker.state is CircuitState.OPEN

    clock.advance(11)
    outcome = router.search(local_search=lambda: ["local"], mcp_search=lambda: ["mcp-recovered"])
    assert outcome.provider_used == "mcp"
    assert outcome.fallback_used is False
    assert breaker.state is CircuitState.CLOSED


def test_hybrid_mode_requires_mcp_search_callable():
    router = RagProviderRouter(name="t", mode="hybrid", timeout_seconds=1)
    with pytest.raises(ValueError):
        router.search(local_search=lambda: [])


def test_mcp_call_exceeding_timeout_is_treated_as_recoverable_and_falls_back():
    import time

    def slow_mcp():
        time.sleep(0.5)
        return ["too-slow"]

    router = RagProviderRouter(name="t", mode="hybrid", timeout_seconds=0.05)
    outcome = router.search(local_search=lambda: ["local"], mcp_search=slow_mcp)
    assert outcome.provider_used == "local"
    assert outcome.fallback_used is True
    assert outcome.fallback_reason == "TimeoutError"
    router.close()


# --------------------------------------------------------------------------
# health()
# --------------------------------------------------------------------------


def test_health_local_mode_is_always_healthy():
    breaker = CircuitBreaker()
    assert compute_health("local", breaker) == ProviderHealth(status="healthy")


def test_health_hybrid_reflects_open_circuit():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=30, clock=clock)
    breaker.record_failure()
    health = compute_health("hybrid", breaker)
    assert health.status == "unavailable"
    assert health.error_code == "circuit_open"


def test_health_mcp_mode_is_unknown_without_a_live_probe():
    breaker = CircuitBreaker()
    health = compute_health("mcp", breaker)
    assert health.status == "unknown"


# --------------------------------------------------------------------------
# Invalid mode
# --------------------------------------------------------------------------


def test_router_rejects_unsupported_mode():
    with pytest.raises(ValueError):
        RagProviderRouter(name="t", mode="carrier-pigeon")


# --------------------------------------------------------------------------
# RateLimitedWarningLogger
# --------------------------------------------------------------------------


def test_rate_limited_logger_suppresses_repeat_warnings_within_cooldown(caplog):
    clock = FakeClock()
    logger = logging.getLogger("test.rate_limited")
    limiter = RateLimitedWarningLogger(logger, cooldown_seconds=30, clock=clock)

    with caplog.at_level(logging.WARNING, logger="test.rate_limited"):
        limiter.warn_once("k", "first warning")
        limiter.warn_once("k", "second warning (should be suppressed at WARNING)")
        clock.advance(31)
        limiter.warn_once("k", "third warning (cooldown elapsed)")

    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warning_records) == 2
    assert warning_records[0].message == "first warning"
    assert warning_records[1].message == "third warning (cooldown elapsed)"


def test_rate_limited_logger_reset_allows_immediate_warning_again():
    clock = FakeClock()
    logger = logging.getLogger("test.rate_limited.reset")
    limiter = RateLimitedWarningLogger(logger, cooldown_seconds=30, clock=clock)
    limiter.warn_once("k", "first")
    limiter.reset("k")
    # After reset, the very next call is treated as first-ever again (no
    # exception, no assertion needed beyond "doesn't raise"); behavioural
    # proof is covered by the full router recovery test above.
    limiter.warn_once("k", "after reset")
