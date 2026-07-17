"""Tests for benchmarks/run.py: dataset integrity, end-to-end execution of a
few real cases (no live LLM -- deterministic intent, local RAG provider),
infra-error handling, and output-file generation. Not a re-test of the full
40-case dataset (that is a manual `python -m benchmarks.run` run, see
docs/SINGLE_VS_MULTI_AGENT_BENCHMARK.md); this proves the runner itself is
correct."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from benchmarks import run as bench_run

DATASET_PATH = Path(__file__).resolve().parents[2] / "benchmarks" / "data" / "corporate_sales_cases.json"


@pytest.fixture(scope="module")
def dataset():
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def test_dataset_has_forty_cases_across_six_categories(dataset):
    assert dataset["data_label"] == "SYNTHETIC BENCHMARK DATA"
    assert len(dataset["cases"]) == 40
    categories = {c["category"] for c in dataset["cases"]}
    assert categories == {
        "simple_product_query", "multi_product_bundle", "missing_information",
        "legal_risk_blocking", "out_of_scope", "security_adversarial",
    }


def test_every_case_has_a_unique_id_and_required_fields(dataset):
    ids = [c["case_id"] for c in dataset["cases"]]
    assert len(ids) == len(set(ids)), "duplicate case_id"
    for case in dataset["cases"]:
        assert case["input"].get("text")
        assert "expected" in case


def test_security_case_is_blocked_at_input_not_run_through_engine(dataset):
    case = next(c for c in dataset["cases"] if c["category"] == "security_adversarial")
    result = asyncio.run(
        bench_run._run_case_mode(case, "natural", index_path=Path("unused"), legal_index_path=Path("unused"), live_intent=False)
    )
    assert result.status == "blocked_at_input"
    assert result.abstained is True


def test_non_security_case_runs_end_to_end_with_deterministic_intent(tmp_path):
    case = {
        "case_id": "BENCH-TEST-001", "category": "multi_product_bundle",
        "input": {
            "text": "Doanh nghiep can chi luong cho nhan vien.",
            "customer_attributes": {"employees_count": 50},
            "documents": [{"document_type": "business_registration", "status": "verified"}],
        },
        "expected": {"route": "complex", "required_product_ids": ["PROD-PAYROLL"]},
    }
    result = asyncio.run(
        bench_run._run_case_mode(
            case, "multi_agent", index_path=tmp_path / "products.sqlite3",
            legal_index_path=tmp_path / "legal.sqlite3", live_intent=False,
        )
    )
    assert result.status == "ok"
    assert "PROD-PAYROLL" in result.product_ids
    assert result.final_status in {"pending_approval", "pending_information", "pending_review"}


def test_infra_error_is_recorded_not_silently_treated_as_zero_recall(tmp_path, monkeypatch):
    """A provider-level failure must show up as status="infra_error", not as
    a quality failure indistinguishable from "the RAG genuinely found
    nothing relevant" -- otherwise an outage would masquerade as a bad
    retrieval score instead of an infrastructure problem."""
    case = {
        "case_id": "BENCH-TEST-002", "category": "multi_product_bundle",
        "input": {"text": "Doanh nghiep can chi luong.", "customer_attributes": {}, "documents": []},
        "expected": {"route": "complex", "required_product_ids": ["PROD-PAYROLL"]},
    }

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated provider outage")

    monkeypatch.setattr(bench_run, "_build_state", _boom)
    result = asyncio.run(
        bench_run._run_case_mode(
            case, "multi_agent", index_path=tmp_path / "products.sqlite3",
            legal_index_path=tmp_path / "legal.sqlite3", live_intent=False,
        )
    )
    assert result.status == "infra_error"
    assert result.error_type == "RuntimeError"


def test_score_case_marks_infra_error_distinctly_from_a_quality_miss():
    case = {"case_id": "X", "category": "multi_product_bundle", "expected": {"route": "complex", "required_product_ids": ["PROD-PAYROLL"]}}
    infra_error_result = bench_run.CaseRunResult("X", "multi_product_bundle", "multi_agent", status="infra_error", latency_ms=1.0, error_type="TimeoutError")
    natural_result = bench_run.CaseRunResult("X", "multi_product_bundle", "natural", status="ok", latency_ms=1.0, actual_route="complex")
    scored = bench_run._score_case(case, {"natural": natural_result, "multi_agent": infra_error_result})
    assert scored["multi_agent"] == {"infra_error": "TimeoutError"}


def test_write_outputs_creates_all_three_files(tmp_path, dataset):
    small_dataset = {**dataset, "cases": dataset["cases"][:1]}
    fake_result = bench_run.CaseRunResult(
        small_dataset["cases"][0]["case_id"], small_dataset["cases"][0]["category"], "natural",
        status="ok", latency_ms=1.0, actual_route="simple",
    )
    report = bench_run.build_report(small_dataset, [fake_result], cache_mode="warm", case_filter=None)
    bench_run.write_outputs(tmp_path, small_dataset, [fake_result], report)
    assert (tmp_path / "results.jsonl").exists()
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "report.md").exists()
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["summary"]["data_label"] == "SYNTHETIC BENCHMARK DATA"


def test_cost_is_never_fabricated():
    rows = [{"single_agent_rag": {"product_recall": 1.0, "product_precision": 1.0, "missing_info_recall": None,
             "legal_flag_recall": None, "citation_coverage": None, "citation_validity": None,
             "unsupported_claim_rate": None, "abstention_correct": True, "forbidden_violation": False,
             "latency_ms": 1.0}}]
    summary = bench_run._summarize("single_agent_rag", rows)
    assert summary["cost"] is None
    assert summary["token_usage"] is None
    assert summary["cost_status"] == "NOT_CALCULATED"
