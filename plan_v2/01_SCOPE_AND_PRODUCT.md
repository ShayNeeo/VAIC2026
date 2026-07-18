# 01 — Product Scope, Users and Outcomes

## 1. Job-to-be-done

Khi RM đang xử lý một doanh nghiệp, hệ thống phải tự nhận biết context hiện tại, hiểu yêu cầu ngắn hoặc mơ hồ, tái sử dụng dữ liệu/kết quả đã có và chuẩn bị các bước tiếp theo mà không tạo công việc trùng.

## 2. Primary user journeys

### Journey A — Kiểm tra hồ sơ trong case đang mở

Input: RM đang mở `COMP-ABC / Working Capital` và nói “Kiểm tra còn thiếu gì”.

Expected:

- Tự lấy customer/case/product từ workspace.
- Không hỏi lại khách hàng nào/sản phẩm nào.
- Kiểm tra documents + KYC/UBO.
- Trả checklist và evidence.
- Không tạo task nếu task tương đương đã tồn tại.

### Journey B — Nhu cầu đa sản phẩm

Input: “Khách muốn chi lương, gom dòng tiền và có hạn mức khi thiếu hụt”.

Expected:

- Tách multi-intent.
- Product RAG tìm Payroll, Cash Management, Working Capital.
- Legal chặn riêng nhánh tín dụng nếu thiếu UBO/BCTC.
- Giữ các nhánh không bị chặn.

### Journey C — Resume sau bổ sung tài liệu

Input: UBO được upload vào case pending information.

Expected:

- Tính impact từ document type.
- Chạy lại Legal/Evidence/Operations liên quan.
- Không chạy lại intent/product nếu input không đổi.
- Cập nhật task/email hiện có thay vì tạo mới.

### Journey D — External action

Input: RM bấm Approve.

Expected:

- Hiển thị payload diff.
- Token chứa payload hash và expiry.
- Executor kiểm tra RBAC, evidence, blocking, idempotency.
- Ghi audit; không thực thi lần hai.

## 3. Scope MVP V2

- Employee/workspace context collection.
- Customer/case/document context loading.
- Intent/entity structured extraction.
- Slot auto-fill và confidence policy.
- Product RAG có version/citation.
- Eligibility rules + synthetic legal policies.
- Workflow state machine + partial resume.
- Checklist/email/case/task drafts.
- Task deduplication và artifact reuse.
- RM approval + mock external executor.
- API/UI context preview và correction.
- Evaluation + observability tối thiểu.

## 4. Out of scope MVP

- Tự phê duyệt tín dụng.
- Gửi email thật không qua RM.
- Core Banking write thật.
- Fine-tuning model.
- Chấm hiệu suất nhân viên từ behavioral context.
- Lưu mọi hội thoại vô thời hạn.
- Autonomous agent tự mở rộng tool/action.

## 5. Success metrics

| Metric | MVP target | Pilot target |
|---|---:|---:|
| Intent accuracy | ≥ 90% synthetic/golden | ≥ 95% real sample |
| System slot auto-fill accuracy | ≥ 98% | ≥ 99% |
| Unnecessary clarification rate | < 10% | < 5% |
| Duplicate task creation | 0% | 0% |
| Unsupported important claims | 0% | 0% |
| Unsafe external actions | 0% | 0% |
| Correct resume node selection | ≥ 90% | ≥ 95% |
| P95 non-LLM workflow latency | < 2s | < 2s |
| P95 complete analysis | < 30s | configurable SLO |

## 6. Product principles

- Context first, prompt second.
- Prefer retrieving existing facts over asking.
- Defer questions not required for current step.
- Show the system’s understanding and provenance.
- Let users correct context without restarting.
- Draft before action; approve before write.
- Reuse before recompute; update before create.
- Deterministic rules own high-risk decisions.

