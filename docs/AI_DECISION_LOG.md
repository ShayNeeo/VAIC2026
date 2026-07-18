# AI Decision Log

## Mục tiêu

AI Decision Log giúp RM, QA, vận hành và kiểm toán trả lời bốn câu hỏi cho từng sales case:

1. Module nào đã đưa ra kết quả?
2. Module dùng model, prompt, rule hoặc retrieval version nào?
3. Kết luận dựa trên nguồn nào và mất bao lâu?
4. Có phát sinh token/cost hoặc rủi ro ghi dữ liệu nhạy cảm hay không?

Đây là log giải thích quyết định AI/workflow. Audit Log là log bất biến của hành động nghiệp vụ. Hai loại log bổ sung cho nhau, không thay thế nhau.

## Nơi xem

- Giao diện: mở case, chạy phân tích, chọn tab **Nhật ký AI** ở cột phải.
- API: `GET /api/v2/sales-cases/{case_id}/ai-log` với `X-Employee-ID` và `X-Session-ID` đúng scope.
- Shared state: trường `ai_decision_log` của case, được lưu persistent trong SQLite.
- Audit nghiệp vụ: `GET /api/v2/sales-cases/{case_id}/audit` hoặc `data/logs/audit.jsonl`.

## Contract mỗi entry

| Trường | Ý nghĩa |
|---|---|
| `log_id`, `at` | Định danh và thời điểm entry |
| `case_id`, `trace_id` | Liên kết case và một lần chạy workflow |
| `component`, `event` | Module và sự kiện đã xảy ra |
| `mode`, `model` | Cách xử lý và model/rule engine thực tế |
| `prompt_or_policy_version` | Version prompt, schema, matcher, rule hoặc policy |
| `workflow_version` | Version workflow chung |
| `latency_ms` | Thời gian của module |
| `token_usage`, `estimated_cost` | Input/output/total token và cost ước tính |
| `output_summary` | Kết quả tóm tắt có cấu trúc, không chứa prompt thô |
| `sources` | Document ID, version, location, retrieval score hoặc claim ID |
| `safety` | Cờ xác nhận không ghi raw PII và secret |

## Các module được ghi

- `RequirementExtractor`: intent, confidence, recommended action và fallback reason.
- `Planner`: kế hoạch đầu, lần replan, số câu hỏi và next action.
- `ProductRAG`: Product ID, match score, document/version/location và retrieval score.
- `EligibilityEngine`: rule ID/version/status và nguồn chính sách.
- `EvidenceValidator`: số claim, claim hợp lệ/không hợp lệ.
- `OperationsComposer`: artifact version, readiness, số hồ sơ còn thiếu và số side effect ngoài hệ thống.

## Chính sách bảo mật

AI log không được chứa:

- Nội dung prompt đầy đủ hoặc raw message của khách hàng.
- CCCD, số tài khoản, số điện thoại, email hoặc PII thô.
- API key, credential, session secret hoặc approval token.
- Raw file upload.

Log chỉ giữ ID, version, số đo, source metadata và output summary đã giới hạn. API vẫn kiểm tra case ownership trước khi trả log.

## Cách đọc bản mock

Mặc định `INTENT_USE_LLM=false`, vì vậy Requirement Extractor hiển thị `deterministic_fallback`, token/cost bằng 0. Product RAG hiện dùng `deterministic-hash-embedding-v1`; đây là persistent hybrid retrieval cho demo, không phải semantic embedding production.

Khi bật LLM intent extraction và cấu hình provider hợp lệ, entry sẽ ghi model thực tế, token usage và cost nếu adapter cung cấp. Eligibility, approval và external action vẫn deterministic/HITL.

## Ví dụ kiểm tra

```powershell
$headers = @{
  'X-Employee-ID' = 'RM-999'
  'X-Session-ID' = 'SESS-MP'
}

Invoke-RestMethod `
  -Uri 'http://127.0.0.1:8000/api/v2/sales-cases/{case_id}/ai-log' `
  -Headers $headers
```

Một response hợp lệ phải có:

- `summary.entry_count > 0` sau khi phân tích.
- `summary.raw_pii_logged = false`.
- Có entry của RequirementExtractor, ProductRAG, EligibilityEngine, EvidenceValidator và OperationsComposer.
- Mỗi claim/sản phẩm quan trọng có source hoặc được validator đánh dấu không hợp lệ.

## Giới hạn hiện tại

- AI log được lưu cùng case state trong SQLite local, chưa export sang OpenTelemetry/SIEM.
- Cost bằng 0 ở chế độ deterministic; chưa có pricing registry đa model.
- Chưa có retention/deletion policy production hoặc encryption-at-rest do KMS quản lý.
- Chưa có dashboard aggregate drift/cost; API hiện phục vụ trace theo từng case.
