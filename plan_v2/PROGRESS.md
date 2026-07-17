# PROGRESS — V2 Build State

File này là bộ nhớ bàn giao giữa các phiên AI. Cập nhật trong cùng commit/change set với code.

## 1. Tổng quan

| Trường | Giá trị |
|---|---|
| Plan version | `2.0.0` |
| Cập nhật cuối | `2026-07-17` |
| Giai đoạn | `Planning complete — implementation not started` |
| Task đang làm | `None` |
| Blocker | `Cần xác nhận API/dữ liệu thật trước pilot; không chặn MVP synthetic` |

## 2. Baseline hiện có trong repo

| Thành phần | Baseline | V2 cần làm |
|---|---|---|
| Shared state | Có Pydantic MVP | Migrate sang JSON contract V2 + provenance |
| Planner | Có deterministic DAG | Nối Context/Intent và impact-based resume |
| Product retrieval | Có in-memory hybrid-lite | Ingestion + persistent hybrid index + metadata ACL |
| Product Agent | Có deterministic MVP | Dùng intent contract và evidence versioning |
| Legal Agent | Có synthetic rules | Rule registry + legal RAG + version/effective dates |
| Operations | Có checklist/email draft | Artifact reuse + dedup + partial update |
| Approval | Có HMAC demo | Payload hash, nonce, expiry, one-time use, RBAC |
| API/UI | Có FastAPI và demo UI | Context endpoints, correction UI, intent preview |
| Tests | 16 tests, 91% baseline coverage | V2 golden sets và thresholds trong module 15 |

Baseline không đồng nghĩa task V2 đã Done. Mỗi task chỉ Done khi đạt acceptance V2.

## 3. Task tracker

| ID | Task | Status | Evidence | Deviation |
|---|---|---|---|---|
| V2-001 | Contracts + schema validation | Not Started | | |
| V2-002 | Employee/Workspace Context | Not Started | | |
| V2-003 | Context Assembler | Not Started | | |
| V2-004 | Intent Extractor | Not Started | | |
| V2-005 | Slot Auto-Fill + Confidence | Not Started | | |
| V2-006 | Product ingestion/index | Not Started | | |
| V2-007 | Hybrid retrieval/evidence | Not Started | | |
| V2-008 | Eligibility/Legal | Not Started | | |
| V2-009 | Orchestration/state machine | Not Started | | |
| V2-010 | Operations/dedup/resume | Not Started | | |
| V2-011 | Safety/approval/executor | Not Started | | |
| V2-012 | Storage/observability | Not Started | | |
| V2-013 | API/UI | Not Started | | |
| V2-014 | Evaluation/golden datasets | Not Started | | |
| V2-015 | E2E pilot-ready MVP | Not Started | | |

Status chỉ dùng: `Not Started`, `In Progress`, `Blocked`, `Done`.

## 4. Decision log

### 2026-07-17 — Contract-first modular planning

- Quyết định: JSON schemas trong `contracts/` là source of truth.
- Lý do: ngăn các phiên AI tự thêm field/trạng thái không đồng bộ.
- Ảnh hưởng: mọi module và test phải import/validate cùng contract version.

### 2026-07-17 — Workflow-first, agent optional

- Quyết định: deterministic workflow là runtime mặc định; LLM chỉ ở các node semantic.
- Lý do: giảm bất định, dễ resume, dedup và kiểm thử.
- Ảnh hưởng: không dùng autonomous multi-agent cho external actions.

## 5. Deviation log

Chưa có deviation V2. Khi phát sinh, ghi:

```text
Task/Contract:
Plan yêu cầu:
Thực tế:
Lý do:
Migration/test bổ sung:
Cần xử lý sau:
```

## 6. Verification log

| Ngày | Task | Command/Test | Kết quả | Ghi chú |
|---|---|---|---|---|
| 2026-07-17 | Plan package validation | PowerShell `ConvertFrom-Json` for all contracts | Pass: 4/4 JSON contracts | 24 plan files, 2,436 lines before AGENTS entrypoint update |
