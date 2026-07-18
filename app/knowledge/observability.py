"""Retrieval observability -- RAG & Guardrail Implementation Plan Phase 5
section 48.

In-process structured event emission (no external metrics backend
dependency in this repo -- Prometheus/OpenTelemetry are not installed).
IMPLEMENTED_WITH_DETERMINISTIC_ADAPTER: real event schema and a real
in-memory recorder usable by tests and local debugging; NOT a production
metrics pipeline (no exporter, no persistence beyond process memory).
ControlledRetrievalOrchestrator accepts an optional `on_event` callback
(see retrieve()'s `observer` kwarg) so a real backend could be wired in
later without changing the event schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol


@dataclass(frozen=True)
class RetrievalEvent:
    event_type: str
    trace_id: str
    request_id: str
    retrieval_run_id: str
    agent_type: str
    strategy: Optional[str] = None
    candidate_count_before_filter: Optional[int] = None
    candidate_count_after_filter: Optional[int] = None
    blocked_reason_counts: Dict[str, int] = field(default_factory=dict)
    grounding_pack_id: Optional[str] = None
    selected_chunk_ids: List[str] = field(default_factory=list)
    latency_ms: Optional[int] = None
    error_code: Optional[str] = None

    def to_log_dict(self) -> Dict[str, Any]:
        """No PII/secret fields are ever included here (chunk_id/
        agent_type/reason codes only -- never chunk .content, never a raw
        query string that might carry customer-identifying free text)."""
        return {
            "event_type": self.event_type, "trace_id": self.trace_id, "request_id": self.request_id,
            "retrieval_run_id": self.retrieval_run_id, "agent_type": self.agent_type, "strategy": self.strategy,
            "candidate_count_before_filter": self.candidate_count_before_filter,
            "candidate_count_after_filter": self.candidate_count_after_filter,
            "blocked_reason_counts": self.blocked_reason_counts, "grounding_pack_id": self.grounding_pack_id,
            "selected_chunk_ids": self.selected_chunk_ids, "latency_ms": self.latency_ms, "error_code": self.error_code,
        }


class EventObserver(Protocol):
    def __call__(self, event: RetrievalEvent) -> None: ...


class InMemoryObservabilityRecorder:
    """Test/debug-friendly EventObserver -- collects every event so a
    caller (or a test) can assert on counts/reason codes without a real
    metrics backend."""

    def __init__(self) -> None:
        self.events: List[RetrievalEvent] = []

    def __call__(self, event: RetrievalEvent) -> None:
        self.events.append(event)

    def count_by_error_code(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for event in self.events:
            if event.error_code:
                counts[event.error_code] = counts.get(event.error_code, 0) + 1
        return counts

    def latencies_ms(self) -> List[int]:
        return [e.latency_ms for e in self.events if e.latency_ms is not None]
