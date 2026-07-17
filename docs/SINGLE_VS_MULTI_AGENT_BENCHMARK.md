# Single-Agent vs Multi-Agent Benchmark

Prior state: `mode="single_agent_rag"` was only ever a **routing label**
attached by `ComplexityRouter` (`app/workflow/engine.py:104`) — it recorded
which path was taken, with zero comparative metrics. This is a real,
executed benchmark that runs the **same 40 cases through both paths** and
computes real metrics from real pipeline output.

## How fairness is achieved

Both `single_agent_rag` and `multi_agent` runs for a given case use:
identical input text/customer attributes/documents, the identical product
catalog and knowledge index (`data/synthetic/v2/products.json` +
`eligibility_rules.json`), the identical `RAG_PROVIDER`/embedding provider,
the identical timeout, the identical cache mode. The only difference is a
new `force_route: Literal["simple","complex"] | None = None` keyword-only
parameter on `V2WorkflowEngine.run()` (`app/workflow/engine.py`), which
bypasses `ComplexityRouter.is_complex(state)` when set. **Default is
`None`** — production routing (the real `/api/v2/sales-cases/.../run-analysis`
path) is completely unaffected; `force_route` is only ever passed by
`benchmarks/run.py`.

Each case actually runs **three** times: once unforced ("natural" —
measures whether `ComplexityRouter`'s real decision matches the dataset's
expected route), once forced simple, once forced complex.

Group F (security/adversarial) cases are not run through the engine at
all — they call `app.safety.input_guardrails_v2.screen_input()` directly,
because that is the actual, real enforcement point
(`app/api/v2/router.py`'s `create_sales_case`/`create_case`/`add_message`
all call it before anything reaches the workflow engine).

## Dataset — `benchmarks/data/corporate_sales_cases.json`

40 cases, **SYNTHETIC BENCHMARK DATA**, 6 categories exactly per spec:

| Category | Count | Ground truth checks |
| --- | --- | --- |
| A — simple product queries | 8 | expected route |
| B — multi-product bundle | 10 | route, required/acceptable product IDs, expected case status, required missing info |
| C — missing information | 8 | route, required product ID, required missing info (built from real `eligibility_rules.json` gates: revenue/account-count/operating-years/UBO/employee-count) |
| D — legal/risk blocking | 6 | route, required legal flags (real `failure_code`s: `BAD_DEBT_FOUND`, `OPERATING_HISTORY_TOO_SHORT`, `EMPLOYEE_COUNT_BELOW_MINIMUM`, `REVENUE_BELOW_MINIMUM`, `UBO_MISSING_OR_UNVERIFIED`) |
| E — out-of-scope | 4 | must_abstain |
| F — security/adversarial | 4 | blocked at `screen_input`, not routed at all |

Ground truth uses the JSON shape from the spec (`case_id`, `category`,
`input`, `expected.{route,required_product_ids,acceptable_product_ids,
forbidden_product_ids,required_missing_information,required_legal_flags,
expected_case_status,must_require_human_approval,must_abstain}`), not an
LLM judge.

## Metrics — `benchmarks/metrics.py` (10 unit tests)

Every metric is a pure function over plain data; `None` (not `0.0`) when a
case has no ground truth for that metric, so averaging never silently
treats "not applicable" as "failed" — `aggregate_optional_floats`/
`aggregate_bools` both drop `None`s before averaging.

`product_recall`, `product_precision`, `forbidden_product_violation`,
`missing_information_recall`, `legal_flag_recall`, `citation_coverage`,
`citation_validity` (uses the **real** `Evidence.is_valid` set by the
evidence validator wired into the live engine — see
`docs/EVIDENCE_VALIDATION_IMPLEMENTATION.md`, not a benchmark-only check),
`unsupported_claim_rate`, `routing_correct`, `abstention_correct`.

`action_correctness`/`tool_selection_accuracy` from the original spec list
are **not computed** — this benchmark does not run the approval/execution
flow (that requires a real approval token round trip, out of scope for a
routing/retrieval/eligibility benchmark); `action_readiness` is captured
per-case in `results.jsonl` for manual inspection instead.
`token_usage`/`cost` are always `null`/`"NOT_CALCULATED"` — the
deterministic-intent + local-embedding path used by default doesn't call a
metered LLM, and this benchmark does not estimate cost from a pricing
table it can't verify.

## Real bugs found and fixed while building this (via actual execution, not inspection)

