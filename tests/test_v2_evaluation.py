"""Evaluation dataset and quality gates are executable in CI."""

from __future__ import annotations

import json

from app.evaluation.runner import DEFAULT_DATASET, run_evaluation


def test_golden_dataset_has_40_versioned_synthetic_cases():
    payload = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    assert payload["synthetic"] is True
    assert len(payload["cases"]) == 40
    assert len({item["id"] for item in payload["cases"]}) == 40


def test_offline_quality_gates(tmp_path):
    report = run_evaluation(index_path=tmp_path / "eval-index.sqlite3")
    assert report["passed"], report["failures"]
    assert report["metrics"]["intent_accuracy"] >= 0.95
    assert report["metrics"]["retrieval_hit_at_3"] >= 0.95
    assert report["metrics"]["eligibility_accuracy"] == 1.0
    assert report["metrics"]["unsafe_approval_rate"] == 0.0
    assert report["metrics"]["relevant_policy_precision"] >= 0.95
    assert report["metrics"]["relevant_policy_recall"] >= 0.95
