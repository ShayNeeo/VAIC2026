# Single-Agent vs Multi-Agent Benchmark Report

**SYNTHETIC BENCHMARK DATA** -- no real SHB customer or transaction data.

- Dataset: `corporate-sales-single-vs-multi-agent-v1` v`2026.07.18-v1`, 1 cases
- Run at: 2026-07-18T05:46:35.673747+00:00
- Cache mode: `warm`
- git_commit: `None`, working_tree_dirty: `None`
- RAG_PROVIDER: `local`, intent mode: `deterministic`

## Routing accuracy: 1.0

## Metrics: single_agent_rag vs multi_agent

| Metric | single_agent_rag | multi_agent | Δ (multi - single) |
| --- | ---: | ---: | ---: |
| cases_evaluated | 0 | 0 | - |
| infra_errors | 1 | 1 | - |
| product_recall | None | None | None |
| product_precision | None | None | - |
| missing_info_recall | None | None | None |
| legal_flag_recall | None | None | None |
| citation_coverage | None | None | - |
| citation_validity | None | None | None |
| unsupported_claim_rate | None | None | - |
| abstention_accuracy | None | None | - |
| forbidden_violation_rate | None | None | - |
| avg_latency_ms | None | None | None |

## Per-category breakdown

### simple_product_query (1 cases)
- `BENCH-A01`: routing_correct=True, single_agent_rag=INFRA_ERROR(missing_result), multi_agent=INFRA_ERROR(missing_result)

## Cost and token usage

cost_status: `NOT_CALCULATED` -- 'local' local retrieval and the deterministic eligibility engine do not call a metered LLM in this benchmark run; token_usage/cost are reported as `null`/`NOT_CALCULATED` rather than estimated.
