# RAG Provider and Fallback

## What changed and why

Before this change, `ProductKnowledgeService.search()` and
`LegalKnowledgeService.search()` each had ~60 lines of inline logic gated by
a single boolean, `RAG_MCP_ENABLED` (default `true`): if enabled, try the
standalone RAG MCP server; on **any** exception, log a bare
`logger.warning(...)` and silently fall through to the local SQLite index.
This had three real, observed problems:

1. **No way to run local-only without attempting an MCP connection.** Every
   test run and every local dev session that didn't have `services/rag_mcp`
   running paid the cost of a connection attempt, a timeout, and a warning
   log line on every single product/legal search — this was directly
   responsible for `RAG MCP Product search failed, falling back to local
   SQLite: Session terminated` noise on nearly every test.
2. **No circuit breaker.** A down MCP server meant every request re-paid
   the full connection/timeout cost, forever.
3. **No distinction between "MCP is temporarily unreachable" (safe to fall
   back) and "MCP rejected the request" (auth/policy/schema failure — must
   not be silently retried against local data under a different policy).**

## The new model: `RAG_PROVIDER=local|mcp|hybrid`

Set in `.env`/`.env.v2.example`. Read once at import time by
`app/config.py::_resolve_rag_provider()`.

| Mode | Behavior |
| --- | --- |
| `local` (default) | Only ever calls the local SQLite/embedding index. Never constructs an MCP client, never health-checks MCP, never logs an MCP warning. |
| `mcp` | Only ever calls MCP. On any failure, raises `RagProviderUnavailableError` (a structured Python exception) instead of falling back. |
| `hybrid` | Prefers MCP, guarded by a circuit breaker and a hard per-call timeout (`RAG_MCP_REQUEST_TIMEOUT_SECONDS`, default 3s). Falls back to local **only** for network/availability failures (`is_recoverable_error()` in `app/knowledge/rag_provider.py`); anything else (a bare `RuntimeError` from `RagMCPClient._call()`, which is what an auth/policy/schema denial looks like) propagates instead of being silently swallowed. |

### Backward compatibility

`RAG_MCP_ENABLED` is still read (so an old `.env` doesn't break at import),
but only consulted when `RAG_PROVIDER` is **not** set: `true` maps to
`hybrid` (the old "try then silently fall back" behavior), `false` maps to
`local`. A `DeprecationWarning` is emitted once per process. If both are
set, `RAG_PROVIDER` wins.

## Architecture

```
ProductKnowledgeService / LegalKnowledgeService
        │  (one RagProviderRouter instance per service, built once in __init__)
        ▼
RagProviderRouter (app/knowledge/rag_provider.py)
        │
        ├── mode="local"  → local_search() only
        ├── mode="mcp"    → mcp_search() only, no fallback, raises on failure
        └── mode="hybrid" → CircuitBreaker.allow_request()?
                              ├─ no  → local_search() (fallback_reason="circuit_open")
                              └─ yes → try mcp_search() with a hard timeout
                                         ├─ success → record_success(), return MCP hits
                                         └─ recoverable error → record_failure(),
                                                                 local_search()
                                         └─ non-recoverable error → raise (no fallback)
```

Every `RagProviderRouter.search()` call returns a `SearchOutcome` (kept on
`ProductKnowledgeService.last_search_outcome`, not part of the public
`List[RetrievalHit]` return type, so no existing caller's contract
changed):

```python
SearchOutcome(
    hits=[...],
    provider_requested="hybrid",
    provider_used="local",
    fallback_used=True,
    fallback_reason="ConnectionError",
    latency_ms=12.4,
)
```

### Circuit breaker

Three states (`CLOSED` / `OPEN` / `HALF_OPEN`), an injectable clock (tests
never sleep), configured via:

```env
RAG_MCP_FAILURE_THRESHOLD=3
RAG_MCP_COOLDOWN_SECONDS=30
RAG_MCP_REQUEST_TIMEOUT_SECONDS=3
RAG_MCP_HALF_OPEN_MAX_CALLS=1
```

`N` consecutive recoverable failures → `OPEN` (no more MCP calls attempted
until cooldown elapses) → `HALF_OPEN` (bounded probe calls) → a successful
probe closes the circuit, a failed probe re-opens it.

### Why the MCP call always runs in a dedicated worker thread

`RagProviderRouter` owns one `ThreadPoolExecutor` for its lifetime (built
once, in the service's `__init__`, not per-call — see the comment in
`RagProviderRouter.__init__` for why a per-call executor would either block
on `.shutdown(wait=True)` even after a timeout fired, or leak threads if
never shut down). `make_async_bridge()` always calls `asyncio.run()` fresh
inside that worker thread, so it never shares an event loop with the
caller's already-running loop. The previous inline implementation
sometimes reused the caller's running loop via a nested
"`ThreadPoolExecutor` wrapping `asyncio.run`" pattern — the most likely
cause of `tests/rag_mcp/test_transport.py`'s async-cleanup flake (see
`docs/P1_RELIABILITY_AND_EVALUATION_IMPLEMENTATION_REPORT.md` §21).

### Logging

`RateLimitedWarningLogger` (in the same module) logs a `WARNING` the first
time a given failure key is seen, then demotes repeats within
`RAG_MCP_WARNING_COOLDOWN_SECONDS` (default 30s) to `DEBUG` instead of
either spamming or dropping them. Recovery is logged once at `INFO`.

### Metrics

Uses the existing lightweight `app.observability.runtime.metrics` counter
registry (the same one `app/api/v2/router.py` already increments), with
keys like `rag.product.requests_total.hybrid`,
`rag.product.mcp_result_total.failure`,
`rag.product.mcp_fallback_total.ConnectionError`,
`rag.product.local_result_total.success`. No Prometheus dependency was
added; `GET /api/v2/metrics` already exposes a snapshot of this registry.

### Health and readiness

`GET /api/v2/health` gained an additive `rag_provider` block (existing keys
unchanged):

```json
{
  "status": "ok",
  "rag_provider": {
    "status": "healthy",
    "mode": "local",
    "providers": {
      "product": {"status": "healthy", "mode": "local", "error_code": null},
      "legal": {"status": "healthy", "mode": "local", "error_code": null}
    }
  }
}
```

A new `GET /api/v2/ready` returns `503` when storage itself is unhealthy,
`200` with `status: "degraded"` when a hybrid provider's circuit is open,
and `200` with `status: "healthy"` otherwise. Neither endpoint makes a live
MCP network call (cheap, `CircuitBreaker.state` read only) — a genuine
MCP round-trip health probe is a larger addition left for a follow-up.

## Known limitation: no offline/mock embedding provider

`create_embedding_provider()` in `app/knowledge/index.py` supports
`openai` and `gemini` only; a previous `DeterministicHashEmbedding`
fallback (usable with no API key at all) existed earlier in this repo's
history and was removed by a separate change before this work started.
This means **product/legal retrieval always needs a real, working
embedding provider** — `RAG_PROVIDER=local` removes the MCP dependency but
not the embedding-API dependency. This is why `.github/workflows/ci.yml`
requires an `OPENAI_API_KEY` repository secret to pass; there is currently
no way to run the full test suite with zero network/API dependencies. This
is a real, disclosed gap, not something this change set out to fix (it is
listed as a P2 follow-up in the final report).
