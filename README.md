# SHB Corporate Sales Copilot — Local MVP V2

Hệ thống hỗ trợ RM xử lý một sales case doanh nghiệp theo luồng có kiểm soát:

```text
Tiếp nhận hồ sơ → trích xuất Customer Business Snapshot → RM xác nhận context
→ hiểu nhu cầu → tìm sản phẩm → kiểm tra điều kiện → lập kế hoạch/checklist/nháp
→ kiểm chứng nguồn → RM xem và phê duyệt exact payload → mock executor thực thi
```

> Toàn bộ khách hàng, sản phẩm, chính sách, hồ sơ và kết quả CRM trong repo là **SYNTHETIC_DEMO_DATA**. Không dùng làm chính sách SHB thật hoặc quyết định tín dụng production.

## Bản này đã có gì

- Document intake cho PDF/DOCX/XLSX/TXT/MD/CSV/JSON: kiểm tra loại/kích thước, SHA-256, quality gate và prompt-injection quarantine; không lưu raw upload.
- Hồ sơ doanh nghiệp hợp nhất từ CRM mock, tài liệu và RM correction thành `Customer Business Snapshot` có nguồn, confidence, conflict và revision hash.
- RM confirmation gate trước khi AI phân tích; thay đổi profile làm vô hiệu kết quả downstream cũ.
- Intent extraction có schema, confidence và deterministic fallback khi chưa bật LLM.
- Persistent hybrid Product RAG và Legal RAG bằng SQLite, có ACL, version, effective date, citation và retrieval score.
- Eligibility Engine deterministic, versioned và fail-closed; LLM không quyết định đạt/không đạt.
- Bộ policy B2B synthetic gắn Product → Rule → Policy → Section cho Payroll, Cash Management, Bulk Payment và Working Capital; output từng sản phẩm có chính sách/điều khoản, legal summary, hồ sơ cần bổ sung và evidence đã kiểm chứng. Xem `docs/LEGAL_B2B_CAPABILITY_MATRIX.md`.
- Planner liên kết Product → Legal/Eligibility → Operations → Approval; có Next Best Question và Next Best Action.
- Operations tạo checklist, proposal/email nháp và exact CRM/task payload; không tự gọi hệ thống ngoài.
- Approval token khóa theo `case_id`, RM, exact payload hash, nonce, expiry và one-time use; executor có idempotency.
- Persistent case state, optimistic locking, hash-chained audit và partial resume theo impact graph.
- **AI Decision Log theo từng case**: module, mode/model, prompt/rule/workflow version, nguồn, latency, token/cost, output tóm tắt và cờ an toàn. Không ghi raw PII, secret, prompt thô hoặc approval token.
- RM Workspace ba cột, năm bước nghiệp vụ, bốn case mẫu có output kỳ vọng và tab Nguồn / Nhật ký AI / Audit / JSON.
- `/api/v2` có `40` route (đếm trực tiếp qua route decorator ngày 2026-07-18). V1 (`app/agents/`, `app/rag/`, `/api/v1`) đã được gỡ bỏ hoàn toàn khỏi mã nguồn và không còn mount trong `app/main.py`.

## RAG provider (local | mcp | hybrid)

`app/knowledge/service.py`/`legal_service.py` route mọi truy vấn qua
`RAG_PROVIDER` (`.env`/`.env.v2.example`):

- `local` (mặc định, an toàn khi chưa deploy MCP server): chỉ dùng SQLite
  index cục bộ, không khởi tạo MCP client, không log cảnh báo MCP.
- `mcp`: chỉ dùng MCP server; lỗi trả `RagProviderUnavailableError`, không
  fallback âm thầm.
- `hybrid`: ưu tiên MCP, có circuit breaker (`RAG_MCP_FAILURE_THRESHOLD`,
  `RAG_MCP_COOLDOWN_SECONDS`, `RAG_MCP_REQUEST_TIMEOUT_SECONDS`) + fallback
  local chỉ cho lỗi mạng/khả dụng (không fallback cho lỗi auth/policy).