1. **Benchmark employee had no branch → every `PROD-WORKING-CAPITAL` case
   scored 0 recall.** `PROD-WORKING-CAPITAL`'s `access_scope.branches =
   ["HN01", "HCM01"]` (not `"*"`); the knowledge ACL filter treats a caller
   branch of `"*"` as "no specific branch," not "sees everything" — so the
   benchmark's default `MINIMAL_CONTEXT_SNAPSHOT` (`access_scope={}` →
   branch defaults to `"*"`) could never see it. Fixed by giving the
   benchmark employee `access_scope={"branch": "HN01"}`, matching what a
   real RM session always has (`SQLiteIAMAdapter` never returns an empty
   branch).
2. **Abstention was measured off `case status`, which the simple path
   never reaches.** The single-agent path always ends
   `CaseStatus.COMPLETED`, whether or not it found a product — it never
   reaches `PENDING_REVIEW` (that's a complex-path-only branch on
   `no_grounded_product`). The original abstention check
   (`status == "pending_review"`) therefore always reported
   `single_agent_rag` as "never abstains," even when it recommended
   nothing. Fixed to check `not product_ids` directly, uniformly for both
   paths.
3. **A malformed case would crash the whole benchmark run, not just that
   case.** `_build_state()`/engine construction were originally called
   *before* the `try/except` in `_run_case_mode`, so an exception there
   propagated out of the whole run instead of being recorded as that
   case's `infra_error`. Moved inside the `try` block (caught by a new
   regression test, `test_infra_error_is_recorded_not_silently_treated_as_zero_recall`).
4. **Ground-truth data bug, not a code bug:** `BENCH-B01` set
   `ubo_status: "pending"`, but `EligibilityEngine._execute()`'s "unverified
   UBO" special case only recognizes specific Vietnamese phrases
   (`"chưa xác minh đầy đủ"` etc.) as PENDING_INFORMATION — `"pending"`
   fell through to `FAILED`. Corrected the fixture value; this was a test
   authoring mistake, not a system defect (the actual matching behavior is
   covered by `BENCH-C03`, which uses the correct phrase and passes).

## Cold-cache vs warm-cache

`--cache-mode cold` temporarily redirects `settings.VECTOR_DB_DIR` to a
fresh `tempfile.mkdtemp()` directory (cleaned up afterward) so every
embedding call is a genuinely fresh API call, not served from
`data/vector_db/openai_vector_cache.json`. `--cache-mode warm` uses the
repo's persistent index/cache. This was smoke-tested on 3 cases
(`BENCH-B02`, `BENCH-D03`, `BENCH-E02`); `single_agent_rag.avg_latency_ms`
jumped from ~2-50ms (warm) to ~161ms (cold), confirming it genuinely hit
the network rather than reusing a cache. The full 40-case run was executed
in **warm** mode only (cold-mode full run would mean ~120 fresh embedding
calls across 3 engine runs × 40 cases — a deliberate cost/time scoping
decision, disclosed here rather than silently run or silently skipped).

## How to run

```powershell
# Full 40-case run, warm cache, deterministic intent (no API cost beyond
# whatever embeddings aren't already cached in data/vector_db/):
python -m benchmarks.run --cache-mode warm --output-dir benchmarks/results/latest

# Small cold-cache smoke test (real, fresh API calls):
python -m benchmarks.run --cache-mode cold --cases BENCH-B02,BENCH-D03,BENCH-E02 --output-dir benchmarks/results/cold_smoke

# With the real OpenAI-backed intent extractor instead of the deterministic
# fallback (real API cost/latency; requires OPENAI_API_KEY):
python -m benchmarks.run --live-intent
```

Outputs: `results.jsonl` (one row per case×mode), `summary.json`
(aggregate + comparison), `report.md` (human-readable, per-category
breakdown).

## Results (warm cache, deterministic intent, 2026-07-18)

40 cases, `single_agent_rag`/`multi_agent` each evaluated on the 36 cases
where routing/abstention applies (Group F's 4 cases are scored separately
via `screen_input`, all 4 correctly blocked).

| Metric | single_agent_rag | multi_agent |
| --- | ---: | ---: |
| product_recall | 0.9167 | 0.9167 |
| product_precision | 0.8462 | 0.8462 |
| **missing_info_recall** | **0.0** | **0.8889** |
| **legal_flag_recall** | **0.0** | **0.8333** |
| citation_coverage | null (no evidence produced) | 1.0 |
| citation_validity | null | 1.0 |
| abstention_accuracy | 0.9677 | 0.9677 |
| avg_latency_ms | 46.99 | 49.80 |

**Routing accuracy: 0.8333** (30/36 applicable cases) — real, not tuned to
100%; see "Known limitation" below.

### The headline, real finding

Product retrieval quality is **identical** between the two paths (both do
real RAG search) — `product_recall`/`product_precision` show no
difference. The entire, safety-relevant difference is downstream:
**the single-agent path has zero ability to catch missing information or
legal/risk blocking conditions**, because it structurally never runs
`EligibilityEngine`. Forcing a legal-risk-blocking case (e.g. a customer
with recent bad debt asking for working capital) through the single-agent
path produces a clean product recommendation with no risk flag at all —
confirmed directly in `benchmarks/results/latest/results.jsonl` for every
`legal_risk_blocking` case. This is the single most important, genuinely
discovered (not assumed) result of building this benchmark.

### Known limitation: routing_accuracy is 0.83, not 1.0

Several Group A ("simple query") cases combine a `compare_products` signal
with product-name keywords (e.g. "trả lương", "dòng tiền"). The
deterministic intent extractor (`app/intent/fallback.py`) detects **both**
`compare_products` and `find_product` as intents in that case; `find_product`
becomes a non-empty `sub_intents` entry, and `ComplexityRouter.is_simple()`
returns `False` whenever `sub_intents` is non-empty (`app/workflow/router.py`)
— even though `compare_products` alone would have been "simple." This is
real, observed router behavior, not a benchmark bug, and the ground truth
was deliberately left as-is (not curve-fit to whatever the router currently
does) so `routing_accuracy` stays a genuine, informative signal.
