# 11 — Safety, Evidence, Approval and Action Execution

## 1. Objective

Defense in depth cho input, context, retrieval, output và tools; external action chỉ thực thi đúng payload RM đã duyệt.

## 2. Input safety

- Authentication/session validation.
- RBAC/ABAC before context/data retrieval.
- File type/size/malware checks.
- Prompt injection detection on user/document text.
- PII classification/minimization.
- Rate limit/abuse detection.

Retrieved documents are untrusted data. Their text cannot change system/tool policy.

## 3. Evidence validation

Validation layers:

1. Source identity/version/effective status.
2. Exact quote presence at location.
3. Deterministic value/unit match.
4. Semantic support score for non-numeric claims.
5. Optional binary judge for unresolved support.

Thresholds configurable/evaluated. Numeric/fee/limit claims require deterministic exact match regardless semantic score.

Invalid evidence behavior:

- Remove/block unsupported claim from customer-facing output.
- Mark `hallucination_flag`.
- Re-retrieve once if source version valid.
- Then pending review/failure; no write action.

## 4. Tool allowlist

Source: `contracts/tool_contracts.json`.

Gateway checks:

- Caller identity/module.
- Tool allowlist.
- Input schema.
- Customer/data scope.
- Risk level.
- Approval required.
- Idempotency key.
- Timeout/retry policy.

Product/Intent/Planner calling write tool must produce `TOOL_PERMISSION_DENIED` and high-severity audit event.

## 5. Approval payload

Approval preview includes:

- Case/customer.
- Exact action list.
- Recipient/target system.
- Payload diff.
- Evidence/risk summary.
- Reversibility.
- Expiry.

Signed token claims:

```json
{
  "token_id": "uuid",
  "case_id": "CASE-1",
  "approver_id": "RM-999",
  "permissions": ["create_crm_case"],
  "payload_hash": "sha256",
  "issued_at": "timestamp",
  "expires_at": "timestamp",
  "nonce": "random",
  "one_time_use": true
}
```

If payload changes after approval, token invalid.

## 6. Approval rules

- Approver must own/have scope for case.
- Separation of duties configurable for high-risk actions.
- Blocking eligibility prevents product-opening/credit write.
- `pending_information` may allow approved follow-up draft/send only if policy permits; default no external write in MVP.
- Rejected/expired/consumed token cannot execute.
- Approval never inferred from chat text alone; UI/API explicit action required.

## 7. Action Executor

Execution sequence:

```text
verify auth/session
→ load latest state
→ verify token signature/expiry/nonce/one-time use
→ recompute payload hash
→ verify evidence + no blocking + permissions
→ acquire idempotency lock
→ call external adapter
→ query outcome if timeout
→ persist result/audit
→ consume token
```

Executor cannot modify approved payload except adapter-level transport formatting.

## 8. PII/logging policy

Never log:

- Raw identity numbers.
- Account/card/PIN.
- Full email body with sensitive data.
- Approval token.
- Model/API secrets.

Log hashes, redacted IDs, stable event codes and metadata needed for audit.

## 9. Proposed code artifacts

| File | Responsibility |
|---|---|
| `app/safety/input_guardrails.py` | Injection/PII/file policy |
| `app/safety/evidence.py` | Hybrid validation |
| `app/safety/tool_gateway.py` | Allowlist/schema/scope |
| `app/approval/models.py` | Approval/token/payload models |
| `app/approval/service.py` | Issue/verify/invalidate |
| `app/actions/executor.py` | Guarded execution |
| `app/actions/idempotency.py` | Lock/result store |
| `app/security/redaction.py` | Structured sanitization |

## 10. Tests

- Prompt injection in uploaded document blocked/isolated.
- Product module cannot call CRM write.
- Token wrong case/RM/payload rejected.
- Expired/reused token rejected.
- Payload edit invalidates token.
- Blocking Legal prevents execution.
- Concurrent approve calls produce one external action.
- Tool timeout checks status before retry.
- PII absent from logs.
- Unsupported product/legal claim cannot reach approval.

## 11. Acceptance

- Unsafe external action rate = 0.
- Cross-user/customer data leakage = 0.
- Duplicate side effect under replay/concurrency = 0.
- 100% important displayed claims have valid evidence.