Chi tiết kiến trúc, circuit breaker, logging, metrics: `docs/RAG_PROVIDER_AND_FALLBACK.md`.

`KNOWLEDGE_EMBEDDING_PROVIDER` (`openai` | `gemini`) chọn embedding provider
cho index cục bộ; mặc định `openai` (Gemini có thể hết prepayment credits).
Không có fallback dạng deterministic-hash không cần API key ở thời điểm
hiện tại (xem "Known limitation" trong `docs/RAG_PROVIDER_AND_FALLBACK.md`).

## RAG MCP Server độc lập

Repo có thêm một service riêng tại `services/rag_mcp/`. Service này sở hữu corpus, ingestion, chunk/index và retrieval; không import Agent/Workflow code.

- Official MCP Python SDK `1.x`, Streamable HTTP stateless.
- Tools: `rag_search`, `rag_get_chunk`, `rag_list_sources`, `rag_health`.
- Persistent SQLite index: 3 source và 19 active chunk thuộc Product, Legal, Operations.
- Permission + branch ACL, effective/version filter, sparse gate và citation/content hash.
- Bearer service authentication và retrieval audit không lưu raw query/PII.
- MCP transport E2E được kiểm thử bằng official client.

Chạy server:

```powershell
.\run_rag_mcp.cmd
```

MCP endpoint: `http://127.0.0.1:8100/mcp`. Hướng dẫn đầy đủ: `docs/RAG_MCP_SERVER.md`; audit MCP của repo đồng đội: `docs/VAIC2026_MCP_AUDIT.md`.

## Chạy bản mock

```powershell
cd C:\Users\Admin\Desktop\hakathon
.\run_mock_demo.cmd
```

Mở:

- UI: `http://127.0.0.1:8000`
- OpenAPI: `http://127.0.0.1:8000/docs`
- V2 health: `http://127.0.0.1:8000/api/v2/health`

Nếu cổng 8000 bận:

```powershell
.\run_mock_demo.cmd 8010
```

Hành trình UI khuyến nghị:

1. Giữ persona `RM-999`, session `SESS-MP`, khách hàng `Minh Phát · COMP-MP`.
2. Chọn một case mẫu rồi bấm **Tạo sales case**.
3. Bấm **Tải lên & kiểm tra file** để dùng bộ hồ sơ synthetic hoặc chọn file thật trong phạm vi demo.
4. Bấm **Chạy Document Intelligence**, xem từng field, nguồn và conflict.
5. RM tick xác nhận và bấm **Xác nhận context**.
6. Bấm **Chạy phân tích end-to-end**; đọc kết quả từ trái sang phải.
7. Mở tab **Nhật ký AI** để xem trace quyết định.
8. Nếu đủ điều kiện: **Xem payload → RM phê duyệt → Thực thi trên CRM mock**.

Chi tiết từng case và output kỳ vọng: `docs/MOCK_DEMO_GUIDE.md`.

## API sales-case facade

| Giai đoạn | Endpoint chính |
|---|---|
| Tạo/list case | `POST/GET /api/v2/sales-cases` |
| Upload/list hồ sơ | `POST/GET /api/v2/sales-cases/{case_id}/documents` |
| Trích xuất | `POST .../process-documents`, `GET .../processing-status` |
| Review context | `GET/PATCH .../extracted-profile`, `POST .../confirm-profile` |
| Phân tích | `POST .../run-analysis` |
| Đọc kết quả | `GET .../recommendations`, `GET .../missing-information`, `GET .../trace` |
| Kiểm soát hành động | `POST .../approval-preview`, `POST .../approve`, `POST .../reject`, `POST .../execute-actions` |
| Truy vết | `GET .../audit`, `GET .../ai-log` |

MVP auth dùng `X-Employee-ID` và `X-Session-ID` với synthetic adapters. Production phải thay bằng principal do SSO/session gateway xác thực.

## Cấu hình

Xem `.env.v2.example`. Các biến chính:

