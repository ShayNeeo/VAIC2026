# 17 — Assumptions, Data Requirements and Open Questions

## 1. Purpose

Tách rõ điều đã biết, thiết kế đề xuất và dữ liệu/quyết định cần chủ hệ thống xác nhận. AI không được biến giả định dưới đây thành fact.

## 2. Assumption register

| ID | Assumption | Impact if false | Owner to confirm | Status |
|---|---|---|---|---|
| ASM-001 | Workspace cung cấp selected customer/case/task | Phải hỏi nhiều hơn hoặc tích hợp UI khác | Product/UI owner | Open |
| ASM-002 | IAM cung cấp customer/branch scope | Không thể bảo đảm data isolation | Security/IT | Open |
| ASM-003 | CRM có read APIs và stable IDs | Context/customer mapping không ổn định | CRM team | Open |
| ASM-004 | CRM/task supports idempotency or status query | Có nguy cơ duplicate write | Integration team | Open |
| ASM-005 | Product/legal docs có version/effective date | Không kiểm soát policy stale | Data owners | Open |
| ASM-006 | DMS có document type/status metadata | Resume/checklist khó chính xác | DMS team | Open |
| ASM-007 | RM approval can be represented digitally | Executor chỉ dừng ở draft | Governance | Open |
| ASM-008 | Internal model gateway allows structured output | Cần fallback parser/provider | AI platform | Open |

## 3. Data required

| Dataset | Minimum for MVP | Required for pilot | Owner |
|---|---|---|---|
| Product catalog | Synthetic 5–10 products | Current real catalog + metadata/version | Product |
| Product policies | Synthetic rules | Approved policy versions | Product/Risk |
| Legal/KYC/AML | Synthetic 3–5 rules | Current policies + rule owner | Legal/Compliance |
| SOP/SLA | Synthetic templates | Approved operational SOP/calendar | Operations |
| Employee/IAM | Mock roles/scopes | SSO/IAM integration spec | IT/Security |
| CRM profiles/cases | Synthetic companies | Sandbox schema/API | CRM team |
| Historical conversations | Curated synthetic | De-identified consented samples | Business/Data |
| Evaluation labels | Initial golden set | Dual-reviewed high-risk labels | SMEs |

## 4. Open business questions

| ID | Question | Affects | Priority |
|---|---|---|---|
| BQ-001 | Intent taxonomy nào phản ánh đúng công việc RM? | Intent/eval | High |
| BQ-002 | Field nào bắt buộc ở từng workflow stage? | Clarification | High |
| BQ-003 | Khi CRM và tài liệu mâu thuẫn, nguồn nào thắng? | Context/legal | High |
| BQ-004 | Action nào RM tự approve, action nào cần cấp khác? | HITL | High |
| BQ-005 | Pending information có được phép gửi email sau RM approve không? | Safety/ops | High |
| BQ-006 | Validity window của KYC/BCTC/task result? | Cache/reuse | Medium |
| BQ-007 | SLA/VIP rules và business calendar? | Operations | Medium |
| BQ-008 | Khi nào task được update thay vì create revision? | Dedup | Medium |

## 5. Open technical questions

| ID | Question | Affects | Priority |
|---|---|---|---|
| TQ-001 | Vector DB/embedding/model gateway chuẩn nội bộ? | RAG/deploy | High |
| TQ-002 | Event/webhook có sẵn cho document/CRM/IAM changes? | Resume/cache | High |
| TQ-003 | Required tenant/branch isolation model? | Storage/RBAC | High |
| TQ-004 | Audit retention/encryption/tamper requirements? | Governance | High |
| TQ-005 | Existing frontend stack and session context API? | UI/context | Medium |
| TQ-006 | Observability backend approved? | Ops | Medium |
| TQ-007 | On-prem/cloud/data egress restrictions? | Model/RAG | High |

## 6. Decision gates

### Before coding MVP

- Accept V2 contracts and status enum.
- Approve synthetic data scope.
- Select intent taxonomy owner.

### Before pilot integration

- Resolve IAM/customer scope.
- Provide sandbox CRM/DMS/task specs.
- Approve real document ingestion and retention.
- Approve model/data egress policy.
- Define approval authority matrix.

### Before production

- Close all High open questions.
- Meet module 15 pilot gates.
- Complete security/privacy/legal reviews.
- Verify backup/DR/SLO/on-call ownership.

## 7. How AI should handle unresolved items

- Use explicit interface/mock and label `ASSUMPTION` or `DATA REQUIRED`.
- Do not invent endpoint, policy, SLA or permission behavior.
- Record chosen temporary default in `PROGRESS.md` decision/deviation log.
- Keep adapter replaceable and core logic independent.

