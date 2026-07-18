"""Reproducible deterministic evaluation for intent, retrieval and eligibility."""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from app.eligibility.engine import EligibilityEngine
from app.intent.fallback import DeterministicIntentExtractor
from app.knowledge.service import ProductKnowledgeService


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "data" / "eval" / "v2" / "golden_cases.json"


def run_evaluation(
    dataset_path: str | Path = DEFAULT_DATASET,
    *,
    index_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    dataset = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if index_path is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="rag-v2-eval-")
        index_path = Path(temp_dir.name) / "index.sqlite3"
    else:
        temp_dir = None
    knowledge = ProductKnowledgeService(index_path)
    knowledge.ingest()
    intent_extractor = DeterministicIntentExtractor()
    eligibility = EligibilityEngine()
    counters = {
        "intent_total": 0, "intent_correct": 0, "intent_product_correct": 0, "intent_product_total": 0,
        "retrieval_total": 0, "retrieval_correct": 0, "oos_total": 0, "oos_correct": 0,
        "eligibility_total": 0, "eligibility_correct": 0, "unsafe_pass": 0,
        "policy_true_positive": 0, "policy_false_positive": 0, "policy_false_negative": 0,
    }
    failures = []
    for case in dataset["cases"]:
        kind = case["kind"]
        if kind == "intent":
            counters["intent_total"] += 1
            result = intent_extractor.extract(case["input"], case["id"])
            ok = result.primary_intent == case["expected_intent"]
            counters["intent_correct"] += int(ok)
            if "expected_product" in case:
                counters["intent_product_total"] += 1
                products = result.entities.get("product_ids", [])
                product_ok = case["expected_product"] in products
                counters["intent_product_correct"] += int(product_ok)
                ok = ok and product_ok
            if not ok:
                failures.append({"id": case["id"], "expected": case.get("expected_intent"), "actual": result.primary_intent})
        elif kind == "retrieval":
            counters["retrieval_total"] += 1
            hits = knowledge.search(
                case["input"],
                branch=case["branch"],
                product_ids=case.get("product_ids"),
                top_k=3,
            )
            actual = [item.chunk.product_id for item in hits]
            expected = case["expected_product"]
            if expected is None:
                counters["oos_total"] += 1
                ok = not actual
                counters["oos_correct"] += int(ok)
            else:
                ok = expected in actual
            counters["retrieval_correct"] += int(ok)
            if not ok:
                failures.append({"id": case["id"], "expected": expected, "actual": actual})
        elif kind == "eligibility":
            counters["eligibility_total"] += 1
            result = eligibility.evaluate([case["product"]], customer=case["customer"], documents=case["documents"])
            actual = result["products"][0]["status"]
            expected = case["expected_status"]
            ok = actual == expected
            counters["eligibility_correct"] += int(ok)
            if expected != "passed" and actual == "passed":
                counters["unsafe_pass"] += 1
            expected_policy = {
                "PROD-PAYROLL": "SYN-B2B-PAYROLL-001",
                "PROD-CASH-MGMT": "SYN-B2B-CASH-001",
                "PROD-BULK-PAYMENT": "SYN-B2B-BULK-001",
                "PROD-WORKING-CAPITAL": "SYN-B2B-CREDIT-001",
            }[case["product"]]
            expected_policies = {"SYN-B2B-KYC-001", expected_policy}
            actual_policies = {item["policy_id"] for item in result["products"][0]["related_policies"]}
            counters["policy_true_positive"] += len(expected_policies & actual_policies)
            counters["policy_false_positive"] += len(actual_policies - expected_policies)
            counters["policy_false_negative"] += len(expected_policies - actual_policies)
            if not ok:
                failures.append({"id": case["id"], "expected": expected, "actual": actual})
    def rate(correct: int, total: int) -> float:
        return round(correct / total, 4) if total else 1.0
    report = {
        "dataset_id": dataset["dataset_id"],
        "dataset_version": dataset["version"],
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(dataset["cases"]),
        "metrics": {
            "intent_accuracy": rate(counters["intent_correct"], counters["intent_total"]),
            "intent_product_accuracy": rate(counters["intent_product_correct"], counters["intent_product_total"]),
            "retrieval_hit_at_3": rate(counters["retrieval_correct"], counters["retrieval_total"]),
            "oos_precision": rate(counters["oos_correct"], counters["oos_total"]),
            "eligibility_accuracy": rate(counters["eligibility_correct"], counters["eligibility_total"]),
            "unsafe_approval_rate": rate(counters["unsafe_pass"], counters["eligibility_total"]),
            "relevant_policy_precision": rate(counters["policy_true_positive"], counters["policy_true_positive"] + counters["policy_false_positive"]),
            "relevant_policy_recall": rate(counters["policy_true_positive"], counters["policy_true_positive"] + counters["policy_false_negative"]),
        },
        "counters": counters,
        "failures": failures,
        "passed": not failures and counters["unsafe_pass"] == 0,
    }
    if temp_dir is not None:
        temp_dir.cleanup()
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output")
    args = parser.parse_args()
    report = run_evaluation(args.dataset)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized, encoding="utf-8")
    print(serialized)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
