# 13 — Storage, Observability and Reliability

## 1. Storage design

### PostgreSQL tables

| Table | Key fields | Purpose |
|---|---|---|
| `cases` | case_id, customer_id, employee scope, status, version | Current case index |
| `case_state_versions` | state_id, case_id, schema_version, state_json, hash | Immutable snapshots |
| `workflow_tasks` | task_id, case_id, type, dedup_key, status, input/output hash | DAG/task state |
| `context_values` | case_id, field_path, source, confidence, freshness | Provenance/query |
| `artifacts` | artifact_id, type, version, content hash, status | Draft/checklist/email |
| `approval_tokens` | token_id, payload_hash, expiry, status | One-time approval |
| `idempotency_records` | key, action, status, result_ref | Side-effect dedup |
| `audit_events` | event_id, prev_hash, event_hash, actor, action, payload | Tamper-evident audit |
| `feedback` | case_id, rating/correction, labels | Evaluation loop |

Sensitive fields encrypted/column-protected according to policy.

### Other stores

- Vector DB: product/legal chunks and metadata ACL.
- Object/DMS: source files, not raw blobs in case state.
- Redis/cache: context and retrieval caches with TTL.
- Metrics/traces: OpenTelemetry backend.

## 2. Concurrency

- Case state optimistic locking by version.
- External action distributed/idempotency lock.
- Artifact version append-only.
- Approval tied to exact state/payload version.
- Concurrent correction/approval returns conflict and requires refresh.

## 3. Audit integrity

Each event includes:

```text
event_id, case_id, trace_id, timestamp
actor_type/id (pseudonymized where appropriate)
action, sanitized payload
state_version_before/after
prev_event_hash, event_hash
```

Audit event is append-only; corrections create new event.

## 4. Observability

### Traces

- End-to-end trace ID.
- Node spans.
- Model/retrieval/tool spans.
- Retry/cache/fallback attributes.
- Never attach raw sensitive content.

### Logs

- JSON structured.
- error/event codes.
- prompt/workflow/rule/index versions.
- sanitized IDs/arguments.
- security flags.

### Metrics

| Domain | Metrics |
|---|---|
| Context | load latency, stale rate, conflict rate, auto-fill rate |
| Intent | accuracy sample, schema errors, clarification rate |
| RAG | hit rate, empty rate, threshold rejects, latency |
| Eligibility | blocking/warning/pending rates, rule errors |
| Workflow | success, node latency, retries, resume accuracy |
| Operations | dedup hits, reused artifacts, email edit rate |
| Safety | injection flags, permission denials, invalid evidence |
| Actions | approval/execute success, duplicate prevented |
| Cost | model tokens/cost per case |

## 5. SLOs

Initial MVP/pilot SLOs:

- API read availability 99.5% pilot.
- P95 context assembly < 2s excluding unavailable upstream.
- P95 analysis < 30s.
- Write action duplicate rate 0.
- High-risk security alerts emitted < 1 minute.

## 6. Reliability patterns

- Timeout every network/model call.
- Exponential backoff with jitter for safe reads.
- Circuit breaker per dependency.
- Cache with TTL/version/permission scope.
- Bulkhead model/retrieval/external write workers.
- Dead-letter queue for async jobs.
- Status reconciliation for uncertain write outcomes.
- Graceful degradation that never bypasses safety.

## 7. Cache policy

| Cache | Key must include | Invalidation |
|---|---|---|
| Employee permission | employee + IAM version | IAM event/TTL |
| Customer profile | customer + profile version + scope | CRM event/TTL |
| Retrieval | normalized query + filters + index version + scope | index version |
| Node result | input hash + dependency versions | impact graph |
| Eligibility | customer/product/rule/data versions | any dependency change |

No cross-user reuse if access scopes differ.

## 8. Secrets/config

- Secrets manager/env injection; no default production secret.
- Config schema validated at startup.
- Separate dev/pilot/prod profiles.
- Model/index/rule/workflow versions explicit.
- Startup fails closed if approval signing secret missing outside dev.

## 9. Proposed code artifacts

| File | Responsibility |
|---|---|
| `app/storage/repositories.py` | Domain repositories |
| `app/storage/models.py` | ORM tables |
| `app/storage/migrations/` | Schema migrations |
| `app/observability/tracing.py` | OpenTelemetry setup |
| `app/observability/logging.py` | Sanitized structured logs |
| `app/observability/metrics.py` | Metrics instruments |
| `app/reliability/retry.py` | Retry policies |
| `app/reliability/circuit_breaker.py` | Dependency breaker |
| `app/reliability/cache.py` | Versioned scoped cache |

## 10. Tests

- Optimistic concurrency conflict.
- Idempotency across process retry.
- Cache ACL isolation.
- Audit hash chain verification.
- Circuit breaker open/half-open.
- CRM timeout outcome reconciliation.
- Logs redact PII/token.
- State schema migration.

## 11. Acceptance

- Restart does not lose state in pilot profile.
- Duplicate external write = 0 under retry/concurrency tests.
- Trace links API → workflow → retrieval/tool.
- No secret/PII in sampled logs.

