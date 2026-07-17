"""Executable security and reliability evaluation suites."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from app.reliability.patterns import CircuitBreaker, CircuitOpenError, ScopedTTLCache, retry_safe
from app.safety.input_guardrails_v2 import screen_input


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SECURITY = ROOT / "data" / "eval" / "v2" / "security_cases.json"
DEFAULT_RELIABILITY = ROOT / "data" / "eval" / "v2" / "reliability_cases.json"


def run_security(path: str | Path = DEFAULT_SECURITY) -> Dict[str, Any]:
    dataset = json.loads(Path(path).read_text(encoding="utf-8"))
    failures = []
    for case in dataset["cases"]:
        result = screen_input(case["text"])
        if case["kind"] == "injection":
            passed = not result.safe and "PROMPT_INJECTION" in result.flags
        elif case["kind"] == "pii_redaction":
            passed = case["text"] not in result.sanitized_text and case["marker"] in result.sanitized_text
            # Compare the actual number rather than the whole source sentence.
            passed = passed or (case["marker"] in result.sanitized_text and not any(ch.isdigit() for ch in result.sanitized_text))
        else:
            passed = result.safe
        if not passed:
            failures.append({"id": case["id"], "kind": case["kind"]})
    return {
        "dataset_id": dataset["dataset_id"],
        "version": dataset["version"],
        "case_count": len(dataset["cases"]),
        "passed_count": len(dataset["cases"]) - len(failures),
        "failures": failures,
        "passed": not failures,
    }


def run_reliability(path: str | Path = DEFAULT_RELIABILITY) -> Dict[str, Any]:
    dataset = json.loads(Path(path).read_text(encoding="utf-8"))
    failures = []
    for case in dataset["cases"]:
        passed = False
        if case["kind"] == "retry_success":
            calls = {"count": 0}
            def operation():
                calls["count"] += 1
                if calls["count"] <= case["failures"]:
                    raise TimeoutError("synthetic")
                return "ok"
            try:
                passed = retry_safe(operation, attempts=case["attempts"], base_delay=0) == "ok"
            except TimeoutError:
                passed = False
        elif case["kind"] == "retry_denied":
            try:
                retry_safe(lambda: "unsafe", attempts=case["attempts"], idempotent=False)
            except ValueError:
                passed = True
        elif case["kind"] == "cache_isolation":
            cache = ScopedTTLCache()
            cache.set(scope=case["writer_scope"], version="v1", key="K", value="secret", ttl_seconds=10)
            passed = cache.get(scope=case["reader_scope"], version="v1", key="K") is None
        elif case["kind"] == "circuit_open":
            breaker = CircuitBreaker(failure_threshold=case["failure_threshold"], recovery_seconds=60)
            for _ in range(case["failure_threshold"]):
                try:
                    breaker.call(lambda: (_ for _ in ()).throw(TimeoutError("down")))
                except TimeoutError:
                    pass
            try:
                breaker.call(lambda: "must not execute")
            except CircuitOpenError:
                passed = True
        if not passed:
            failures.append({"id": case["id"], "kind": case["kind"]})
    return {
        "dataset_id": dataset["dataset_id"],
        "version": dataset["version"],
        "case_count": len(dataset["cases"]),
        "passed_count": len(dataset["cases"]) - len(failures),
        "failures": failures,
        "passed": not failures,
    }


def run_all() -> Dict[str, Any]:
    security = run_security()
    reliability = run_reliability()
    return {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "security": security,
        "reliability": reliability,
        "passed": security["passed"] and reliability["passed"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    report = run_all()
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized, encoding="utf-8")
    print(serialized)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
