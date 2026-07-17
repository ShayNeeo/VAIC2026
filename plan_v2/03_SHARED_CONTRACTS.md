# 03 — Shared Contracts

## 1. Contract files

- `contracts/shared_case_state.schema.json`
- `contracts/context_snapshot.schema.json`
- `contracts/intent_result.schema.json`
- `contracts/tool_contracts.json`

Các file JSON là source of truth. Module plan chỉ giải thích cách dùng.

## 2. Versioning

- `schema_version` bắt buộc ở top-level.
- Patch: thêm mô tả/constraint không phá compatibility.
- Minor: thêm optional field.
- Major: đổi required field, enum hoặc semantics.
- State lưu trong DB phải giữ version để migration.

## 3. Provenance contract

Mọi field được auto-fill hoặc suy luận phải dùng `ResolvedValue`:

```json
{
  "value": "COMP-ABC",
  "source_type": "workspace",
  "source_id": "selected_customer_id",
  "confidence": 1.0,
  "confirmed": true,
  "observed_at": "2026-07-17T10:00:00Z",
  "expires_at": null
}
```

`source_type` chỉ dùng:

```text
user_explicit | workspace | sso | iam | crm | document
| workflow | conversation_confirmed | cache | llm_inference
```

## 4. Evidence contract

Một claim quan trọng cần:

- `claim_id` duy nhất.
- `agent/module` tạo claim.
- `claim` dạng user-readable.
- `source_document_id` và `source_version`.
- `section/page`.
- `quote`.
- `validation_method`.
- `is_valid` và `validation_score`.

Không dùng URL hoặc filename đơn lẻ làm identity tài liệu.

## 5. Error contract

Mọi service/tool error được chuẩn hóa:

```json
{
  "error_code": "CRM_TIMEOUT",
  "message": "Không thể lấy hồ sơ doanh nghiệp",
  "retryable": true,
  "safe_to_retry": true,
  "correlation_id": "trace-id",
  "details": {}
}
```

Không trả stack trace hoặc secret qua API.

## 6. State mutation rules

- Node chỉ sửa section do mình sở hữu.
- Context node: `context.*`.
- Intent node: `intent_result`.
- Product node: `product_result`, product evidences.
- Eligibility node: `eligibility_result`, legal evidences.
- Operations node: `operations_result`.
- Approval node: `approval`.
- Workflow engine: `workflow`, `status`, audit events.

Cross-section update phải qua workflow command/event, không sửa trực tiếp từ agent.

## 7. Contract tests

Phải có:

- Valid minimal payload.
- Valid full payload.
- Unknown enum bị reject.
- Missing required ID bị reject.
- Confidence ngoài `[0,1]` bị reject.
- External action thiếu idempotency/approval bị reject.
- Old compatible version migration test.
- API response validate cùng schema.
