"""Pure metric calculators for the single-agent vs multi-agent benchmark.

Every function here takes plain data (lists/sets/dicts) and returns a
number or bool -- no I/O, no model calls, so these are independently unit
tested (tests/unit/test_v2_benchmark_metrics.py) without needing a live run.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence


def _safe_ratio(numerator: float, denominator: float) -> Optional[float]:
    """None (not 0.0) when the denominator is 0 -- "no ground truth items to
    recall" is a different situation from "recalled zero of many", and
    averaging must not silently treat them the same (see aggregate())."""
    if denominator == 0:
        return None
    return numerator / denominator


def product_recall(required: Sequence[str], actual: Sequence[str]) -> Optional[float]:
    if not required:
        return None
    hit = len(set(required) & set(actual))
    return _safe_ratio(hit, len(set(required)))


def product_precision(actual: Sequence[str], required: Sequence[str], acceptable: Sequence[str]) -> Optional[float]:
    if not actual:
        return None
    relevant = set(required) | set(acceptable)
    hit = len(set(actual) & relevant)
    return _safe_ratio(hit, len(set(actual)))


def forbidden_product_violation(actual: Sequence[str], forbidden: Sequence[str]) -> bool:
    return bool(set(actual) & set(forbidden))


def missing_information_recall(required: Sequence[str], actual: Sequence[str]) -> Optional[float]:
    if not required:
        return None
    hit = len(set(required) & set(actual))
    return _safe_ratio(hit, len(set(required)))


def legal_flag_recall(required: Sequence[str], actual: Sequence[str]) -> Optional[float]:
    if not required:
        return None
    hit = len(set(required) & set(actual))
    return _safe_ratio(hit, len(set(required)))


def citation_coverage(evidences: Iterable[Dict[str, Any]]) -> Optional[float]:
    items = list(evidences)
    if not items:
        return None
    covered = sum(1 for item in items if item.get("source_document_id") and item.get("quote"))
    return _safe_ratio(covered, len(items))


def citation_validity(evidences: Iterable[Dict[str, Any]]) -> Optional[float]:
    """Fraction of evidences the real EvidenceValidator (wired into
    V2WorkflowEngine, not a benchmark-only check) marked is_valid=True."""
    items = list(evidences)
    if not items:
        return None
    valid = sum(1 for item in items if item.get("is_valid") is True)
    return _safe_ratio(valid, len(items))


def unsupported_claim_rate(evidences: Iterable[Dict[str, Any]]) -> Optional[float]:
    coverage = citation_validity(evidences)
    if coverage is None:
        return None
    return round(1.0 - coverage, 6)


def routing_correct(expected_route: str, actual_route: str) -> Optional[bool]:
    if expected_route in {"blocked_at_input"}:
        return None  # routing never applies -- the input never reaches the router
    return expected_route == actual_route


def abstention_correct(must_abstain: Optional[bool], actually_abstained: bool) -> Optional[bool]:
    """None when the case's ground truth doesn't take a position on whether
    a product should be recommended (e.g. a pure "what's my case status"
    query) -- comparing against a default of False there would penalize the
    system for correctly recommending nothing when nothing was ever asked
    for."""
    if must_abstain is None:
        return None
    return must_abstain == actually_abstained


def aggregate_optional_floats(values: List[Optional[float]]) -> Optional[float]:
    """Average, ignoring None entries (cases with no applicable ground truth
    for this metric). None if every value was None."""
    present = [v for v in values if v is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 4)


def aggregate_bools(values: List[Optional[bool]]) -> Optional[float]:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return round(sum(1 for v in present if v) / len(present), 4)
