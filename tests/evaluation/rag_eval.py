"""RAG Evaluation Runner - computes Hit@K, MRR, citation correctness."""

import json
from pathlib import Path
from typing import List, Dict, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from servers.product_agent.rag.retriever import ProductRetriever


def load_cases(path: Path) -> List[Dict[str, Any]]:
    cases = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def hit_at_k(retrieved: List[str], expected: List[str], k: int) -> float:
    if not expected:
        return 1.0 if not retrieved else 0.0
    top_k = retrieved[:k]
    hits = sum(1 for eid in expected if eid in top_k)
    return hits / len(expected)


def mrr_at_k(retrieved: List[str], expected: List[str], k: int) -> float:
    if not expected:
        return 1.0 if not retrieved else 0.0
    for i, rid in enumerate(retrieved[:k], 1):
        if rid in expected:
            return 1.0 / i
    return 0.0


def citation_correctness(retrieved: List[Dict], expected_ids: List[str]) -> float:
    if not expected_ids:
        return 1.0
    retrieved_ids = [r.get("product_id") for r in retrieved if r.get("product_id")]
    matches = sum(1 for eid in expected_ids if eid in retrieved_ids)
    return matches / len(expected_ids)


def run_evaluation():
    cases = load_cases(Path(__file__).parent / "data/eval/v2/product_rag_cases.jsonl")
    retriever = ProductRetriever()

    k_values = [1, 3, 5]
    metrics = {k: {"hit": [], "mrr": []} for k in k_values}
    citation_scores = []
    oos_precision = []
    oos_recall = []

    for case in cases:
        query = case["query"]
        expected = case["expected_products"]
        expected_oos = case["expected_oos"]

        results = retriever.search(query, top_k=5)
        retrieved_ids = [r.product_id for r in results]
        citations = [r.citation() for r in results]

        for k in k_values:
            metrics[k]["hit"].append(hit_at_k(retrieved_ids, expected, k))
            metrics[k]["mrr"].append(mrr_at_k(retrieved_ids, expected, k))

        citation_scores.append(citation_correctness(citations, expected))

        is_oos = len(results) == 0
        if expected_oos:
            oos_recall.append(1.0 if is_oos else 0.0)
            oos_precision.append(1.0 if is_oos else 0.0)
        else:
            oos_precision.append(1.0 if not is_oos else 0.0)
            oos_recall.append(1.0 if not is_oos else 0.0)

    print("=" * 60)
    print("RAG EVALUATION REPORT")
    print("=" * 60)
    print(f"Total cases: {len(cases)}")

    for k in k_values:
        hit_avg = sum(metrics[k]["hit"]) / len(metrics[k]["hit"])
        mrr_avg = sum(metrics[k]["mrr"]) / len(metrics[k]["mrr"])
        print(f"Hit@{k}: {hit_avg:.2%}")
        print(f"MRR@{k}: {mrr_avg:.4f}")

    print(f"\nCitation Correctness: {sum(citation_scores)/len(citation_scores):.2%}")
    print(f"OOS Precision: {sum(oos_precision)/len(oos_precision):.2%}")
    print(f"OOS Recall: {sum(oos_recall)/len(oos_recall):.2%}")

    # Per-difficulty breakdown
    print("\n--- By Difficulty ---")
    for diff in ["easy", "medium", "hard"]:
        diff_cases = [c for c in cases if c.get("difficulty") == diff]
        if not diff_cases:
            continue
        diff_hits = []
        for c in diff_cases:
            r = retriever.search(c["query"], top_k=5)
            ids = [x.product_id for x in r]
            diff_hits.append(hit_at_k(ids, c["expected_products"], 5))
        if diff_hits:
            print(f"  {diff}: Hit@5 = {sum(diff_hits)/len(diff_hits):.2%} ({len(diff_cases)} cases)")

    # Gate check
    hit5 = sum(metrics[5]["hit"]) / len(metrics[5]["hit"])
    cit = sum(citation_scores) / len(citation_scores)
    print("\n--- GATE CHECK ---")
    print(f"Hit@5: {hit5:.2%} {'✅ PASS' if hit5 >= 0.90 else '❌ FAIL'} (MVP threshold: 90%)")
    print(f"Citation: {cit:.2%} {'✅ PASS' if cit == 1.0 else '❌ FAIL'} (MVP: 100%)")

    return {
        "hit_at_5": hit5,
        "citation_correctness": cit,
        "oos_precision": sum(oos_precision)/len(oos_precision),
        "oos_recall": sum(oos_recall)/len(oos_recall),
    }


if __name__ == "__main__":
    run_evaluation()