# Single-Agent vs Multi-Agent Benchmark Report

**SYNTHETIC BENCHMARK DATA** -- no real SHB customer or transaction data.

- Dataset: `corporate-sales-single-vs-multi-agent-v1` v`2026.07.18-v1`, 40 cases
- Run at: 2026-07-17T22:21:29.174831+00:00
- Cache mode: `warm`
- git_commit: `bd18718eafb465cae44765295edbc23f2ff51534`, working_tree_dirty: `True`
- RAG_PROVIDER: `local`, intent mode: `deterministic`

## Routing accuracy: 0.8333

## Metrics: single_agent_rag vs multi_agent

| Metric | single_agent_rag | multi_agent | Δ (multi - single) |
| --- | ---: | ---: | ---: |
| cases_evaluated | 36 | 36 | - |
| infra_errors | 0 | 0 | - |
| product_recall | 0.9167 | 0.9167 | 0.0 |
| product_precision | 0.8462 | 0.8462 | - |
| missing_info_recall | 0.0 | 0.8889 | 0.8889 |
| legal_flag_recall | 0.0 | 0.8333 | 0.8333 |
| citation_coverage | None | 1.0 | - |
| citation_validity | None | 1.0 | None |
| unsupported_claim_rate | None | 0.0 | - |
| abstention_accuracy | 0.9677 | 0.9677 | - |
| forbidden_violation_rate | 0.0 | 0.0 | - |
| avg_latency_ms | 47.8179 | 50.5556 | 2.7377 |

## Per-category breakdown

### simple_product_query (8 cases)
- `BENCH-A01`: routing_correct=False, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-A02`: routing_correct=False, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-A03`: routing_correct=True, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-A04`: routing_correct=False, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-A05`: routing_correct=True, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-A06`: routing_correct=False, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-A07`: routing_correct=False, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-A08`: routing_correct=False, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None

### multi_product_bundle (10 cases)
- `BENCH-B01`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-B02`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-B03`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-B04`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-B05`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-B06`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-B07`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-B08`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-B09`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-B10`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True

### missing_information (8 cases)
- `BENCH-C01`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-C02`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-C03`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-C04`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-C05`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-C06`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-C07`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-C08`: routing_correct=True, single_agent_rag=recall=0.0,status_ok=False, multi_agent=recall=0.0,status_ok=False

### legal_risk_blocking (6 cases)
- `BENCH-D01`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-D02`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-D03`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-D04`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True
- `BENCH-D05`: routing_correct=True, single_agent_rag=recall=0.0,status_ok=False, multi_agent=recall=0.0,status_ok=False
- `BENCH-D06`: routing_correct=True, single_agent_rag=recall=1.0,status_ok=False, multi_agent=recall=1.0,status_ok=True

### out_of_scope (4 cases)
- `BENCH-E01`: routing_correct=True, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-E02`: routing_correct=True, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-E03`: routing_correct=True, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-E04`: routing_correct=True, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None

### security_adversarial (4 cases)
- `BENCH-F01`: routing_correct=None, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-F02`: routing_correct=None, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-F03`: routing_correct=None, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None
- `BENCH-F04`: routing_correct=None, single_agent_rag=recall=None,status_ok=None, multi_agent=recall=None,status_ok=None

## Cost and token usage

cost_status: `NOT_CALCULATED` -- 'local' local retrieval and the deterministic eligibility engine do not call a metered LLM in this benchmark run; token_usage/cost are reported as `null`/`NOT_CALCULATED` rather than estimated.
