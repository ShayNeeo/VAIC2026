# 04 — Employee, Workspace and Case Context

## 1. Objective

Tự động xác định nhân viên đang làm gì, cho khách hàng nào, trong case/task nào để giảm hỏi lại và tránh dùng sai context.

Upstream: SSO/IAM, Workspace, CRM, DMS, Task system.  
Downstream: Intent Engine, Workflow Router, RBAC, UI Context Header.

## 2. Context layers

| Layer | Required fields | Source | Default freshness |
|---|---|---|---|
| Employee | employee_id, role, org unit | SSO/HRIS | session/24h |
| Permission | scopes, managed customers | IAM | 5m |
| Workspace | screen, selected customer/case/task | UI session | realtime |
| Customer | profile, segment, KYC, products | CRM | 5m |
| Workflow | current node, open questions, tasks | State DB | realtime |
| Documents | type, version, status, access | DMS | 5m |
| Conversation | goal, confirmed facts, rejected assumptions | State DB | session |
| Preference | language, output format, tone | User settings | 30d |

Freshness phải configurable theo data owner; không hard-code trong service.

## 3. Context collection sequence

```text
Authenticated employee
→ load IAM scope
→ read workspace selection
→ validate employee can access selected customer/case
→ load active case/customer/task/doc metadata in parallel
→ load confirmed conversation facts
→ normalize + timestamp + provenance
→ context conflict check
→ return ContextSnapshot
```

Nếu selected customer không thuộc scope, dừng với `CONTEXT_ACCESS_DENIED`; không fallback sang customer gần nhất.

## 4. Precedence rules

Khi cùng field có nhiều giá trị:

1. `user_explicit` trong message mới và hợp lệ.
2. `workspace` selection hiện tại.
3. `crm/document/workflow` còn fresh.
4. `conversation_confirmed`.
5. `cache` còn TTL.
6. `llm_inference`.

Ngoại lệ: permission/IAM luôn thắng user input. Người dùng không thể tự khai báo quyền.

## 5. Conflict model

```json
{
  "field": "customer_id",
  "candidates": [
    {"value": "COMP-ABC", "source_type": "workspace"},
    {"value": "COMP-XYZ", "source_type": "user_explicit"}
  ],
  "resolution": "user_explicit",
  "decision_impact": "high",
  "requires_confirmation": true
}
```

High-impact conflicts: customer, case, recipient, product with external action. Phải hiển thị/cần xác nhận trước write.

## 6. Context minimization

Context Assembler nhận `IntentPreparationRequest` và chỉ lấy field cần cho intent taxonomy hiện có. Không gửi:

- Toàn bộ danh sách khách hàng RM quản lý.
- Toàn bộ lịch sử email.
- Raw identity document.
- Nội dung case khác.
- Preference/behavior không liên quan.

LLM context gồm summary có cấu trúc, không phải dump database.

## 7. Proposed code artifacts

| File | Responsibility |
|---|---|
| `app/context/models.py` | ContextSnapshot, ResolvedValue, Conflict |
| `app/context/employee_service.py` | Employee/IAM context |
| `app/context/workspace_service.py` | Selected screen/customer/case/task |
| `app/context/customer_service.py` | CRM profile adapter facade |
| `app/context/conversation_state.py` | Confirmed/rejected/open questions |
| `app/context/assembler.py` | Merge, minimize, provenance |
| `app/context/freshness.py` | TTL/stale rules |
| `app/context/conflicts.py` | Conflict detection/resolution |
| `app/integrations/sso.py` | SSO adapter |
| `app/integrations/iam.py` | Permission adapter |
| `app/integrations/crm.py` | CRM read adapter |

## 8. API/internal contract

Input:

```json
{
  "employee_id": "RM-999",
  "session_id": "SESSION-1",
  "message_id": "MSG-1",
  "message": "Kiểm tra còn thiếu gì"
}
```

Output: `ContextSnapshot` mapped to `state.context`. Every system-resolved field must use provenance contract from module 03.

## 9. Failure/fallback

| Failure | Behavior |
|---|---|
| Workspace context unavailable | Use explicit IDs in request; otherwise clarification |
| CRM timeout | Use fresh cache; else mark stale and do not make eligibility decision |
| IAM timeout | Fail closed for sensitive reads/writes |
| DMS timeout | Return document status unknown; workflow pending information |
| Conversation state corrupt | Start clean conversation state, preserve case state |

## 10. Tests

- Selected case auto-fills customer/product.
- User explicitly switches customer; conflict surfaced.
- Unauthorized selected customer rejected.
- Stale CRM profile not used for final eligibility.
- Two sources same value deduplicated.
- LLM inference never overrides confirmed/system value.
- Context contains no unrelated customer data.
- Workspace unavailable leads to one targeted missing slot, not generic question.

## 11. Acceptance

- System IDs auto-fill accuracy ≥ 98%.
- Cross-customer leakage = 0.
- Context source/freshness present for every auto-filled field.
- “Khách hàng nào/case nào?” không được hỏi khi workspace đã có selection hợp lệ.

