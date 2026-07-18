"""Unit tests for benchmarks/metrics.py -- pure functions, no live run."""

from __future__ import annotations

from benchmarks import metrics as m


def test_product_recall_full_and_partial_and_no_ground_truth():
    assert m.product_recall(["A", "B"], ["A", "B", "C"]) == 1.0
    assert m.product_recall(["A", "B"], ["A"]) == 0.5
    assert m.product_recall([], ["A"]) is None  # no ground truth -> not applicable, not 0


def test_product_precision_ignores_empty_actual():
    assert m.product_precision([], ["A"], []) is None
    assert m.product_precision(["A", "X"], ["A"], ["B"]) == 0.5
    assert m.product_precision(["A"], ["A"], []) == 1.0


def test_forbidden_product_violation():
    assert m.forbidden_product_violation(["A", "B"], ["B"]) is True
    assert m.forbidden_product_violation(["A"], ["B"]) is False


def test_missing_information_recall_zero_division_guarded():
    assert m.missing_information_recall([], []) is None
    assert m.missing_information_recall(["x"], []) == 0.0
    assert m.missing_information_recall(["x", "y"], ["x"]) == 0.5


def test_citation_coverage_and_validity():
    evidences = [
        {"source_document_id": "D1", "quote": "q1", "is_valid": True},
        {"source_document_id": "D2", "quote": "q2", "is_valid": False},
        {"source_document_id": None, "quote": "", "is_valid": False},
    ]
    assert m.citation_coverage(evidences) == 2 / 3
    assert m.citation_validity(evidences) == 1 / 3
    assert m.unsupported_claim_rate(evidences) == round(1 - 1 / 3, 6)


def test_citation_metrics_none_when_no_evidence():
    assert m.citation_coverage([]) is None
    assert m.citation_validity([]) is None
    assert m.unsupported_claim_rate([]) is None


def test_routing_correct_skips_blocked_at_input():
    assert m.routing_correct("simple", "simple") is True
    assert m.routing_correct("simple", "complex") is False
    assert m.routing_correct("blocked_at_input", "complex") is None


def test_abstention_correct():
    assert m.abstention_correct(True, True) is True
    assert m.abstention_correct(True, False) is False
    assert m.abstention_correct(False, False) is True


def test_aggregate_optional_floats_ignores_none():
    assert m.aggregate_optional_floats([1.0, None, 0.5]) == 0.75
    assert m.aggregate_optional_floats([None, None]) is None


def test_aggregate_bools_ignores_none():
    assert m.aggregate_bools([True, False, None, True]) == round(2 / 3, 4)
    assert m.aggregate_bools([None]) is None
