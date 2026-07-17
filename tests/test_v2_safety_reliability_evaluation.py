"""Security/reliability datasets and quality gates."""

from __future__ import annotations

import json

from app.evaluation.safety_reliability_runner import (
    DEFAULT_RELIABILITY,
    DEFAULT_SECURITY,
    run_all,
)


def test_security_and_reliability_dataset_sizes_are_versioned():
    security = json.loads(DEFAULT_SECURITY.read_text(encoding="utf-8"))
    reliability = json.loads(DEFAULT_RELIABILITY.read_text(encoding="utf-8"))
    assert security["synthetic"] is True and len(security["cases"]) == 25
    assert reliability["synthetic"] is True and len(reliability["cases"]) == 20
    assert len({case["id"] for case in security["cases"]}) == 25
    assert len({case["id"] for case in reliability["cases"]}) == 20


def test_security_and_reliability_quality_gates():
    report = run_all()
    assert report["passed"], report
    assert report["security"]["passed_count"] == 25
    assert report["reliability"]["passed_count"] == 20
