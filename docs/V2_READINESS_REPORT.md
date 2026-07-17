# V2 Readiness Report

Thang điểm: `0` chưa có; `1` interface/plan; `2` local/mock; `3` E2E synthetic có test; `4` pilot-shaped persistent có eval/observability; `5` production verified bằng dữ liệu, hạ tầng và security review thật.

## Trạng thái local MVP

| Hạng mục | Điểm / 5 | Bằng chứng | Gap để production |
|---|---:|---|---|
| Shared contracts | 3 | Pydantic + JSON Schema, intake/planner/AI log contracts và contract tests | Governance/version migration production |
| Employee/workspace context | 3 | Adapters, RBAC scope, provenance, correction/impact tests | SSO/IAM/session/CRM thật |
| Intent understanding | 3 | Multi-intent, fallback, slots, confidence, message rerun | SME-labeled conversation dataset |
| Product RAG | 4 | Source Card, parser, persistent index, ACL/version eval | Semantic embedding + catalog thật |
| Eligibility/Legal | 4 | Deterministic rules + persistent Legal RAG + fail-closed tests | Legal corpus/live KYC-CIC thật và sign-off |
| Workflow/resume | 4 | State machine, DAG, impact resume, loop guard | Distributed workers/event reconciliation |
| Operations/dedup | 4 | Versioned drafts, checklist merge, dedup | CRM/task/SOP thật và concurrency at scale |
| Safety/approval | 4 | Injection quarantine, exact payload, one-time token, idempotency | Enterprise auth, SoD, security review |
| Persistence | 4 | SQLite case/index/audit/idempotency + migrations + health | PostgreSQL/encryption/backup/HA |
| Observability/reliability | 4 | Per-case AI Decision Log, hash-chained audit, JSON logs, metrics, retry/breaker/cache runner | OpenTelemetry/SIEM backend, alerting, retention, SLO/load test |
| API/UI V2 | 4 | 39 routes, 19-route sales facade và browser E2E intake → mock execution | Enterprise auth và formal accessibility audit |
| Independent RAG MCP | 4 | Official MCP transport, 4 read tools, persistent index, ACL/version/effective filter, service auth và transport E2E | OAuth/mTLS, semantic model benchmark, production vector DB và approved real corpus |
| Evaluation | 4 | 40 business + 25 security + 20 reliability cases | De-identified real cases và independent red-team |

Tổng readiness: **49/65 (75,4%)** cho target production. Local/sandbox MVP chạy end-to-end; không hạng mục nào đạt `5` vì chưa có hệ thống, dữ liệu và phê duyệt thật.

## Quality snapshot

| Chỉ số | Kết quả synthetic |
|---|---:|
| Unit/integration/contract/API/UI/MCP tests | 172 passed |
| Coverage toàn repo | 92% |
| Business golden cases | 40/40 |
| Security cases | 25/25 |
| Reliability cases | 20/20 |
| Intent accuracy | 100% |
| Product entity accuracy | 100% |
| Retrieval Hit@3 | 100% |
| OOS precision | 100% |
| Eligibility accuracy | 100% |
| Unsafe approval rate | 0% |
| Browser console error/warning | 0 |
| AI log raw PII recorded | false |

Các tỷ lệ 100% chỉ phản ánh bộ synthetic nhỏ, deterministic và do repo kiểm soát. Không dùng snapshot này làm cam kết pilot trước SME adjudication, shadow evaluation và security review trên dữ liệu được duyệt.

## Kết luận

- **Sẵn sàng:** demo/local sandbox, review kiến trúc, chạy regression tự động và tích hợp thử qua adapter.
- **Chưa sẵn sàng:** quyết định tín dụng thật, gửi thông tin khách hàng thật hoặc kết nối production không có gateway/phê duyệt.
- **Điều kiện lên pilot:** catalog/policy đã ký duyệt, SSO/IAM và CRM sandbox thật, dữ liệu case đã de-identify, semantic retrieval benchmark, telemetry tập trung và security sign-off.
