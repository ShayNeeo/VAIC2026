# 14 — AI Coding Build Order and Backlog

## 1. Build policy

Không bắt đầu task nếu dependency chưa Done, trừ khi tạo interface mock rõ ràng. Mỗi task phải cập nhật `PROGRESS.md`.

Data readiness là dependency xuyên suốt. Trước V2-002/V2-006/V2-008, phải đăng ký source liên quan theo module 18, xác định Tier/owner/purpose/license và tạo synthetic contract nếu source thật chưa khả dụng.

## 2. Ordered backlog

| ID | Task | Depends on | Primary artifacts | Required tests | Done when |
|---|---|---|---|---|---|
| V2-001 | Contracts/models | — | contracts, Pydantic models, validators | contract tests | JSON/Pydantic/API examples đồng nhất |
| V2-002 | Employee/workspace context | 001 | context services/adapters | RBAC/context tests | source/freshness đầy đủ |
| V2-003 | Context assembler | 002 | merge/minimize/conflict | isolation/stale tests | no cross-case leakage |
| V2-004 | Intent extractor | 001,003 | taxonomy/prompt/extractor | intent golden | valid structured outputs |
| V2-005 | Slot/confidence/clarification | 004 | resolver/policy | no-repeat tests | clarification target đạt |
| V2-006 | Product ingestion/index | 001 | ingest/chunks/index | parser/index tests | versioned index reproducible |
| V2-007 | Hybrid retrieval/product match | 004,006 | retrieval/matcher | RAG golden | Hit@5 target, citations |
| V2-008 | Eligibility/legal | 001,007 | rule engine/legal retrieval | rule/security tests | blocking/evidence correct |
| V2-009 | Workflow/state/resume | 005,008 | state machine/nodes/impact | workflow tests | DAG/retry/resume correct |
| V2-010 | Operations/dedup/artifacts | 009 | checklist/message/dedup | replay tests | no duplicate artifacts/tasks |
| V2-011 | Safety/approval/executor | 001,009,010 | gateway/token/executor | adversarial/concurrency | no unsafe/duplicate writes |
| V2-012 | Storage/observability | 001,009,011 | DB/migrations/tracing | persistence/log tests | restart-safe pilot profile |
| V2-013 | API/UI | 002–012 | `/api/v2`, workspace UI | API/UI E2E | full journey usable |
| V2-014 | Evaluation suite | 004–013 | datasets/runners/reports | eval regression | thresholds measurable |
| V2-015 | E2E hardening | all | config/docs/docker/pilot | full suite | module 15 acceptance |

## 2.1. Data workstream đi cùng backlog

| ID | Data task | Phải hoàn thành trước | Artifact |
|---|---|---|---|
| DATA-001 | Internal source inventory + owner mapping | V2-002, V2-006 | Source Cards |
| DATA-002 | Synthetic MVP data pack + contracts | V2-002–008 | `data/synthetic/v2/`, schemas |
| DATA-003 | Manifest/quarantine/quality gates | V2-006 | ingest report + gates |
| DATA-004 | Canonical IDs/entity resolution | V2-003, V2-008 | resolver + golden matches |
| DATA-005 | Product/Legal Gold artifacts | V2-006–008 | versioned catalog/docs/rules |
| DATA-006 | Official/vendor source POC shadow mode | Pilot | coverage/cost/legal report |
| DATA-007 | Retention/deletion/lineage verification | V2-012, pilot | lifecycle tests/audit |

## 3. Suggested implementation file tree

```text
app/
├── api/v2/
├── context/
├── intent/
├── product/
├── eligibility/
├── knowledge/
│   ├── ingest/
│   ├── chunking/
│   ├── index/
│   └── retrieval/
├── workflow/
│   └── nodes/
├── operations/
├── safety/
├── approval/
├── actions/
├── integrations/
├── storage/
├── observability/
├── reliability/
└── schemas/
tests/
├── contract/
├── unit/
├── integration/
├── security/
├── e2e/
└── eval/
data/
├── synthetic/
└── eval/
```

## 4. Per-task workflow

For every task:

1. Create/update domain models from contract.
2. Define port/interface.
3. Implement deterministic core.
4. Implement mock adapter.
5. Add production adapter skeleton only if spec known.
6. Add unit tests.
7. Add integration test with upstream/downstream port.
8. Add metrics/log events.
9. Update README/config examples.
10. Update `PROGRESS.md`.

## 5. Vertical demo checkpoints

### Checkpoint 1 — Understand only (V2-001–005)

Demo: message “Kiểm tra còn thiếu gì” + workspace context → correct intent/slots without asking customer/case.

### Checkpoint 2 — Grounded recommendation (V2-006–008)

Demo: ABC multi-intent → products + eligibility + citations.

### Checkpoint 3 — Controlled workflow (V2-009–011)

Demo: pending information → upload UBO → partial resume → approval → one mock action.

### Checkpoint 4 — Pilot-shaped app (V2-012–015)

Demo: persistent state, UI context correction, trace, eval report.

## 6. Parallel work allowed

After V2-001:

- Context adapters and Product ingestion can run in parallel.
- Evaluation dataset authoring can start alongside implementation.
- UI components can be mocked after API contracts, but final integration waits for services.

Do not parallelize duplicate state models or independent tool registries.

## 7. Current-code migration strategy

- Preserve existing MVP behavior behind tests.
- Introduce V2 models/adapters incrementally.
- Add `/api/v2` without breaking `/api/v1` until migration complete.
- Wrap current synthetic services as adapters.
- Replace in-memory state only after repository abstraction tests.
- Remove old paths only after V2 E2E and compatibility decision.

