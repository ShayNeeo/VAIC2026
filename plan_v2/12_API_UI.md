# 12 — API and RM Workspace UI

## 1. API principles

- Prefix `/api/v2`.
- Typed request/response; validate against contracts.
- Auth principal from session/token, not trusted request body.
- Stable error codes.
- Correlation/trace ID in response headers.
- Optimistic concurrency via state version/ETag.
- Idempotency header for writes.

## 2. Endpoints

| Method | Endpoint | Purpose | Risk |
|---|---|---|---|
| GET | `/context/current` | Employee/workspace context | sensitive read |
| POST | `/context/resolve` | Assemble context for message | sensitive read |
| POST | `/cases` | Create analysis case | internal write |
| GET | `/cases/{id}` | State/summary | sensitive read |
| POST | `/cases/{id}/messages` | Add request/clarification answer | internal write |
| POST | `/cases/{id}/documents` | Register/upload document metadata | internal write |
| POST | `/cases/{id}/resume` | Resume impacted workflow | internal write |
| GET | `/cases/{id}/trace` | User-safe trace | sensitive read |
| PATCH | `/cases/{id}/context` | Correct context with reason | internal write |
| POST | `/cases/{id}/approval-preview` | Freeze payload preview | high read/prep |
| POST | `/cases/{id}/approve` | Issue approval for frozen payload | high |
| POST | `/cases/{id}/execute` | Execute approved action | high external write |
| POST | `/cases/{id}/reject` | Reject action | high internal write |
| GET | `/knowledge/products/search` | Read-only product search | read |

## 3. Key request semantics

### Create case

- Body contains message and optional explicit customer/case IDs.
- Employee identity from auth.
- Workspace context from server/session adapter.
- Return `case_id`, `status`, `intent_preview`, `context_summary`, `next_action`.

### Correct context

- Requires `field`, `new_value`, `reason`, `expected_state_version`.
- Creates correction event.
- Returns impacted nodes/artifacts and whether approval invalidated.

### Resume

- Body lists changed artifact IDs or field paths.
- Server computes resume nodes; client cannot arbitrarily skip safety nodes.

## 4. UI screens

### A. Context Header

Always visible:

```text
RM / Role | Customer | Active Case | Current Step | Product(s) | Missing Info
```

Shows source/freshness tooltip and edit control if permitted.

### B. Intent Preview

- “Hệ thống hiểu rằng…” summary.
- Primary/sub-intents.
- Resolved fields and sources.
- Assumptions/low-confidence fields.
- One targeted clarification if blocking.

### C. Product/Evidence Panel

- Product candidate + score components.
- Eligibility per product.
- Source quote/version side by side.
- Blocked/pending reasons.

### D. Operations Panel

- Checklist with existing/missing status.
- Existing task reused/update/create badges.
- Email draft editor with version/diff.
- SLA source.

### E. Approval Panel

- Exact actions and payload diff.
- Target system/recipient.
- Risk/evidence status.
- Approve/reject; no generic single click without preview.

### F. Timeline

User-safe event timeline, not hidden chain-of-thought:

- Context loaded.
- Intent resolved.
- Retrieval/rules run.
- Evidence validated.
- Draft updated/reused.
- Approval/execution events.

## 5. UX to minimize repetition

- Pre-fill from context with visible source.
- Preserve draft edits.
- Highlight reused artifact/task.
- On new document, offer “Resume affected checks” not “Run all”.
- Clarification asks one focused question.
- Context correction immediately shows impact preview.

## 6. Accessibility/localization

- Vietnamese default, English optional.
- Keyboard navigation and accessible labels.
- Color not sole status indicator.
- Dates/timezone explicit.
- Currency/number localized but API canonical.

## 7. Proposed code artifacts

| File | Responsibility |
|---|---|
| `app/api/v2/context.py` | Context endpoints |
| `app/api/v2/cases.py` | Case/messages/documents/resume |
| `app/api/v2/approval.py` | Preview/approve/execute/reject |
| `app/api/v2/knowledge.py` | Read-only search |
| `app/api/errors.py` | Stable error envelope |
| `app/api/auth.py` | Principal/session mapping |
| `web/src/components/ContextHeader.*` | Context display/correction |
| `web/src/components/IntentPreview.*` | Intent/confidence |
| `web/src/components/EvidencePanel.*` | Claims/sources |
| `web/src/components/ApprovalPanel.*` | Frozen payload/HITL |

If keeping server-rendered MVP UI, preserve component boundaries in templates/JS modules.

## 8. Tests

- Auth identity cannot be spoofed via body.
- Wrong RM gets 403.
- ETag/state version conflict returns 409.
- Context correction computes impact.
- Resume cannot skip evidence node.
- Approval preview payload equals executed payload hash.
- UI displays source/confidence/stale flags.
- Keyboard/accessibility smoke tests.

## 9. Acceptance

- Complete ABC journey usable without Swagger/manual DB edits.
- No repeated customer/case input when workspace context exists.
- All high-risk actions show preview and explicit approval.

