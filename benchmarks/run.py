"""Single-agent (simple) vs multi-agent (complex) benchmark runner.

Runs every case in benchmarks/data/corporate_sales_cases.json through
V2WorkflowEngine THREE times each: once with normal (unforced) routing (to
measure routing accuracy against the dataset's expected route), once forced
onto the "simple"/single_agent_rag path, and once forced onto the
"complex"/multi_agent path (see app/workflow/engine.py's force_route param,
added specifically for this benchmark and defaulting to None/no-op in
production). Group F (security/adversarial) cases are validated against
app.safety.input_guardrails_v2.screen_input directly instead -- that is the
actual enforcement point in the live API (app/api/v2/router.py), and these
inputs are expected to never reach the workflow engine at all.

No result in this file is fabricated: every number comes from actually
running the real ProductService/EligibilityEngine/OperationsService/
RiskGuardrailGate pipeline against synthetic input. Where a real dependency
(e.g. an embedding provider) is genuinely unavailable, the case is recorded
as an infrastructure error, never silently folded into a "0% relevant"
quality score.

Usage:
    python -m benchmarks.run --cache-mode warm
    python -m benchmarks.run --cache-mode cold --cases BENCH-B01,BENCH-B06,BENCH-D01
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import config as app_config  # noqa: E402
from app.eligibility.engine import EligibilityEngine  # noqa: E402
from app.knowledge.legal_service import LegalKnowledgeService  # noqa: E402
from app.knowledge.service import ProductKnowledgeService  # noqa: E402
from app.operations.service import OperationsService  # noqa: E402
from app.product.service import ProductService  # noqa: E402
from app.safety.input_guardrails_v2 import screen_input  # noqa: E402
from app.schemas.v2.context_snapshot import ContextSnapshot, WorkspaceDocument  # noqa: E402
from app.schemas.v2 import examples as ex  # noqa: E402
from app.schemas.v2.shared_case_state import (  # noqa: E402
    Approval, ApprovalStatus, CaseStatus, Request, SharedCaseState, Workflow,
)
from app.workflow.engine import V2WorkflowEngine  # noqa: E402
from app.workflow.planner import PlannerService  # noqa: E402
from app.workflow.next_best import NextBestService  # noqa: E402
from app.workflow.risk_gate import RiskGuardrailGate  # noqa: E402
from app.workflow.router import ComplexityRouter  # noqa: E402
from app.intent.extractor import IntentExtractor  # noqa: E402

from benchmarks import metrics as m  # noqa: E402

DEFAULT_DATASET = ROOT / "benchmarks" / "data" / "corporate_sales_cases.json"
DEFAULT_OUTPUT_DIR = ROOT / "benchmarks" / "results" / "latest"

MODES = ("natural", "single_agent_rag", "multi_agent")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_state() -> Dict[str, Any]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        commit = None
    try:
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
    except Exception:
        dirty = None
    return {"git_commit": commit, "working_tree_dirty": dirty}


def _build_state(case: Dict[str, Any]) -> SharedCaseState:
    context = ContextSnapshot.model_validate(ex.MINIMAL_CONTEXT_SNAPSHOT)
    # A real RM always has a branch (SQLiteIAMAdapter always returns one);
    # MINIMAL_CONTEXT_SNAPSHOT's access_scope={} defaults to branch="*" in
    # V2WorkflowEngine, which the knowledge ACL filter treats as "no
    # specific branch" -- NOT as wildcard/see-everything. Branch-restricted
    # products (PROD-WORKING-CAPITAL: access_scope.branches=["HN01","HCM01"])
    # are then invisible to every case, which is not representative of a
    # real RM session and was confirmed live (product_recall=0.0 on every
    # working-capital case) before this fix.
    context = context.model_copy(
        update={"employee": context.employee.model_copy(update={"access_scope": {"branch": "HN01"}})}
    )
    input_spec = case["input"]
    attributes = dict(input_spec.get("customer_attributes") or {})
    documents = [
        WorkspaceDocument(
            document_id=f"DOC-{uuid.uuid4().hex[:8].upper()}",
            document_type=doc["document_type"],
            version="1",
            status=doc.get("status", "verified"),
            access_scope={"branches": ["*"]},
        )
        for doc in (input_spec.get("documents") or [])
    ]
    context = context.model_copy(
        update={
            "customer": context.customer.model_copy(
                update={"customer_id": f"BENCH-{case['case_id']}", "attributes": attributes, "stale": False}
            ),
            "documents": documents,
        }
    )
    now = datetime.now(timezone.utc)
    return SharedCaseState(
        case_id=f"CASE-{case['case_id']}",
        trace_id=f"TRACE-{uuid.uuid4().hex.upper()}",
        status=CaseStatus.NEW,
        context=context,
        request=Request(message_id=f"MSG-{uuid.uuid4().hex[:12].upper()}", text=input_spec["text"], received_at=now),
        workflow=Workflow(workflow_version="benchmark", current_node=None, tasks=[], loop_count=0),
        evidences=[],
        approval=Approval(status=ApprovalStatus.NOT_REQUIRED),
        audit_events=[],
        created_at=now,
        updated_at=now,
    )


@dataclass
class CaseRunResult:
    case_id: str
    category: str
    mode: str
    status: str  # "ok" | "infra_error" | "blocked_at_input" | "not_applicable"
    latency_ms: float
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    actual_route: Optional[str] = None
    final_status: Optional[str] = None
    product_ids: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    legal_flags: List[str] = field(default_factory=list)
    evidences: List[Dict[str, Any]] = field(default_factory=list)
    action_readiness: Optional[str] = None
    abstained: bool = False


def _blocking_rule_ids(eligibility_result: Optional[Dict[str, Any]]) -> List[str]:
    ids: List[str] = []
    for product in (eligibility_result or {}).get("products", []):
        for rule in product.get("rules", []):
            if rule.get("status") in {"failed", "pending_review"}:
                ids.append(rule.get("failure_code") or rule.get("rule_id"))
    return ids


async def _run_case_mode(
    case: Dict[str, Any], mode: str, *, index_path: Path, legal_index_path: Path, live_intent: bool
) -> CaseRunResult:
    category = case["category"]
    if category == "security_adversarial":
        if mode != "natural":
            return CaseRunResult(case["case_id"], category, mode, status="not_applicable", latency_ms=0.0)
        started = time.perf_counter()
        result = screen_input(case["input"]["text"])
        latency = round((time.perf_counter() - started) * 1000, 3)
        return CaseRunResult(
            case["case_id"], category, "natural", status="blocked_at_input" if not result.safe else "ok",
            latency_ms=latency, actual_route="blocked_at_input" if not result.safe else "reached_engine",
            abstained=not result.safe,
        )

    started = time.perf_counter()
    try:
        # State/engine construction is inside the try too: a malformed case
        # or a provider that fails at construction time (not just at
        # .run()) must still be recorded as this case's infra_error and let
        # the rest of the benchmark continue, not crash the whole run.
        engine = V2WorkflowEngine(
            intent=IntentExtractor(prefer_llm=live_intent),
            product=ProductService(ProductKnowledgeService(index_path)),
            eligibility=EligibilityEngine(),
            operations=OperationsService(),
            planner=PlannerService(),
            next_best=NextBestService(),
            router=ComplexityRouter(),
            risk_gate=RiskGuardrailGate(),
            legal_knowledge=LegalKnowledgeService(legal_index_path),
        )
        state = _build_state(case)
        force = {"single_agent_rag": "simple", "multi_agent": "complex"}.get(mode)
        state = await engine.run(state, force_route=force)
    except Exception as exc:  # noqa: BLE001 -- benchmark must record, not crash, on infra failures
        latency = round((time.perf_counter() - started) * 1000, 3)
        return CaseRunResult(
            case["case_id"], category, mode, status="infra_error", latency_ms=latency,
            error_type=type(exc).__name__, error_message=str(exc)[:500],
        )
    latency = round((time.perf_counter() - started) * 1000, 3)

    actual_route = "simple" if (state.execution_plan or {}).get("plan_version") == 1 and not state.workflow.tasks else "complex"
    product_ids = [item.get("product_id") for item in (state.product_result or {}).get("recommendations", [])]
    # Abstention means "recommended nothing" -- checked directly, not via
    # case status: the simple/single-agent path always ends CaseStatus.
    # COMPLETED whether or not it found a product (it never reaches
    # PENDING_REVIEW, unlike the complex path's no_grounded_product branch),
    # so a status-based check silently always reported single_agent_rag as
    # "never abstains" regardless of what it actually recommended.
    abstained = not product_ids and category != "legal_risk_blocking"
    return CaseRunResult(
        case["case_id"], category, mode, status="ok", latency_ms=latency,
        actual_route=actual_route, final_status=state.status.value,
        product_ids=[pid for pid in product_ids if pid],
        missing_information=list((state.next_best_questions or []) and [q.get("target_field") for q in state.next_best_questions] or []),
        legal_flags=_blocking_rule_ids(state.eligibility_result),
        evidences=[e.model_dump(mode="json") for e in state.evidences],
        action_readiness=(state.operations_result or {}).get("action_readiness"),
        abstained=abstained,
    )


async def run_all(
    dataset: Dict[str, Any], *, cache_mode: str, case_filter: Optional[set], live_intent: bool = False
) -> List[CaseRunResult]:
    cases = [c for c in dataset["cases"] if case_filter is None or c["case_id"] in case_filter]

    if cache_mode == "cold":
        tmp_dir = Path(tempfile.mkdtemp(prefix="rag-bench-cold-"))
        original_vector_dir = app_config.settings.VECTOR_DB_DIR
        app_config.settings.VECTOR_DB_DIR = str(tmp_dir)
        index_path = tmp_dir / "products.sqlite3"
        legal_index_path = tmp_dir / "legal.sqlite3"
    else:
        original_vector_dir = None
        index_path = ROOT / "data" / "vector_db" / "v2_products.sqlite3"
        legal_index_path = ROOT / "data" / "vector_db" / "v2_legal.sqlite3"

    try:
        results: List[CaseRunResult] = []
        for case in cases:
            for mode in MODES:
                results.append(
                    await _run_case_mode(
                        case, mode, index_path=index_path, legal_index_path=legal_index_path, live_intent=live_intent
                    )
                )
        return results
    finally:
        if original_vector_dir is not None:
            app_config.settings.VECTOR_DB_DIR = original_vector_dir
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _expected(case: Dict[str, Any]) -> Dict[str, Any]:
    return case.get("expected", {})


def _score_case(case: Dict[str, Any], results_by_mode: Dict[str, CaseRunResult]) -> Dict[str, Any]:
    expected = _expected(case)
    natural = results_by_mode.get("natural")
    scored: Dict[str, Any] = {"case_id": case["case_id"], "category": case["category"]}

    if case["category"] == "security_adversarial":
        scored["abstention_correct"] = m.abstention_correct(expected.get("must_abstain"), bool(natural and natural.abstained))
        scored["routing_correct"] = None
        return scored

    scored["routing_correct"] = m.routing_correct(expected.get("route", "complex"), natural.actual_route if natural else "")

    for mode_key, result_key in (("single_agent_rag", "single_agent_rag"), ("multi_agent", "multi_agent")):
        r = results_by_mode.get(mode_key)
        if r is None or r.status != "ok":
            scored[result_key] = {"infra_error": r.error_type if r else "missing_result"}
            continue
        scored[result_key] = {
            "product_recall": m.product_recall(expected.get("required_product_ids", []), r.product_ids),
            "product_precision": m.product_precision(r.product_ids, expected.get("required_product_ids", []), expected.get("acceptable_product_ids", [])),
            "forbidden_violation": m.forbidden_product_violation(r.product_ids, expected.get("forbidden_product_ids", [])),
            "missing_info_recall": m.missing_information_recall(expected.get("required_missing_information", []), r.missing_information),
            "legal_flag_recall": m.legal_flag_recall(expected.get("required_legal_flags", []), r.legal_flags),
            "citation_coverage": m.citation_coverage(r.evidences),
            "citation_validity": m.citation_validity(r.evidences),
            "unsupported_claim_rate": m.unsupported_claim_rate(r.evidences),
            "abstention_correct": m.abstention_correct(expected.get("must_abstain"), r.abstained),
            "final_status_matches_expected": (
                None if "expected_case_status" not in expected else r.final_status == expected["expected_case_status"]
            ),
            "latency_ms": r.latency_ms,
        }
    return scored


def _summarize(mode_key: str, per_case_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = [row[mode_key] for row in per_case_scores if isinstance(row.get(mode_key), dict) and "infra_error" not in row[mode_key]]
    infra_errors = sum(1 for row in per_case_scores if isinstance(row.get(mode_key), dict) and "infra_error" in row[mode_key])
    return {
        "cases_evaluated": len(rows),
        "infra_errors": infra_errors,
        "product_recall": m.aggregate_optional_floats([r["product_recall"] for r in rows]),
        "product_precision": m.aggregate_optional_floats([r["product_precision"] for r in rows]),
        "missing_info_recall": m.aggregate_optional_floats([r["missing_info_recall"] for r in rows]),
        "legal_flag_recall": m.aggregate_optional_floats([r["legal_flag_recall"] for r in rows]),
        "citation_coverage": m.aggregate_optional_floats([r["citation_coverage"] for r in rows]),
        "citation_validity": m.aggregate_optional_floats([r["citation_validity"] for r in rows]),
        "unsupported_claim_rate": m.aggregate_optional_floats([r["unsupported_claim_rate"] for r in rows]),
        "abstention_accuracy": m.aggregate_bools([r["abstention_correct"] for r in rows]),
        "forbidden_violation_rate": m.aggregate_bools([r["forbidden_violation"] for r in rows]),
        "avg_latency_ms": m.aggregate_optional_floats([r["latency_ms"] for r in rows]),
        "token_usage": None,
        "cost": None,
        "cost_status": "NOT_CALCULATED",
    }


def build_report(
    dataset: Dict[str, Any], results: List[CaseRunResult], *, cache_mode: str, case_filter: Optional[set],
    live_intent: bool = False,
) -> Dict[str, Any]:
    by_case: Dict[str, Dict[str, CaseRunResult]] = {}
    for r in results:
        by_case.setdefault(r.case_id, {})[r.mode] = r
    cases = [c for c in dataset["cases"] if case_filter is None or c["case_id"] in case_filter]
    per_case_scores = [_score_case(case, by_case.get(case["case_id"], {})) for case in cases]

    routing_rows = [row["routing_correct"] for row in per_case_scores if row["routing_correct"] is not None]
    routing_accuracy = m.aggregate_bools(routing_rows)

    summary = {
        "dataset_id": dataset["dataset_id"],
        "dataset_version": dataset["dataset_version"],
        "data_label": dataset["data_label"],
        "run_timestamp": _now_iso(),
        "cache_mode": cache_mode,
        "case_count": len(cases),
        **_git_state(),
        "configuration": {
            "rag_provider": app_config.settings.RAG_PROVIDER,
            "knowledge_embedding_provider_env": "see .env KNOWLEDGE_EMBEDDING_PROVIDER",
            "intent_mode": "llm" if live_intent else "deterministic",
        },
        "routing_accuracy": routing_accuracy,
        "single_agent_rag": _summarize("single_agent_rag", per_case_scores),
        "multi_agent": _summarize("multi_agent", per_case_scores),
    }
    summary["comparison"] = {
        key: (
            None
            if summary["single_agent_rag"][key] is None or summary["multi_agent"][key] is None
            else round(summary["multi_agent"][key] - summary["single_agent_rag"][key], 4)
        )
        for key in ("product_recall", "missing_info_recall", "legal_flag_recall", "citation_validity", "avg_latency_ms")
    }
    return {"summary": summary, "per_case": per_case_scores}


def write_outputs(output_dir: Path, dataset: Dict[str, Any], results: List[CaseRunResult], report: Dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "results.jsonl").open("w", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(asdict(r), ensure_ascii=False, default=str) + "\n")
    (output_dir / "summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    (output_dir / "report.md").write_text(_render_markdown(dataset, report), encoding="utf-8")


def _render_markdown(dataset: Dict[str, Any], report: Dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# Single-Agent vs Multi-Agent Benchmark Report",
        "",
        "**SYNTHETIC BENCHMARK DATA** -- no real SHB customer or transaction data.",
        "",
        f"- Dataset: `{s['dataset_id']}` v`{s['dataset_version']}`, {s['case_count']} cases",
        f"- Run at: {s['run_timestamp']}",
        f"- Cache mode: `{s['cache_mode']}`",
        f"- git_commit: `{s.get('git_commit')}`, working_tree_dirty: `{s.get('working_tree_dirty')}`",
        f"- RAG_PROVIDER: `{s['configuration']['rag_provider']}`, intent mode: `{s['configuration']['intent_mode']}`",
        "",
        f"## Routing accuracy: {s['routing_accuracy']}",
        "",
        "## Metrics: single_agent_rag vs multi_agent",
        "",
        "| Metric | single_agent_rag | multi_agent | Δ (multi - single) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for key in ("cases_evaluated", "infra_errors", "product_recall", "product_precision", "missing_info_recall",
                "legal_flag_recall", "citation_coverage", "citation_validity", "unsupported_claim_rate",
                "abstention_accuracy", "forbidden_violation_rate", "avg_latency_ms"):
        single = s["single_agent_rag"].get(key)
        multi = s["multi_agent"].get(key)
        delta = s["comparison"].get(key, "")
        lines.append(f"| {key} | {single} | {multi} | {delta if delta != '' else '-'} |")
    lines += ["", "## Per-category breakdown", ""]
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for row in report["per_case"]:
        by_cat.setdefault(row["category"], []).append(row)
    for cat, rows in by_cat.items():
        lines.append(f"### {cat} ({len(rows)} cases)")
        for row in rows:
            single_status = row.get("single_agent_rag", {})
            multi_status = row.get("multi_agent", {})
            lines.append(f"- `{row['case_id']}`: routing_correct={row['routing_correct']}, "
                         f"single_agent_rag={_short(single_status)}, multi_agent={_short(multi_status)}")
        lines.append("")
    lines += [
        "## Cost and token usage",
        "",
        f"cost_status: `{s['single_agent_rag']['cost_status']}` -- {app_config.settings.RAG_PROVIDER!r} local retrieval and the "
        "deterministic eligibility engine do not call a metered LLM in this benchmark run; token_usage/cost are "
        "reported as `null`/`NOT_CALCULATED` rather than estimated.",
        "",
    ]
    return "\n".join(lines)


def _short(d: Dict[str, Any]) -> str:
    if "infra_error" in d:
        return f"INFRA_ERROR({d['infra_error']})"
    return f"recall={d.get('product_recall')},status_ok={d.get('final_status_matches_expected')}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--cache-mode", choices=["cold", "warm"], default="warm")
    parser.add_argument("--cases", default=None, help="Comma-separated case_ids to run (default: all)")
    parser.add_argument(
        "--live-intent", action="store_true",
        help="Use the real OpenAI-backed IntentExtractor instead of the deterministic fallback. "
             "Costs real API calls/tokens; not run by default (see docs/SINGLE_VS_MULTI_AGENT_BENCHMARK.md).",
    )
    args = parser.parse_args()

    if args.live_intent and not app_config.settings.OPENAI_API_KEY:
        print("LIVE BENCHMARK NOT RUN — CREDENTIALS UNAVAILABLE", file=sys.stderr)
        raise SystemExit(2)

    dataset = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    case_filter = set(args.cases.split(",")) if args.cases else None

    results = asyncio.run(
        run_all(dataset, cache_mode=args.cache_mode, case_filter=case_filter, live_intent=args.live_intent)
    )
    report = build_report(
        dataset, results, cache_mode=args.cache_mode, case_filter=case_filter, live_intent=args.live_intent
    )
    write_outputs(Path(args.output_dir), dataset, results, report)

    print(json.dumps(report["summary"], ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
