"""Phase 2 section 15/16: retrieval benchmark + ablation runner.

Ingests the REAL corpus this repo actually has (Legal via
LegalKnowledgeService, Operations via OperationsKnowledgeService, Product
via a benchmark-local ingestion of data/synthetic/v2/products.json -- see
tests/e2e/test_product_controlled_retrieval.py docstring for why Product
is not ingested through app/product/service.py here), runs
benchmarks/data/retrieval_queries.json against 4 configurations, and
writes real (not fabricated) metric results to
benchmarks/results/retrieval_benchmark_phase2.json.

Usage: PYTHONIOENCODING=utf-8 python -m benchmarks.run_retrieval_benchmark
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List

from app.knowledge.index import LocalEmbedding, PersistentHybridIndex
from app.knowledge.legal_service import LegalKnowledgeService
from app.knowledge.models import KnowledgeChunk
from app.knowledge.retrieval_contracts import AgentType, AuthorityTier, RetrievalRequest, VerificationStatus
from app.knowledge.reranker import RerankerMode
from app.knowledge.retrieval_orchestrator import ControlledRetrievalOrchestrator
from app.operations.sop_knowledge import OperationsKnowledgeService
from benchmarks import retrieval_metrics as m

ROOT = Path(__file__).resolve().parents[1]
QUERIES_PATH = ROOT / "benchmarks" / "data" / "retrieval_queries.json"
RESULTS_PATH = ROOT / "benchmarks" / "results" / "retrieval_benchmark_phase2_3.json"
PRODUCTS_PATH = ROOT / "data" / "synthetic" / "v2" / "products.json"


def _build_product_index(tmp_dir: Path) -> PersistentHybridIndex:
    index = PersistentHybridIndex(tmp_dir / "bench_product.sqlite3", provider=LocalEmbedding())
    payload = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    chunks: List[KnowledgeChunk] = []
    for product in payload["products"]:
        if not product.get("active", True):
            continue
        text = " | ".join(
            [product["name"], product["description"], product["eligibility_summary"], ", ".join(product["benefits"])]
        )
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{product['product_id']}:overview:{product['document_version']}",
                document_id=product["document_id"], document_version=product["document_version"],
                product_id=product["product_id"], section_path=product["section"], chunk_type="product_overview",
                text=text, effective_from=product["effective_from"], effective_to=product["effective_to"],
                active=True, segments=product["segments"], access_scope=product["access_scope"],
                content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                source_type="product_catalog", authority_tier=AuthorityTier.TIER_1_AUTHORITATIVE,
                verification_status=VerificationStatus.VERIFIED,
            )
        )
    index.upsert(chunks, source_hash="bench-products", dataset_version=payload["dataset_version"])
    return index


def _indexes(tmp_dir: Path) -> Dict[str, PersistentHybridIndex]:
    legal = LegalKnowledgeService(index_path=tmp_dir / "bench_legal.sqlite3", provider=LocalEmbedding())
    legal.ensure_index()
    ops = OperationsKnowledgeService(index_path=tmp_dir / "bench_ops.sqlite3", provider=LocalEmbedding())
    ops.ensure_index()
    product = _build_product_index(tmp_dir)
    return {"legal_policy": legal.index, "operations": ops.index, "product": product}


def _config_a_legacy(index: PersistentHybridIndex, query: str, product_ids) -> List[str]:
    hits = index.search(query, top_k=5, product_ids=product_ids or None, threshold=0.01)
    return [hit.chunk.chunk_id for hit in hits]


def _config_b_bm25(index: PersistentHybridIndex, query: str, product_ids) -> List[str]:
    hits = index.sparse_search_bm25(query, top_k=5, product_ids=product_ids or None)
    return [hit.chunk.chunk_id for hit in hits]


def _config_c_dense(index: PersistentHybridIndex, query: str, product_ids) -> List[str]:
    hits = index.dense_search(query, top_k=5, product_ids=product_ids or None)
    return [hit.chunk.chunk_id for hit in hits]


def _config_orchestrator(
    index: PersistentHybridIndex, agent_type: str, query: str, product_ids, **retrieve_kwargs
) -> List[str]:
    orchestrator = ControlledRetrievalOrchestrator(index)
    request = RetrievalRequest(
        request_id="bench", trace_id="bench", actor_id="bench", actor_role="RM",
        agent_type=AgentType(agent_type), task_type="benchmark",
        raw_query=query, normalized_query=query, product_ids=list(product_ids or []),
        effective_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        retrieval_policy_id=f"retrieval-policy-{agent_type.replace('_', '-')}-v1",
    )
    result = orchestrator.retrieve(request, top_k=5, **retrieve_kwargs)
    if result.grounding_pack is None:
        return []
    return [item.chunk_id for item in result.grounding_pack.items]


def run(tmp_dir: Path) -> Dict[str, object]:
    payload = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))
    queries = payload["queries"]
    indexes = _indexes(tmp_dir)

    configs = [
        "A_legacy_linear_sum", "B_bm25_only", "C_dense_only", "E_rrf_with_policy_filter",
        "F_rrf_plus_query_expansion", "G_rrf_plus_heuristic_rerank", "H_rrf_plus_mmr", "I_full_phase3",
    ]
    per_config: Dict[str, Dict[str, object]] = {c: {"recall_1": [], "recall_3": [], "recall_5": [], "mrr": [],
                                                       "ndcg_5": [], "forbidden_hit": [], "no_result_correct": []}
                                                   for c in configs}

    for q in queries:
        index = indexes[q["agent_type"]]
        product_ids = q.get("product_ids")
        relevant = q.get("relevant_chunk_ids", [])
        forbidden = q.get("forbidden_chunk_ids", [])

        ranked_by_config = {
            "A_legacy_linear_sum": _config_a_legacy(index, q["query"], product_ids),
            "B_bm25_only": _config_b_bm25(index, q["query"], product_ids),
            "C_dense_only": _config_c_dense(index, q["query"], product_ids),
            "E_rrf_with_policy_filter": _config_orchestrator(index, q["agent_type"], q["query"], product_ids),
            "F_rrf_plus_query_expansion": _config_orchestrator(
                index, q["agent_type"], q["query"], product_ids, query_expansion_enabled=True,
            ),
            "G_rrf_plus_heuristic_rerank": _config_orchestrator(
                index, q["agent_type"], q["query"], product_ids, reranker_mode=RerankerMode.HEURISTIC,
            ),
            "H_rrf_plus_mmr": _config_orchestrator(
                index, q["agent_type"], q["query"], product_ids, mmr_enabled=True,
            ),
            "I_full_phase3": _config_orchestrator(
                index, q["agent_type"], q["query"], product_ids,
                query_expansion_enabled=True, reranker_mode=RerankerMode.HEURISTIC, mmr_enabled=True,
            ),
        }
        for cfg, ranked in ranked_by_config.items():
            bucket = per_config[cfg]
            bucket["recall_1"].append(m.recall_at_k(ranked, relevant, 1))
            bucket["recall_3"].append(m.recall_at_k(ranked, relevant, 3))
            bucket["recall_5"].append(m.recall_at_k(ranked, relevant, 5))
            bucket["mrr"].append(m.reciprocal_rank(ranked, relevant))
            bucket["ndcg_5"].append(m.ndcg_at_k(ranked, relevant, 5))
            bucket["forbidden_hit"].append(m.forbidden_retrieved(ranked, forbidden, 5))
            no_res = m.no_result_correct(ranked, relevant)
            if no_res is not None:
                bucket["no_result_correct"].append(no_res)

    summary = {}
    for cfg, bucket in per_config.items():
        summary[cfg] = {
            "recall_at_1": m.average(bucket["recall_1"]),
            "recall_at_3": m.average(bucket["recall_3"]),
            "recall_at_5": m.average(bucket["recall_5"]),
            "mrr": m.average(bucket["mrr"]),
            "ndcg_at_5": m.average(bucket["ndcg_5"]),
            "forbidden_source_retrieval_rate": m.rate(bucket["forbidden_hit"]),
            "no_result_correct_rate": m.rate(bucket["no_result_correct"]) if bucket["no_result_correct"] else None,
        }

    return {
        "benchmark_version": payload["benchmark_version"],
        "query_count": len(queries),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": summary,
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
