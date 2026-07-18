# SHB Multi-Agent Workflow — Diagram-to-Code Mapping

Ngày: 2026-07-18. Đối chiếu sơ đồ "SHB Multi-Agent Workflow: Corporate Product
Eligibility & Onboarding" do người dùng cung cấp với triển khai thực tế trong
`app/workflow/engine.py` và các module liên quan, sau khi bổ sung
`app/workflow/router.py` và `app/workflow/risk_gate.py`.

## 1. Bảng đối chiếu node

| Node trong sơ đồ | Thành phần trong code | Trạng thái |
|---|---|---|
| RM nhập nhu cầu và hồ sơ doanh nghiệp | `POST /api/v2/sales-cases`, `POST /api/v2/cases` (`app/api/v2/router.py`) | Khớp |
| Input Validator & Data Normalizer | `screen_input()` (`app/safety/input_guardrails_v2.py`) + `IntakeService`/`ContextAssembler` | Khớp |
| Complexity Router | `app/workflow/router.py::ComplexityRouter` (tách khỏi `engine.py`, trước đây là 1 static method nội bộ) | Khớp — component riêng, có test độc lập |
| Câu hỏi đơn giản → Single-agent/RAG | `V2WorkflowEngine.run()` nhánh `not is_complex`: gọi thẳng `ProductService.recommend()`, log `mode="single_agent_rag"` | Khớp |
| Planner Agent → dependency graph | `PlannerService.plan()` → `ExecutionPlan.steps` | Khớp |
| Product / Compliance / Operations Agent | `ProductService`, `EligibilityEngine`, `OperationsService` | Khớp về vai trò; **không song song thật** — xem mục 3 |
| Evidence Validator | `V2WorkflowEngine._analysis()` khối `if start_index <= 2` | Khớp |
| Risk & Guardrail Gate | `app/workflow/risk_gate.py::RiskGuardrailGate`, gọi qua `_apply_risk_gate()` ngay sau Evidence Validator | Khớp — mới thêm, xem mục 2 |
| Đủ dữ liệu → Đề xuất action | `RiskGateDecision.outcome == "approve"` → `CaseStatus.PENDING_APPROVAL` | Khớp |
| Thiếu dữ liệu → Hỏi bổ sung | `RiskGateDecision.outcome == "need_information"` → `CaseStatus.PENDING_INFORMATION` | Khớp |
| Rủi ro cao → Human review | `RiskGateDecision.outcome == "need_review"`, `risk_level == "high"` → `CaseStatus.PENDING_REVIEW` | Khớp — trước đây gộp chung với "thiếu dữ liệu", không phân biệt được |
| Create case/task/report | `OperationsService.prepare()` (checklist/email/task/CRM draft), chạy cho mọi outcome | Khớp |
| Audit log + Dashboard | `state.ai_decision_log`, `state.audit_events`, UI tab AI log/Audit (`app/static/app.js`) | Khớp |

## 2. Risk & Guardrail Gate — nguồn gốc rule

`RiskGuardrailGate` **không phát minh rule rủi ro mới**. Nó nối lại taxonomy đã
có sẵn nhưng bị bỏ phí trong `plan_v2/08_ELIGIBILITY_LEGAL.md` mục 5
(`passed / failed / pending_information / pending_review`) và
`app/eligibility/engine.py::_aggregate()` (đã implement đúng thứ tự ưu tiên
`pending_review > failed > pending_information > passed`), cộng thêm kết quả
Evidence Validator:

| `eligibility_result.overall_status` hoặc evidence | `outcome` | `risk_level` |
|---|---|---|
| có evidence `is_valid=false` (bất kể eligibility) | `need_review` | `high` |
| `passed` | `approve` | `none` |
| `pending_information` | `need_information` | `none` |
| `failed` (hard block, vd nợ xấu, doanh thu dưới ngưỡng) | `need_review` | `high` |
| `pending_review` (xung đột chính sách/PEP/AML/live-check lỗi) | `need_review` | `high` |
| giá trị lạ không nhận diện được | `need_review` | `high` (fail-closed mặc định) |

