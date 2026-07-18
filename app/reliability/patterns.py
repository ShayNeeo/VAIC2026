"""Dependency-free reliability primitives with explicit safe-retry controls."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import Any, Callable, Dict, Hashable, Optional, Tuple, TypeVar


T = TypeVar("T")


def retry_safe(
    operation: Callable[[], T],
    *,
    attempts: int = 2,
    retryable: Tuple[type[Exception], ...] = (TimeoutError,),
    idempotent: bool = True,
    base_delay: float = 0.01,
) -> T:
    if not idempotent and attempts > 1:
        raise ValueError("non-idempotent operation cannot be retried")
    for attempt in range(attempts):
        try:
            return operation()
        except retryable:
            if attempt == attempts - 1:
                raise
            time.sleep(base_delay * (2**attempt) + random.random() * base_delay)
    raise RuntimeError("unreachable")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    pass


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int = 3, recovery_seconds: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.failures = 0
        self.opened_at: Optional[float] = None
        self.state = CircuitState.CLOSED
        self._lock = RLock()

    def call(self, operation: Callable[[], T]) -> T:
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self.opened_at is not None and time.monotonic() - self.opened_at >= self.recovery_seconds:
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise CircuitOpenError("dependency circuit is open")
        try:
            result = operation()
        except Exception:
            with self._lock:
                self.failures += 1
                if self.failures >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.opened_at = time.monotonic()
            raise
        with self._lock:
            self.failures = 0
            self.opened_at = None
            self.state = CircuitState.CLOSED
        return result


@dataclass
class _CacheEntry:
    value: Any
    expires_at: float


class ScopedTTLCache:
    """Keys always include access scope, preventing cross-user cache reuse."""

    def __init__(self) -> None:
        self._items: Dict[Tuple[Hashable, Hashable, Hashable], _CacheEntry] = {}
        self._lock = RLock()

    def set(self, *, scope: Hashable, version: Hashable, key: Hashable, value: Any, ttl_seconds: float) -> None:
        with self._lock:
            self._items[(scope, version, key)] = _CacheEntry(value, time.monotonic() + ttl_seconds)

    def get(self, *, scope: Hashable, version: Hashable, key: Hashable) -> Any:
        composite = (scope, version, key)
        with self._lock:
            entry = self._items.get(composite)
            if entry is None or entry.expires_at <= time.monotonic():
                self._items.pop(composite, None)
                return None
            return entry.value