- `V2_DB_PATH`, `VECTOR_DB_DIR`, `AUDIT_LOG_PATH`.
- `APPROVAL_SECRET`, `APPROVAL_TOKEN_TTL_SECONDS`.
- `INTENT_USE_LLM=false` để chạy hoàn toàn offline/deterministic.
- `OPENAI_API_KEY`, `OPENAI_MODEL` chỉ cần khi bật LLM cho intent extraction.

Ngoài development, app từ chối khởi tạo approval service nếu còn dùng secret demo mặc định.

## Kiểm thử và đánh giá

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m app.evaluation.runner --output data\eval\v2\latest_report.json
.\.venv\Scripts\python.exe -m app.evaluation.safety_reliability_runner --output data\eval\v2\latest_safety_reliability_report.json

# Single-agent vs multi-agent benchmark (40 synthetic cases, xem
# docs/SINGLE_VS_MULTI_AGENT_BENCHMARK.md)
.\.venv\Scripts\python.exe -m benchmarks.run --cache-mode warm --output-dir benchmarks\results\latest
.\.venv\Scripts\python.exe -m benchmarks.run --cache-mode cold --cases BENCH-B02,BENCH-D03,BENCH-E02 --output-dir benchmarks\results\cold_smoke
```

Snapshot ngày `2026-07-18` (chạy trực tiếp với `.env` mặc định, không override thủ công):

- `275 passed`, 0 fail (snapshot Legal B2B ngày 2026-07-18).
- Business golden evaluation `40/40`; unsafe approval rate `0%`.
- Relevant-policy precision/recall `100%/100%` trên 10 eligibility golden cases synthetic.
- Security `25/25`; reliability `20/20`.
- Hero multi-product scenario (`tests/test_sales_cases_e2e.py`, 5 case bao gồm flagship) `5/5 passed`.
- Benchmark single-agent vs multi-agent (40 case, warm cache): `missing_info_recall` 0.0 (single) vs 0.889 (multi); `legal_flag_recall` 0.0 (single) vs 0.833 (multi) — single-agent path không có khả năng phát hiện thiếu hồ sơ hoặc rủi ro pháp lý vì không chạy Eligibility Engine. Chi tiết: `docs/SINGLE_VS_MULTI_AGENT_BENCHMARK.md`.

OCR: hiện chỉ có phát hiện trạng thái `NEEDS_OCR` cho PDF scan/không có text
layer, **chưa có OCR engine thật** — không tuyên bố "đã implement OCR".

Bằng chứng:

- `docs/BUILD_V2_LOG.md`
- `docs/MOCK_DEMO_RUN_REPORT.md`
- `docs/AI_DECISION_LOG.md`
- `docs/RAG_MCP_SERVER.md`
- `docs/RAG_MCP_RUN_REPORT.md`
- `docs/VAIC2026_MCP_AUDIT.md`
- `docs/V2_READINESS_REPORT.md`
- `data/eval/v2/latest_report.json`
- `data/eval/v2/latest_safety_reliability_report.json`

## Ranh giới production

Local MVP đã chạy end-to-end nhưng chưa production-ready vì còn thiếu:

- SSO/IAM/CRM/DMS/CIC/KYC và catalog/policy SHB thật.
- Data-owner, Legal, Privacy và Security sign-off.
- Semantic embedding/reranker benchmark trên dữ liệu thật. Hiện chưa có fallback dạng deterministic-hash không cần API key — nếu `OPENAI_API_KEY`/`GOOGLE_API_KEY` không khả dụng, retrieval sẽ lỗi thay vì suy biến êm sang một provider không cần mạng (xem "Known limitation" trong `docs/RAG_PROVIDER_AND_FALLBACK.md`).
- OCR cho PDF scan; parser PDF hiện cần text layer.
- PostgreSQL/Redis/vector DB/secret manager/OpenTelemetry backend production.
- Load, penetration, DR test và golden set case thật đã de-identify, được SME adjudicate.

Không trộn synthetic source vào production serving index.
