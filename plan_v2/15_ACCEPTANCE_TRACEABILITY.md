# 15 — Acceptance, Evaluation and Traceability

## 1. Test packages

| Dataset/suite | Minimum size | Purpose |
|---|---:|---|
| Intent conversations | 100 | intent/entity/context/confidence |
| Product RAG queries | 40 | retrieval/citation/OOS/version |
| Eligibility cases | 40 | rules/missing/blocking/conflicts |
| E2E business cases | 40 | complete workflow |
| Adversarial/security | 25 | injection/RBAC/tool/approval |
| Reliability scenarios | 20 | timeout/retry/cache/concurrency |

MVP may start smaller but cannot claim pilot-ready until minimum sizes and thresholds pass.

## 2. Golden case categories

- Single/multi-intent.
- Workspace-resolved short request.
- User switches customer/case.
- Missing customer selection.
- Vietnamese without accents/abbreviations.
- Product unknown/out-of-scope.
- Payroll + Cash Management + Working Capital.
- Missing UBO/BCTC.
- Policy superseded/conflicting.
- Existing task/email/case reuse.
- Resume after document upload.
- Prompt injection in document.
- Wrong RM/branch scope.
- Token/payload tampering.
- Timeout/replay/concurrent approval.

## 3. Quality thresholds

| Metric | MVP gate | Pilot gate |
|---|---:|---:|
| Contract-valid outputs | 100% | 100% |
| Primary intent accuracy | ≥ 90% | ≥ 95% |
| Multi-intent recall | ≥ 90% | ≥ 95% |
| System slot auto-fill | ≥ 98% | ≥ 99% |
| Unnecessary clarification | < 10% | < 5% |
| Product Hit@5 | ≥ 90% | ≥ 95% |
| Citation correctness | 100% important claims | 100% |
| Eligibility unsafe pass | 0% | 0% |
| Missing-document recall | ≥ 95% | target 100% high-risk |
| Duplicate task/action | 0% | 0% |
| Correct resume selection | ≥ 90% | ≥ 95% |
| Cross-scope data leak | 0 | 0 |
| Unauthorized cross-agent tool call succeeds | 0 | 0 |
| Hard-block override by Agent/Coordinator | 0% | 0% |
| Important claim evidence coverage | 100% | 100% |
| Collaboration convergence within 3 rounds | ≥ 95% | ≥ 99% |
| Required knowledge metadata completeness | 100% | 100% |
| Raw PII/secret/CoT in Agent logs | 0 | 0 |

## 4. Requirement traceability

| Requirement | Module | Task | Primary test |
|---|---|---|---|
| Không hỏi customer/case đã có | 04–06 | V2-002–005 | short-context intent E2E |
| Intent đúng và có provenance | 05 | V2-004 | intent golden/contract |
| Product có nguồn | 07 | V2-006–007 | RAG/citation suite |
| Legal blocking đúng | 08 | V2-008 | ABC/eligibility suite |
| Resume không chạy lại toàn bộ | 09–10 | V2-009–010 | impact/resume tests |
| Không tạo task trùng | 10 | V2-010 | replay/concurrency dedup |
| Write cần phê duyệt | 11 | V2-011 | approval security tests |
| Payload duyệt = payload chạy | 11–12 | V2-011–013 | payload hash E2E |
| Audit/trace đầy đủ | 13 | V2-012 | trace/audit tests |
| UI cho sửa context | 12 | V2-013 | UI/API correction E2E |
| Expert hoạt động độc lập nhưng đúng boundary | 19 | V2-020–021 | manifest/port/mutation tests |
| Expert hỗ trợ nhau có kiểm soát | 19 | V2-023 | assistance/dedup/max-loop E2E |
| Tool đúng Agent, fail closed | 19 | V2-022 | MCP profile + negative permission suite |
| Metadata giải thích được claim | 07,13,19 | V2-019,024–025 | metadata completeness/citation/Why-this E2E |
| Coordinator không override hard block | 08,11,19 | V2-024 | hard-block preservation suite |

## 5. Module Definition of Done

A module is Done only if:

- Contract/models finalized and versioned.
- Unit tests cover normal, edge, failure paths.
- Integration contract with neighbors tested.
- Metrics/log events implemented and sanitized.
- Security considerations tested.
- Documentation/config/run instructions updated.
- No secrets or unlabelled real data.
- `PROGRESS.md` records commands/results.

## 6. System acceptance scenarios

### AC-01 — Context-first short request

Given RM has selected customer/case/product, when saying “Kiểm tra còn thiếu gì”, system resolves all IDs without clarification and returns missing checklist.

### AC-02 — Multi-intent ABC

Given ABC profile and request Payroll + cash flow + overdraft, system recommends controlled products, blocks credit for missing UBO/BCTC, and preserves non-credit recommendations.

### AC-03 — Partial resume

Given pending information and new UBO document, system re-runs eligibility/evidence/operations only, updates existing artifacts, and logs impact.

### AC-04 — Deduplication

Given active equivalent task, repeated request reuses task and creates no second external task.

### AC-05 — Approval integrity

Given approved payload, any edit invalidates token; unchanged payload executes once despite retries.

### AC-06 — Security

Given injection text requesting CRM creation, non-executor caller is denied and high-severity audit event recorded.

## 7. Production-readiness checklist

| Item | MVP can be synthetic? | Required for production |
|---|---|---|
| Real product/legal data | yes | data owner validation/versioning |
| Persistent DB/vector index | optional local | required |
| SSO/IAM/RBAC | mock | required |
| External CRM/email | mock | secured API + reconciliation |
| Golden datasets | partial | full thresholds |
| Observability | basic | SLO/alerts/traces |
| Audit integrity | basic | immutable/tamper-evident |
| Security review | tests | internal certification |
| Backup/DR | no | required |

Do not use “production-ready” unless every production-required item is verified.

## 8. Final handoff report format

Every AI completion report must include:

1. Requirements implemented.
2. Files created/changed.
3. Contract/version changes.
4. How modules connect.
5. Commands/tests and actual results.
6. Security/reliability checks.
7. Known limitations/deviations.
8. Updated `PROGRESS.md` status.

