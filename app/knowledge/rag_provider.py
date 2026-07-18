"""RAG provider routing: local / mcp / hybrid, with a circuit breaker and
controlled, rate-limited fallback logging for the MCP path.

Consolidates retrieval-provider logic that ``ProductKnowledgeService`` and
``LegalKnowledgeService`` used to duplicate inline (each ~60 lines of
asyncio-bridging plus a bare ``try/except Exception: log + fall through``).
See ``docs/RAG_PROVIDER_AND_FALLBACK.md`` for the operational picture.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import time
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import Any, Callable, Coroutine, Generic, Optional, TypeVar

from app.observability.runtime import metrics

T = TypeVar("T")

VALID_MODES = ("local", "mcp", "hybrid")

# Exceptions treated as *transient/recoverable* -- safe to trigger a hybrid
# fallback to the local index. Deliberately narrow: a network-layer failure
# (no connection, DNS, read timeout, our own hard timeout) is the only thing
# that should make a hybrid deployment quietly serve local results instead of
# MCP results.
RECOVERABLE_EXCEPTIONS = (
    ConnectionError,
    ConnectionRefusedError,
    TimeoutError,
    OSError,
)


def is_recoverable_error(exc: BaseException) -> bool:
    """True if ``exc`` looks like a transient network/availability failure.

    NOT recoverable (must propagate, never trigger a silent fallback):
    ``RagMCPClient._call()`` turns an MCP tool-level denial (auth, prompt-
    injection guardrail, unknown chunk, invalid schema -- see
    ``services/rag_mcp/service.py``'s ``AccessDenied``/``UnsafeQuery``/
    ``ChunkNotFound``, all ``RagServiceError(RuntimeError)`` subclasses) into
    a bare ``RuntimeError``. Treating that as "recoverable" would silently
    serve local (unfiltered-by-the-same-policy) results after an
    authorization failure, which is exactly the anti-pattern this module
    exists to avoid.
    """
    return isinstance(exc, RECOVERABLE_EXCEPTIONS)


class RagProviderUnavailableError(RuntimeError):
    """Raised by mode="mcp" (never falls back) when the MCP call fails."""


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ProviderHealth:
    status: str  # "healthy" | "unavailable" | "unknown"
    latency_ms: Optional[float] = None
    error_code: Optional[str] = None


@dataclass
class SearchOutcome(Generic[T]):
    hits: T
    provider_requested: str
    provider_used: str
    fallback_used: bool
    fallback_reason: Optional[str]
    latency_ms: float


class CircuitBreaker:
    """Minimal 3-state (CLOSED/OPEN/HALF_OPEN) circuit breaker.

    ``clock`` is injectable so tests never need a real ``sleep()``.
    """

    def __init__(
        self,
        *,
        failure_threshold: int = 3,
        cooldown_seconds: float = 30.0,
        half_open_max_calls: int = 1,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if half_open_max_calls < 1:
            raise ValueError("half_open_max_calls must be >= 1")
        self._failure_threshold = failure_threshold
        self._cooldown_seconds = cooldown_seconds
        self._half_open_max_calls = half_open_max_calls
        self._clock = clock
        self._lock = RLock()
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at: Optional[float] = None
        self._half_open_calls_in_flight = 0

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._maybe_transition_to_half_open()
            return self._state

    def _maybe_transition_to_half_open(self) -> None:
        if self._state is CircuitState.OPEN and self._opened_at is not None:
            if self._clock() - self._opened_at >= self._cooldown_seconds:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls_in_flight = 0

    def allow_request(self) -> bool:
        """True if a caller may attempt the guarded (MCP) call right now."""
        with self._lock:
            self._maybe_transition_to_half_open()
            if self._state is CircuitState.CLOSED:
                return True
            if self._state is CircuitState.OPEN:
                return False
            if self._half_open_calls_in_flight < self._half_open_max_calls:
                self._half_open_calls_in_flight += 1
                return True
            return False

    def record_success(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._opened_at = None
            self._half_open_calls_in_flight = 0

    def record_failure(self) -> None:
        with self._lock:
            if self._state is CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._opened_at = self._clock()
                self._half_open_calls_in_flight = 0
                return
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = self._clock()


class RateLimitedWarningLogger:
    """Logs a WARNING at most once per ``cooldown_seconds`` per event key.

    Repeats within the cooldown window are demoted to DEBUG instead of being
    dropped entirely, so nothing is silently lost -- just not spammed at
    WARNING on every single request while a dependency is down.
    """

    def __init__(
        self,
        logger: logging.Logger,
        cooldown_seconds: float,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._logger = logger
        self._cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._lock = RLock()
        self._last_logged_at: dict[str, float] = {}

    def warn_once(self, key: str, message: str, *args: object) -> None:
        with self._lock:
            last = self._last_logged_at.get(key)
            now = self._clock()
            if last is not None and (now - last) < self._cooldown_seconds:
                self._logger.debug(message, *args)
                return
            self._last_logged_at[key] = now
        self._logger.warning(message, *args)

    def reset(self, key: str) -> None:
        with self._lock:
            self._last_logged_at.pop(key, None)


def make_async_bridge(coro_factory: Callable[[], Coroutine[Any, Any, T]]) -> Callable[[], T]:
    """Wrap a zero-arg async-coroutine factory into a sync zero-arg callable.

    Always calls ``asyncio.run()`` fresh. ``RagProviderRouter`` only ever
    invokes the returned callable inside its own dedicated worker thread
    (see ``_call_mcp_with_timeout``), so this never shares an event loop with
    a caller's already-running loop. The previous inline implementation in
    ``ProductKnowledgeService``/``LegalKnowledgeService`` sometimes reused the
    caller's running loop via a nested "ThreadPoolExecutor around
    asyncio.run" pattern, which is the likely cause of the
    ``tests/rag_mcp/test_transport.py`` flake ("Attempted to exit cancel
    scope in a different task than it was entered in") when run inside the
    full suite alongside other async tests.
    """

    def _call() -> T:
        return asyncio.run(coro_factory())

    return _call


class RagProviderRouter(Generic[T]):
    """Routes a retrieval call through RAG_PROVIDER=local|mcp|hybrid.

    - ``local``: only ever calls ``local_search``. Never touches MCP.
    - ``mcp``: only ever calls ``mcp_search``. Never falls back; raises
      ``RagProviderUnavailableError`` on failure.
    - ``hybrid``: prefers MCP, guarded by a circuit breaker + hard timeout.
      Falls back to ``local_search`` only for recoverable errors
      (``is_recoverable_error``); non-recoverable errors (auth/policy/schema)
      propagate instead of being silently swallowed.
    """

    def __init__(
        self,
        *,
        name: str,
        mode: str,
        timeout_seconds: float = 3.0,
        circuit_breaker: Optional[CircuitBreaker] = None,
        logger: Optional[logging.Logger] = None,
        warning_cooldown_seconds: float = 30.0,
        metrics_prefix: str = "rag",
    ) -> None:
        if mode not in VALID_MODES:
            raise ValueError(f"Unsupported RAG provider mode {mode!r}; must be one of {VALID_MODES}")
        self.name = name
        self.mode = mode
        self._timeout_seconds = timeout_seconds
        self._circuit = circuit_breaker or CircuitBreaker()
        self._logger = logger or logging.getLogger(f"app.knowledge.rag_provider.{name}")
        self._rate_limited = RateLimitedWarningLogger(self._logger, warning_cooldown_seconds)
        self._metrics_prefix = metrics_prefix
        # One dedicated executor for the lifetime of this router, reused
        # across every search() call. This is deliberately NOT created fresh
        # per call: (a) a fresh-per-call executor used inside a `with` block
        # would block on `.shutdown(wait=True)` at block-exit even after the
        # public-facing timeout already fired, defeating the timeout; (b) a
        # fresh-per-call executor that is never explicitly shut down leaks 2
        # live worker threads on every single search() call. Callers should
        # construct one RagProviderRouter per service instance (not per
        # request) -- see ProductKnowledgeService/LegalKnowledgeService.
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=2, thread_name_prefix=f"rag-provider-{name}"
        )

    @property
    def circuit_state(self) -> CircuitState:
        return self._circuit.state

    def close(self) -> None:
        self._executor.shutdown(wait=False)

    def search(self, *, local_search: Callable[[], T], mcp_search: Optional[Callable[[], T]] = None) -> SearchOutcome[T]:
        if self.mode in {"mcp", "hybrid"} and mcp_search is None:
            raise ValueError(f"mode={self.mode!r} requires an mcp_search callable")
        started = time.monotonic()
        metrics.increment(f"{self._metrics_prefix}.requests_total.{self.mode}")

        if self.mode == "local":
            hits = local_search()
            metrics.increment(f"{self._metrics_prefix}.local_result_total.success")
            return SearchOutcome(hits, "local", "local", False, None, self._elapsed_ms(started))

        assert mcp_search is not None
        if self.mode == "mcp":
            try:
                hits = self._call_mcp_with_timeout(mcp_search)
            except Exception as exc:
                metrics.increment(f"{self._metrics_prefix}.mcp_result_total.failure")
                self._logger.warning(
                    "event=rag_mcp_unavailable provider=%s mode=mcp no_fallback=true error_type=%s error=%s",
                    self.name, type(exc).__name__, exc,
                )
                raise RagProviderUnavailableError(
                    f"RAG provider '{self.name}' (mode=mcp) failed: {exc}"
                ) from exc
            metrics.increment(f"{self._metrics_prefix}.mcp_result_total.success")
            return SearchOutcome(hits, "mcp", "mcp", False, None, self._elapsed_ms(started))

        return self._search_hybrid(started, local_search, mcp_search)

    def _search_hybrid(self, started: float, local_search: Callable[[], T], mcp_search: Callable[[], T]) -> SearchOutcome[T]:
        if not self._circuit.allow_request():
            metrics.increment(f"{self._metrics_prefix}.mcp_result_total.circuit_open")
            hits = local_search()
            metrics.increment(f"{self._metrics_prefix}.local_result_total.success")
            self._rate_limited.warn_once(
                f"{self.name}:circuit_open",
                "event=rag_mcp_unavailable provider=%s fallback_provider=local circuit_state=open",
                self.name,
            )
            return SearchOutcome(hits, "hybrid", "local", True, "circuit_open", self._elapsed_ms(started))

        try:
            hits = self._call_mcp_with_timeout(mcp_search)
        except Exception as exc:
            if not is_recoverable_error(exc):
                metrics.increment(f"{self._metrics_prefix}.mcp_result_total.non_recoverable_error")
                self._logger.warning(
                    "event=rag_mcp_non_recoverable_error provider=%s error_type=%s error=%s "
                    "(not falling back -- looks like auth/policy/schema, not availability)",
                    self.name, type(exc).__name__, exc,
                )
                raise
            self._circuit.record_failure()
            metrics.increment(f"{self._metrics_prefix}.mcp_result_total.failure")
            metrics.increment(f"{self._metrics_prefix}.mcp_fallback_total.{type(exc).__name__}")
            state_after = self._circuit.state
            self._rate_limited.warn_once(
                f"{self.name}:mcp_error",
                "event=rag_mcp_unavailable provider=%s fallback_provider=local circuit_state=%s error_type=%s",
                self.name, state_after.value, type(exc).__name__,
            )
            hits = local_search()
            metrics.increment(f"{self._metrics_prefix}.local_result_total.success")
            return SearchOutcome(hits, "hybrid", "local", True, type(exc).__name__, self._elapsed_ms(started))
        else:
            was_recovering = self._circuit.state is not CircuitState.CLOSED
            self._circuit.record_success()
            metrics.increment(f"{self._metrics_prefix}.mcp_result_total.success")
            if was_recovering:
                self._logger.info("event=rag_mcp_recovered provider=%s circuit_state=closed", self.name)
                self._rate_limited.reset(f"{self.name}:mcp_error")
                self._rate_limited.reset(f"{self.name}:circuit_open")
            return SearchOutcome(hits, "hybrid", "mcp", False, None, self._elapsed_ms(started))

    def _call_mcp_with_timeout(self, mcp_search: Callable[[], T]) -> T:
        future = self._executor.submit(mcp_search)
        try:
            return future.result(timeout=self._timeout_seconds)
        except concurrent.futures.TimeoutError as exc:
            raise TimeoutError(
                f"RAG provider '{self.name}' MCP call exceeded {self._timeout_seconds}s"
            ) from exc

    def health(self) -> ProviderHealth:
        """Non-invasive status snapshot for /api/v2/health -- does not itself
        make a network call; a live MCP probe is left to the caller since it
        is a real network round trip and health checks should stay cheap."""
        return compute_health(self.mode, self._circuit)

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        return round((time.monotonic() - started) * 1000, 3)


def compute_health(mode: str, circuit: CircuitBreaker) -> ProviderHealth:
    """Cheap (no I/O) health snapshot shared by RagProviderRouter.health()
    and callers (ProductKnowledgeService.rag_health() /
    LegalKnowledgeService.rag_health()) that want a status without paying for
    a full RagProviderRouter construction (which owns a ThreadPoolExecutor)."""
    if mode == "local":
        return ProviderHealth(status="healthy")
    state = circuit.state
    if mode == "mcp":
        return ProviderHealth(status="unknown")
    if state is CircuitState.OPEN:
        return ProviderHealth(status="unavailable", error_code="circuit_open")
    return ProviderHealth(status="healthy" if state is CircuitState.CLOSED else "unknown")
