# Single-Agent vs Multi-Agent Benchmark Report

**SYNTHETIC BENCHMARK DATA** -- no real SHB customer or transaction data.

- Dataset: `corporate-sales-single-vs-multi-agent-v1` v`2026.07.18-v1`, 5 cases
- Run at: 2026-07-17T23:26:43.559135+00:00
- Cache mode: `warm`
- git_commit: `2e76c27c6763c8a3789cc87efdc1beb3cb366ac9`, working_tree_dirty: `True`
- RAG_PROVIDER: `local`, intent mode: `deterministic`

## Routing accuracy: 0.75

## Metrics: single_agent_rag vs multi_agent

| Metric | single_agent_rag | multi_agent | Δ (multi - single) |
| --- | ---: | ---: | ---: |
| cases_evaluated | 4 | 4 | - |
| infra_errors | 0 | 0 | - |
| product_recall | 1.0 | 1.0 | 0.0 |
| product_precision | 0.5 | 0.5 | - |
| missing_info_recall | 0.0 | 1.0 | 1.0 |
| legal_flag_recall | 0.0 | 1.0 | 1.0 |
| citation_coverage | None | 1.0 | - |
| citation_validity | None | 1.0 | None |
| unsupported_claim_rate | None | 0.0 | - |
| abstention_accuracy | 0.75 | 0.75 | - |
| forbidden_violation_rate | 0.0 | 0.0 | - |
| avg_latency_ms | 1.6273 | 4.4842 | 2.8569 |

## Per-category breakdown

### simple_product_query (1 cases)
- `BENCH-A01`: routing_correct=False, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None

### multi_product_bundle (1 cases)
- `BENCH-B01`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True

### legal_risk_blocking (1 cases)
- `BENCH-D01`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True

### out_of_scope (1 cases)
- `BENCH-E01`: routing_correct=True, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None

### security_adversarial (1 cases)
- `BENCH-F01`: routing_correct=None, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None

## Cost and token usage

cost_status: `NOT_CALCULATED` -- 'local' local retrieval and the deterministic eligibility engine do not call a metered LLM in this benchmark run; token_usage/cost are reported as `null`/`NOT_CALCULATED` rather than estimated.
