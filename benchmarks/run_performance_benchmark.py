"""Phase 5 section 50: performance benchmark -- real timings, no fabricated
targets. Measures ControlledRetrievalOrchestrator.retrieve() latency
(LocalEmbedding, in-process SQLite -- this repo's only environment that
runs without network/API cost) across cold (first call, empty
process-level caches) and warm (repeated call, OS file-cache warm) runs,
and across this repo's two real corpus sizes (Legal=9 chunks,
Operations=15 chunks after Phase 3's parent-child overview chunks).

Live semantic-provider (OpenAI/Gemini) latency is explicitly NOT measured
here -- see docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md Phase 2's "Phát
hiện phụ" for why benchmarking against the real API risks colliding with
the shared data/vector_db/openai_vector_cache.json file another agent
uses concurrently in this repo. That number is BLOCKED_BY_ENVIRONMENT for
this benchmark run, not fabricated.

Usage: PYTHONIOENCODING=utf-8 python -m benchmarks.run_performance_benchmark
"""

from __future__ import annotations

import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from app.knowledge.index import LocalEmbedding
from app.knowledge.legal_service import LegalKnowledgeService
from app.knowledge.retrieval_contracts import AgentType, RetrievalRequest
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator
from app.operations.sop_knowledge import OperationsKnowledgeService

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "benchmarks" / "results" / "performance_benchmark_phase5.json"

_QUERIES = ["UBO xac minh", "von luu dong dieu kien", "bao cao tai chinh", "dang ky kinh doanh", "chi luong nhan su"]


def _percentile(values: List[float], pct: float) -> float:
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1))))
    return round(ordered[idx], 3)


def _measure(orchestrator: ControlledRetrievalOrchestrator, agent_type: AgentType, policy_id: str, n_runs: int) -> List[float]:
    timings: List[float] = []
    for i in range(n_runs):
        query = _QUERIES[i % len(_QUERIES)]
        request = RetrievalRequest(
            request_id=f"perf-{i}", trace_id=f"perf-{i}", actor_id="bench", actor_role="RM",
            agent_type=agent_type, task_type="benchmark", raw_query=query, normalized_query=query,
            effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc), retrieval_policy_id=policy_id,
        )
        start = time.perf_counter()
        orchestrator.retrieve(request, top_k=5)
        timings.append((time.perf_counter() - start) * 1000)
    return timings


def run(tmp_dir: Path) -> Dict[str, object]:
    legal = LegalKnowledgeService(index_path=tmp_dir / "perf_legal.sqlite3", provider=LocalEmbedding())
    legal.ensure_index()
    ops = OperationsKnowledgeService(index_path=tmp_dir / "perf_ops.sqlite3", provider=LocalEmbedding())
    ops.ensure_index()

    legal_orchestrator = ControlledRetrievalOrchestrator(legal.index)
    ops_orchestrator = ControlledRetrievalOrchestrator(ops.index)

    cold_legal = _measure(legal_orchestrator, AgentType.LEGAL_POLICY, "retrieval-policy-legal-v1", n_runs=1)
    warm_legal = _measure(legal_orchestrator, AgentType.LEGAL_POLICY, "retrieval-policy-legal-v1", n_runs=30)
    cold_ops = _measure(ops_orchestrator, AgentType.OPERATIONS, "retrieval-policy-operations-v1", n_runs=1)
    warm_ops = _measure(ops_orchestrator, AgentType.OPERATIONS, "retrieval-policy-operations-v1", n_runs=30)

    return {
        "provider": "LocalEmbedding (hash-BoW, in-process, no network) -- see module docstring for why live semantic timing is BLOCKED_BY_ENVIRONMENT here",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "legal_corpus_size": legal.index.count(),
        "operations_corpus_size": ops.index.count(),
        "legal_cold_ms": round(cold_legal[0], 3),
        "legal_warm_p50_ms": _percentile(warm_legal, 50),
        "legal_warm_p95_ms": _percentile(warm_legal, 95),
        "operations_cold_ms": round(cold_ops[0], 3),
        "operations_warm_p50_ms": _percentile(warm_ops, 50),
        "operations_warm_p95_ms": _percentile(warm_ops, 95),
    }


def main() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        results = run(Path(tmp))
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
