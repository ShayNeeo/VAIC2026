"""V3 Observability — structured logging, tracing, metrics."""

from __future__ import annotations

import logging
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, Optional

from mcp_common.config import settings


# =============================================================================
# Structured Logging
# =============================================================================

class StructuredFormatter(logging.Formatter):
    """JSON-like structured log formatter with trace correlation."""

    def format(self, record: logging.LogRecord) -> str:
        # Base fields
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add trace context if available
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if hasattr(record, "case_id"):
            log_data["case_id"] = record.case_id
        if hasattr(record, "customer_id"):
            log_data["customer_id"] = record.customer_id
        if hasattr(record, "rm_id"):
            log_data["rm_id"] = record.rm_id

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "name", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "trace_id", "case_id",
                "customer_id", "rm_id"
            }:
                log_data[key] = value

        return str(log_data)


def setup_logging(level: str = None) -> logging.Logger:
    """Configure structured logging for the service."""
    level = level or settings.LOG_LEVEL
    log_level = getattr(logging, level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler with structured formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get logger with service context."""
    return logging.getLogger(name)


# =============================================================================
# Tracing Context
# =============================================================================

class TraceContext:
    """Thread-local trace context for correlation."""

    def __init__(self):
        self.trace_id: Optional[str] = None
        self.case_id: Optional[str] = None
        self.customer_id: Optional[str] = None
        self.rm_id: Optional[str] = None
        self.span_id: Optional[str] = None
        self.parent_span_id: Optional[str] = None

    def new_trace(self, trace_id: str = None) -> "TraceContext":
        self.trace_id = trace_id or uuid.uuid4().hex[:16]
        self.span_id = uuid.uuid4().hex[:8]
        return self

    def child_span(self) -> "TraceContext":
        child = TraceContext()
        child.trace_id = self.trace_id
        child.case_id = self.case_id
        child.customer_id = self.customer_id
        child.rm_id = self.rm_id
        child.parent_span_id = self.span_id
        child.span_id = uuid.uuid4().hex[:8]
        return child


# Global trace context (use thread-local in production)
_trace_context = TraceContext()


def get_trace_context() -> TraceContext:
    return _trace_context


def set_trace_context(context: TraceContext) -> None:
    global _trace_context
    _trace_context = context


@contextmanager
def trace_span(name: str, **tags) -> Generator["Span", None, None]:
    """Context manager for creating trace spans."""
    span = Span(name, **tags)
    try:
        yield span
    finally:
        span.finish()


@dataclass
class Span:
    """Distributed tracing span."""
    name: str
    tags: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    trace_id: str = field(default_factory=lambda: _trace_context.trace_id or "")
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    parent_span_id: str = field(default_factory=lambda: _trace_context.span_id or "")

    def finish(self) -> None:
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000
        logger = get_logger("tracing")
        logger.info(
            f"span_complete: {self.name}",
            extra={
                "trace_id": self.trace_id,
                "span_id": self.span_id,
                "parent_span_id": self.parent_span_id,
                "duration_ms": duration_ms,
                **self.tags,
            }
        )

    def add_tag(self, key: str, value: Any) -> None:
        self.tags[key] = value


# =============================================================================
# Metrics
# =============================================================================

class MetricsCollector:
    """In-memory metrics collector (prometheus-compatible in production)."""

    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = {}

    def increment(self, name: str, value: int = 1, tags: Dict[str, str] = None) -> None:
        key = self._make_key(name, tags)
        self._counters[key] = self._counters.get(key, 0) + value

    def gauge(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        key = self._make_key(name, tags)
        self._gauges[key] = value

    def histogram(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        key = self._make_key(name, tags)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"

    def get_all(self) -> Dict[str, Any]:
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {k: {"count": len(v), "sum": sum(v), "avg": sum(v)/len(v) if v else 0}
                          for k, v in self._histograms.items()},
        }


# Global metrics
_metrics = MetricsCollector()


def metrics() -> MetricsCollector:
    return _metrics


def record_request(
    endpoint: str,
    method: str,
    status: int,
    duration_ms: float,
    trace_id: str = None,
) -> None:
    """Record HTTP request metrics."""
    _metrics.increment("http_requests_total", tags={
        "endpoint": endpoint,
        "method": method,
        "status": str(status),
    })
    _metrics.histogram("http_request_duration_ms", duration_ms, tags={
        "endpoint": endpoint,
    })

    logger = get_logger("access")
    logger.info(
        f"{method} {endpoint} {status} {duration_ms:.1f}ms",
        extra={"trace_id": trace_id} if trace_id else {}
    )


def record_rag_metrics(
    query: str,
    results_count: int,
    top_score: float,
    duration_ms: float,
    trace_id: str = None,
) -> None:
    """Record RAG retrieval metrics."""
    _metrics.increment("rag_queries_total")
    _metrics.gauge("rag_results_count", results_count)
    _metrics.histogram("rag_top_score", top_score)
    _metrics.histogram("rag_duration_ms", duration_ms)

    logger = get_logger("rag")
    logger.debug(
        f"rag_query: results={results_count}, top_score={top_score:.4f}, duration={duration_ms:.1f}ms",
        extra={"trace_id": trace_id} if trace_id else {}
    )


def record_evidence_verification(
    valid: int,
    invalid: int,
    trace_id: str = None,
) -> None:
    """Record evidence verification metrics."""
    _metrics.increment("evidence_verified_total", valid, tags={"result": "valid"})
    _metrics.increment("evidence_verified_total", invalid, tags={"result": "invalid"})
    _metrics.gauge("evidence_valid_ratio", valid / (valid + invalid) if (valid + invalid) > 0 else 0)


def record_guardrail_decision(
    allowed: bool,
    flags: list,
    trace_id: str = None,
) -> None:
    """Record guardrail decision metrics."""
    _metrics.increment("guardrail_decisions_total", tags={
        "allowed": str(allowed).lower(),
    })
    for flag in flags:
        _metrics.increment("guardrail_flags_total", tags={"flag": flag})


# =============================================================================
# Health Check Details
# =============================================================================

@dataclass
class HealthCheckResult:
    """Detailed health check result."""
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "status": self.status,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "details": self.details,
        }


class HealthChecker:
    """Composite health checker for all components."""

    def __init__(self):
        self._checks: Dict[str, callable] = {}

    def register(self, name: str, check_fn: callable) -> None:
        self._checks[name] = check_fn

    async def run_all(self) -> Dict[str, Any]:
        results = {}
        overall_healthy = True

        for name, check_fn in self._checks.items():
            try:
                start = time.time()
                result = await check_fn() if hasattr(check_fn, "__await__") else check_fn()
                latency = (time.time() - start) * 1000

                if isinstance(result, HealthCheckResult):
                    result.latency_ms = latency
                    results[name] = result.to_dict()
                elif isinstance(result, dict):
                    result["latency_ms"] = latency
                    results[name] = result
                else:
                    results[name] = {
                        "status": "healthy" if result else "unhealthy",
                        "message": str(result),
                        "latency_ms": latency,
                    }

                if results[name].get("status") != "healthy":
                    overall_healthy = False

            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "message": str(e),
                    "latency_ms": None,
                }
                overall_healthy = False

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": time.time(),
            "components": results,
        }


# =============================================================================
# Initialize
# =============================================================================

def init_observability(service_name: str) -> HealthChecker:
    """Initialize observability for a service."""
    setup_logging()
    logger = get_logger(service_name)
    logger.info(f"Observability initialized for {service_name}")

    health_checker = HealthChecker()
    return health_checker