"""V3 Error Handling & Resilience — retry, circuit breaker, timeout."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, TypeVar

from mcp_common.config import settings


logger = logging.getLogger(__name__)


# =============================================================================
# Error Types
# =============================================================================

class ErrorCode(str, Enum):
    """Standard error codes per V3 contract."""
    # Input errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INJECTION_DETECTED = "INJECTION_DETECTED"
    PII_VIOLATION = "PII_VIOLATION"

    # Retrieval errors
    RAG_UNAVAILABLE = "RAG_UNAVAILABLE"
    RAG_TIMEOUT = "RAG_TIMEOUT"
    NO_RESULTS = "NO_RESULTS"

    # Model errors
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_PARSE_ERROR = "LLM_PARSE_ERROR"

    # Verification errors
    EVIDENCE_INVALID = "EVIDENCE_INVALID"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"

    # Guardrail errors
    OUTPUT_BLOCKED = "OUTPUT_BLOCKED"
    LEGAL_BLOCKING = "LEGAL_BLOCKING"
    FEE_HALLUCINATION = "FEE_HALLUCINATION"

    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    CONFIG_ERROR = "CONFIG_ERROR"


class V3Error(Exception):
    """Base exception with error code and correlation."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        retryable: bool = False,
        safe_to_retry: bool = False,
        correlation_id: str = None,
        details: Dict[str, Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.retryable = retryable
        self.safe_to_retry = safe_to_retry
        self.correlation_id = correlation_id
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.code.value,
            "message": self.message,
            "retryable": self.retryable,
            "safe_to_retry": self.safe_to_retry,
            "correlation_id": self.correlation_id,
            "details": self.details,
        }


class RAGError(V3Error):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.RAG_UNAVAILABLE, retryable=True, safe_to_retry=True, **kwargs)


class LLMError(V3Error):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.LLM_UNAVAILABLE, retryable=True, safe_to_retry=True, **kwargs)


class EvidenceError(V3Error):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.EVIDENCE_INVALID, retryable=False, **kwargs)


class GuardrailError(V3Error):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.OUTPUT_BLOCKED, retryable=False, **kwargs)


# =============================================================================
# Circuit Breaker
# =============================================================================

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    excluded_exceptions: Tuple[Type[Exception], ...] = ()


class CircuitBreaker:
    """Circuit breaker for external dependencies."""

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            # Check if timeout has passed to transition to half-open
            if (self._last_failure_time and
                time.time() - self._last_failure_time >= self.config.timeout_seconds):
                return CircuitState.HALF_OPEN
        return self._state

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            current_state = self.state

            if current_state == CircuitState.OPEN:
                raise V3Error(
                    f"Circuit breaker {self.name} is OPEN",
                    code=ErrorCode.INTERNAL_ERROR,
                    retryable=True,
                    details={"circuit": self.name}
                )

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._on_success()
            return result

        except Exception as e:
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit breaker {self.name} CLOSED")
            else:
                self._failure_count = 0

    async def _on_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(f"Circuit breaker {self.name} re-OPENED from half-open")
            elif self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.name} OPENED after {self._failure_count} failures")


# Global circuit breakers
_rag_circuit = CircuitBreaker("rag", CircuitBreakerConfig(failure_threshold=5, timeout_seconds=30))
_llm_circuit = CircuitBreaker("llm", CircuitBreakerConfig(failure_threshold=3, timeout_seconds=60))


def get_rag_circuit() -> CircuitBreaker:
    return _rag_circuit


def get_llm_circuit() -> CircuitBreaker:
    return _llm_circuit


# =============================================================================
# Retry Decorator
# =============================================================================

T = TypeVar("T")


def with_retry(
    max_retries: int = None,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retry with exponential backoff."""

    max_retries = max_retries or settings.LLM_MAX_RETRIES

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}",
                            extra={"attempt": attempt + 1, "delay": delay}
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All retries exhausted for {func.__name__}")
                        raise
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                        )
                        time.sleep(delay)
                    else:
                        raise
            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# Timeout Wrapper
# =============================================================================

async def with_timeout(
    coro: Callable[..., T],
    timeout_seconds: float = None,
    *args,
    **kwargs,
) -> T:
    """Execute coroutine with timeout."""
    timeout = timeout_seconds or settings.LLM_TIMEOUT_SECONDS
    try:
        return await asyncio.wait_for(coro(*args, **kwargs), timeout=timeout)
    except asyncio.TimeoutError:
        raise V3Error(
            f"Operation timed out after {timeout}s",
            code=ErrorCode.LLM_TIMEOUT,
            retryable=True,
            safe_to_retry=True,
        )


# =============================================================================
# Resilient HTTP Client (for external APIs)
# =============================================================================

class ResilientHTTPClient:
    """HTTP client with circuit breaker, retry, and timeout."""

    def __init__(
        self,
        base_url: str,
        circuit_breaker: CircuitBreaker = None,
        default_timeout: float = 10.0,
    ):
        import httpx
        self.base_url = base_url.rstrip("/")
        self.circuit = circuit_breaker
        self.timeout = default_timeout
        self._client = httpx.AsyncClient(timeout=default_timeout)

    async def post(self, path: str, json: Dict = None, **kwargs) -> Dict:
        url = f"{self.base_url}{path}"

        async def _request():
            resp = await self._client.post(url, json=json, **kwargs)
            resp.raise_for_status()
            return resp.json()

        return await self.circuit.call(_request)

    async def get(self, path: str, params: Dict = None, **kwargs) -> Dict:
        url = f"{self.base_url}{path}"

        async def _request():
            resp = await self._client.get(url, params=params, **kwargs)
            resp.raise_for_status()
            return resp.json()

        return await self.circuit.call(_request)

    async def close(self):
        await self._client.aclose()