Trước đây `engine.py` gộp `failed`/`pending_review`/evidence-invalid vào chung
một nhánh `else → PENDING_REVIEW` mà không phân biệt lý do — RM thấy cùng một
trạng thái cho "thiếu tài liệu nhẹ" lẫn "vi phạm chính sách tín dụng nghiêm
trọng". Gate mới log riêng (`component="RiskGuardrailGate"`), lưu
`state.risk_gate_result` (field mới trong `SharedCaseState`, xem
`plan_v2/contracts/shared_case_state.schema.json`) và UI hiển thị banner đỏ
riêng khi `risk_level == "high"` (`app/static/app.js::riskGateBanner`).

## 3. Vì sao Product/Compliance/Operations không chạy song song thật

Sơ đồ vẽ 3 ô cạnh nhau hội tụ vào Evidence Validator, gợi ý song song. Trong
code, `Compliance` (Eligibility Engine) **cần `product_ids` do Product trả
về** làm input bắt buộc (`app/eligibility/engine.py::evaluate(product_ids, ...)`)
— không thể chạy trước hoặc đồng thời với Product mà không có dữ liệu đó.
`Operations` cũng cần `eligibility_result` để biết checklist/action nào cần
soạn. Đây là ràng buộc dữ liệu thật, không phải giới hạn kỹ thuật.

`plan_v2/09_WORKFLOW_ORCHESTRATION.md` mục 4 (tài liệu spec gốc của chính hệ
thống này) đã nêu rõ: *"Parallelize Product candidates/legal checks only when
inputs independent."* — tức bản thân spec cũng không yêu cầu song song vô
điều kiện. Quyết định giữ tuần tự (Product → Compliance → Evidence → Operations)
là lựa chọn kỹ thuật có chủ đích, khớp với spec gốc, không phải thiếu sót khi
đọc sơ đồ. Nếu người dùng vẫn muốn song song hoá thật (vd. chạy `asyncio.gather`
cho các bước không phụ thuộc lẫn nhau trong nội bộ mỗi agent), đây là công việc
riêng cần xác nhận thêm vì có thể đổi thứ tự log/audit hiện tại.

## 4. Lỗi Gemini/tokens phát hiện khi verify — đã sửa (2026-07-18, đợt 2)

Phát hiện 2 lỗi run-time không liên quan đến Complexity Router/Risk Gate, ở
nhánh embedding Gemini mà một phiên khác đang phát triển song song. Theo yêu
cầu, đã sửa dứt điểm cả hai:

- **Model Gemini sai tên, đã retired**: `CachedGeminiEmbedding` gọi
  `models/text-embedding-004:embedContent` → `404 NOT_FOUND`. Gọi trực tiếp
  `GET v1beta/models` với đúng `GOOGLE_API_KEY` trong `.env` xác nhận model
  còn hoạt động là `gemini-embedding-001`/`gemini-embedding-2-preview`/
  `gemini-embedding-2`. Đã sửa tên model + thêm `outputDimensionality` để
  vector trả về đúng chiều đã khai báo (`app/knowledge/index.py`,
  `services/rag_mcp/embedding.py`).
- **`tokens`/`fold` bị xoá nhầm**: `services/rag_mcp/service.py` gọi
  `tokens(...)` ở dòng 241/256 nhưng bản `embedding.py` sau khi thêm Gemini
  không còn định nghĩa hàm này → `NameError`, chặn toàn bộ retrieval thật.
  Đã khôi phục `fold()`/`tokens()`/`STOPWORDS` trong `embedding.py` và thêm
  `tokens` vào import của `service.py`.
- **Phát hiện thêm khi test trực tiếp API**: sau khi sửa tên model, gọi thật
  vẫn lỗi — nhưng lần này là `429 RESOURCE_EXHAUSTED: Your prepayment credits
  are depleted`. Đây là vấn đề **billing của project Google Cloud/AI Studio
  đang gắn với `GOOGLE_API_KEY`**, không phải lỗi code — không thể tự sửa
  bằng code. Vì vậy đã đổi **default provider về lại `openai`** (đã xác minh
  hoạt động ổn định suốt phiên làm việc này) ở cả `app/knowledge/index.py` và
  `services/rag_mcp/config.py`; `gemini` vẫn chọn được qua
  `KNOWLEDGE_EMBEDDING_PROVIDER=gemini` / `RAG_MCP_EMBEDDING_PROVIDER=gemini`
  khi nào billing được khôi phục — code đã đúng, chỉ còn phụ thuộc thanh toán.

## 5. Kết quả kiểm thử

```
pytest -q   (không cần override biến môi trường — default đã đúng)
→ 164 passed, 0 failed
```
