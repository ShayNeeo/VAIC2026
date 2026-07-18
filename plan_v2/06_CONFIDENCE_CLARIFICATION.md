# 06 — Slot Auto-Fill, Confidence and Clarification

## 1. Objective

Giảm câu hỏi lặp lại bằng cách tự lấy dữ liệu từ context/tools, trì hoãn field chưa cần, và chỉ hỏi khi thiếu dữ liệu làm thay đổi quyết định.

## 2. Slot resolution order

```text
user_explicit
→ workspace
→ workflow/case state
→ CRM/DMS
→ conversation_confirmed
→ valid cache
→ safe deterministic derivation
→ llm_inference
→ unresolved
```

Không gọi LLM để đoán system identifiers nếu có resolver/tool.

## 3. Required-now versus required-later

Mỗi intent slot có:

- `required_for_understanding`.
- `required_for_retrieval`.
- `required_for_eligibility`.
- `required_for_external_action`.

Ví dụ `requested_amount` có thể không cần để tìm sản phẩm, nhưng bắt buộc trước khi tạo một số credit case. Hệ thống phải tiếp tục các bước an toàn và chỉ hỏi ở bước cần.

## 4. Confidence calculation

Field confidence dựa trên nguồn:

| Source | Base confidence |
|---|---:|
| IAM/SSO authenticated | 1.00 |
| Workspace selected ID | 1.00 |
| Fresh CRM/DMS | 0.98 |
| User explicit current message | 0.95 |
| Workflow state | 0.95 |
| Conversation confirmed | 0.90 |
| Fresh cache | 0.85 |
| Deterministic derivation | 0.85 |
| LLM inference | ≤ 0.70 |

Adjustments:

- Stale source penalty.
- Conflict penalty.
- Entity resolver match score.
- Missing permission sets confidence to 0 and blocks use.

Overall confidence không được dùng thay field-level confidence cho external action.

## 5. Decision matrix

| Field confidence | Risk/impact | Action |
|---:|---|---|
| ≥ 0.90 | low | continue |
| 0.70–0.89 | low | continue + visible assumption |
| < 0.70 | low, not required now | defer |
| < 0.70 | medium/high required now | clarify |
| any | external write | preview + explicit approval |
| conflict | customer/case/recipient | confirmation required |

## 6. Clarification selection

Nếu phải hỏi:

1. Tạo danh sách unresolved slots có decision impact.
2. Xếp hạng theo information gain × risk × downstream blocking.
3. Hỏi tối đa một câu mỗi lượt.
4. Dùng lựa chọn cụ thể khi có 2–3 hypotheses.
5. Không hỏi field có thể lấy bằng read tool.
6. Lưu answer thành `conversation_confirmed` với source message.

Không dùng câu chung “Vui lòng cung cấp thêm thông tin”.

## 7. Safe progress while clarifying

Workflow có thể:

- Tìm product candidates khi chưa có amount.
- Kiểm tra hồ sơ đã có.
- Chuẩn bị checklist.
- Không được tạo payload cuối hoặc gửi ra ngoài khi field quyết định còn thiếu.

## 8. Correction handling

Khi user sửa context:

- Ghi event `context_corrected`.
- Mark value cũ superseded, không xóa audit.
- Tính impacted nodes.
- Invalidate cache/artifacts phụ thuộc.
- Resume workflow từ node sớm nhất bị ảnh hưởng.

## 9. Proposed code artifacts

| File | Responsibility |
|---|---|
| `app/intent/slot_registry.py` | Slot requirements per intent/stage |
| `app/intent/slot_resolver.py` | Resolution order/tools |
| `app/intent/confidence.py` | Field confidence/calibration |
| `app/intent/clarification.py` | Question ranking/generation |
| `app/intent/corrections.py` | Correction and invalidation event |

## 10. Tests

- Customer/case auto-filled from workspace.
- CRM tool used before asking user.
- Amount deferred during product search.
- High-impact customer conflict asks confirmation.
- Low-confidence optional field does not block.
- Only one clarification question selected.
- User answer stored as confirmed provenance.
- Correction invalidates only impacted results.

## 11. Acceptance

- Unnecessary clarification rate < 10% MVP, < 5% pilot.
- System field auto-fill accuracy ≥ 98%.
- No external action uses a required field sourced only from unconfirmed LLM inference.

