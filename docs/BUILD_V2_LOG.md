# V2 Build Log

Nhật ký này là bằng chứng triển khai Plan V2. Một hạng mục chỉ được ghi `Done` khi có test hoặc eval tương ứng. Dữ liệu hiện tại là synthetic và không được coi là chính sách SHB thật.

## V2-018 — Product-scoped Legal B2B policies — 2026-07-18

- Thêm governed `SYNTHETIC_DEMO_DATA` policy pack cho 4 sản phẩm active và Source Card/lineage.
- Mở rộng Pydantic eligibility output với `related_policies` và `legal_summary`; rule bắt buộc tham chiếu `policy_id`/`section_id`.
- Legal RAG index policy sections; workflow kiểm chứng exact quote, fail-closed khi evidence thiếu và ghi policy metadata/metrics.
- Web và Flutter projection hiển thị policy, version, hiệu lực, decision effect và quote; xóa `app/legal/LegalAgentV2` orphan.
- Verification: `pytest -q` → `275 passed`; business eval `40/40`, policy precision/recall `1.0/1.0`, unsafe pass `0`; security `25/25`, reliability `20/20`.
- Flutter analyze/test chưa chạy trong máy review vì không có Flutter SDK trong PATH; thay đổi Dart additive, không chạy codegen.

## Baseline — 2026-07-17

| Hạng mục | Kết quả |
|---|---|
| Test suite ban đầu | `79 passed`, 1 warning |
| V2 có bằng chứng hoàn thành | V2-001, V2-002, V2-003 |
| V2-004 | Code khởi đầu nhưng chưa đủ acceptance; trạng thái thực tế `In Progress` |
| Runtime end-to-end | `/api/v1`, synthetic, state/catalog in-memory |
| `/api/v2`, persistent state/index, golden eval | Chưa có |

Lệnh baseline:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Change set 01 — Intent và context-aware clarification

Trạng thái: `Done` ở phạm vi acceptance V2-004/V2-005 cục bộ; chưa nối API/workflow V2.

Đã làm:

- Taxonomy intent bán hàng doanh nghiệp có version và action allowlist.
- Deterministic fallback khi không có API key, model timeout hoặc output lỗi.
- Chuẩn hóa tiếng Việt, Product ID, số tiền và kỳ hạn.
- Multi-intent; evidence span phải tồn tại đúng trong message nguồn.
- Tái dùng customer/case/product đang chọn, giữ provenance.
- Confidence theo field; conflict bắt buộc confirmation.
- Chỉ chọn tối đa một câu hỏi làm rõ có tác động cao nhất.
- Context đưa vào LLM đã được tối thiểu hóa.

Test:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_v2_intent.py -q
```

Kết quả: `10 passed`. Full suite sau change set: `86 passed, 1 warning`.

## Change set 02 — Governed product data và persistent hybrid RAG

Trạng thái: `Done` cho ingestion/retrieval MVP synthetic; embedding vẫn là deterministic hash, chưa phải semantic embedding pilot.

Đã làm:

- Product data pack versioned, có active/effective dates, ACL, source/version/location.
- Data Source Card đúng contract và serving gate.
- Typed ingestion, SHA-256 lineage, ingest report và idempotent upsert.
- Hybrid dense-hash + sparse index lưu SQLite, còn dữ liệu sau restart.
- Lọc active/effective date, ACL, segment và Product ID trước serving.
- Out-of-scope trả empty; Product Service không được tự kết luận eligibility.

Test:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_v2_product_knowledge.py -q
```

Kết quả: `7 passed`.

## Change set 03 — Eligibility rule engine fail-closed

Trạng thái: `Done` cho rule registry và synthetic legal evidence MVP; chưa có legal document parser/index độc lập hoặc live KYC/CIC thật.

Đã làm:

- Rule registry JSON có rule ID, version, scope, effective date, severity và source quote.
- Rule engine deterministic, aggregate riêng từng sản phẩm.
- Kết quả phân biệt `passed`, `failed`, `pending_information`, `pending_review`.
- UBO và hồ sơ tín dụng chỉ block sản phẩm tín dụng, không làm mất sản phẩm payroll.
- Tool timeout không thể tạo kết quả passed.
- Mọi blocking result giữ source document/version/location/quote.

Test:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_v2_eligibility.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

Kết quả: `5 passed` cho eligibility; full suite `98 passed, 1 warning`.

## Việc chưa hoàn thành sau change set 03

- Workflow V2, impact-based resume và artifact dedup.
- Persistent case/audit/approval state.
- Payload freeze, nonce, one-time approval và executor idempotency.
- `/api/v2`, RM Workspace V2 và full vertical slice.
- Golden datasets/runner, security/reliability evaluation và dashboard metrics.
- Adapter dữ liệu/API SHB thật, auth/RBAC thật, semantic embedding và production security review.

## Change set 04 — Workflow, Operations và partial resume

Trạng thái: `Done` cho local synthetic MVP.

- State machine tập trung và từ chối transition không hợp lệ.
- Task DAG deterministic có dependency, input hash và output reference.
- Impact graph: UBO/BCTC chỉ chạy lại Eligibility → Evidence → Operations.
- Resume tối đa 3 vòng; approval cũ bị reset khi payload downstream thay đổi.
- Operations tạo checklist hợp nhất, email/case/task draft, version, hash và dedup key; side effect luôn rỗng.

Test liên quan: `tests/unit/test_v2_workflow.py`, `tests/unit/test_v2_operations.py`.

## Change set 05 — Persistence, approval, executor và observability

Trạng thái: `Done` cho local/pilot-shaped storage; production backend chưa có.

- SQLite case state restart-safe và optimistic locking.
- Audit append-only có `prev_hash/event_hash` và hàm verify chain.
- Approval HMAC có token ID, nonce, expiry, permission, exact payload hash và one-time consumption.
- Executor kiểm tra status/evidence/eligibility/payload và lưu idempotency result.
- JSON event log redacts token; metrics local process.
- Retry chỉ cho idempotent operation, circuit breaker và TTL cache có access scope/version.

Test liên quan: `test_v2_storage_approval.py`, `test_v2_actions_observability.py`, `test_v2_reliability_security.py`.

## Change set 06 — API/UI V2 và document parsing

Trạng thái: `Done` cho hành trình sandbox.

- `/api/v2` tạo/get/resume/trace/preview/approve/execute/reject/search/metrics.
- Employee lấy từ header synthetic adapter, không tin RM ID trong body; case ownership được enforce.
- State version/ETag và conflict `409`.
- UI hiển thị context, intent, confidence, product, eligibility, checklist, draft, evidence và timeline.
- Parser PDF text layer, DOCX heading/table, XLSX sheet/header, JSON/text; extraction quality gate chặn tài liệu rỗng.
- Prompt injection bị chặn trước khi tạo case; số định danh được redact khỏi prompt lưu trong case.

Test liên quan: `tests/test_api_v2.py`, `tests/unit/test_v2_document_parsers.py`.

## Change set 07 — Golden evaluation

Trạng thái: `Done` cho dataset synthetic version `2026.07.17-v1`.

- 40 golden cases: 15 intent, 15 retrieval, 10 eligibility.
- Runner tái lập được và xuất JSON report.
- Kết quả hiện tại: intent `1.0`, product entity `1.0`, Hit@3 `1.0`, OOS `1.0`, eligibility `1.0`, unsafe approval `0.0`.
- Báo cáo: `data/eval/v2/latest_report.json`.

Lệnh:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.runner --output data\eval\v2\latest_report.json
```

## Change set 08 — Legal RAG, governed ingestion và runtime hardening

Trạng thái: `Done` cho local/sandbox MVP; dữ liệu và adapter bên ngoài vẫn là synthetic.

- Thêm persistent Legal RAG dùng cùng contract chunk/version/ACL với Product RAG. Legal RAG chỉ cung cấp evidence và giải thích; `EligibilityEngine` vẫn là decision owner.
- Thêm parse trực tiếp bytes upload cho PDF/DOCX/XLSX/TXT/MD/CSV/JSON, giới hạn kích thước, quality gate, SHA-256 và prompt-injection quarantine; không lưu raw upload.
- Thêm governed upload-to-index. Chỉ `DataSteward` có `knowledge:write`, source phải có Source Card đã phê duyệt và còn hiệu lực.
- Bổ sung API resolve context, cập nhật mục tiêu, đăng ký tài liệu, sửa context có provenance, Legal search, inspect/ingest tài liệu và health.
- Bổ sung `ResilientCRMAdapter` với timeout/retry an toàn và circuit breaker; lỗi dependency làm context fail-closed.
- Bổ sung migration registry, schema version và SQLite `quick_check` trong health endpoint.
- Bổ sung 25 security cases và 20 reliability cases có runner thực thi thật các guardrail/retry/cache/circuit behavior.
- Bổ sung data-governance test: Source Card phải unique, approved, có owner, lineage và quality policy.

Test liên quan: `test_v2_legal_rag.py`, `test_v2_upload_ingestion.py`, `test_v2_resilient_adapters.py`, `test_v2_data_governance.py`, `test_v2_safety_reliability_evaluation.py` và API V2 mở rộng.

## Change set 09 — RM Workspace information architecture

Trạng thái: `Done` cho UI local/sandbox.

- Bố trí lại theo thứ tự nhận thức: context → tiến trình → đầu vào → kết luận → hành động → kiểm chứng.
- Tách ba vùng rõ ràng: đầu vào bên trái, kết luận nghiệp vụ ở giữa, hành động ưu tiên bên phải.
- Thêm bốn case demo có input, output lần đầu, lý do, hành động tiếp theo và output cuối.
- Dịch status/intent/eligibility sang ngôn ngữ nghiệp vụ; raw code chỉ còn ở lớp thông tin phụ.
- Phân biệt số điều kiện đang chặn với tổng hồ sơ vận hành còn thiếu.
- Checklist phân biệt tài liệu đã có, tài liệu đang chặn điều kiện và tài liệu chỉ phục vụ triển khai.
- Sửa Operations để tài liệu `verified` trong context không còn bị hiển thị `missing`.
- Evidence, audit và JSON được thu gọn mặc định.
- Browser QA bốn case: payroll, multi-product partial resume, clarification và prompt injection; không có console error.
- Thêm `tests/test_ui_v2.py` và tài liệu `docs/UI_INFORMATION_ARCHITECTURE.md`.

## Change set 10 — Document intake, public sales-case facade và AI Decision Log

Trạng thái: `Done` cho local/sandbox vertical slice có browser E2E.

- Thêm persistent intake session, document job, extraction field, conflict và profile draft; schema database nâng lên version `2`.
- Thêm bộ hồ sơ synthetic của Công ty Minh Phát: đăng ký kinh doanh, meeting note, quy trình thanh toán, BCTC và UBO.
- Thêm Document Intelligence deterministic cho MVP: phân loại, trích xuất field, provenance, confidence, conflict và prompt-injection quarantine; không lưu raw upload.
- Thêm `CustomerBusinessSnapshot`, RM attestation/confirmation gate, revision hash và downstream invalidation khi context đổi.
- Thêm Planner contract, initial plan/replan, Next Best Question và Next Best Action liên kết trực tiếp với Eligibility/Operations.
- Mở public facade `19` route dưới `/api/v2/sales-cases` cho create → upload → process → profile review → confirm → analysis → approval → execute → audit/AI log.
- Approval/execute khóa toàn bộ `action_payload`, vẫn giữ legacy `/cases` tương thích.
- Thêm AI Decision Log theo case cho RequirementExtractor, Planner, ProductRAG, EligibilityEngine, EvidenceValidator và OperationsComposer.
- AI log ghi mode/model, prompt/rule/workflow version, source/retrieval score, latency, token/cost và output summary đã sanitize; cờ `raw_pii_logged=false`, `secret_logged=false`.
- Thiết kế lại RM Workspace theo năm bước và ba cột; thêm tab `Nhật ký AI` và hướng dẫn output của từng case mẫu.
- Thêm API E2E tests cho happy path, missing UBO/BCTC partial resume, unsafe input và cross-RM access.

Test liên quan: `tests/test_sales_cases_e2e.py`, `tests/test_ui_v2.py`, toàn bộ contract/unit/API regression và browser E2E.

## Change set 11 — Independent governed RAG MCP server

Trạng thái: `Done` cho local/sandbox server; chưa phải production banking infrastructure.

- Audit riêng phần MCP của `ShayNeeo/VAIC2026`: giữ ý tưởng hybrid retrieval/citation, không lấy các Agent/UI/Workflow khác.
- Thay third-party/unpinned prototype transport bằng official MCP Python SDK `1.x`, Streamable HTTP stateless và structured output.
- Tách service độc lập tại `services/rag_mcp/`; service không import Agent Orchestrator.
- Thêm governed ingestion từ 3 Source Card đã duyệt: Product, Legal, Operations.
- Persistent SQLite source/chunk/vector/audit index; 19 active chunk và 2 expired product chunks không được serving.
- Thêm read-only tools `rag_search`, `rag_get_chunk`, `rag_list_sources`, `rag_health`.
- Thêm permission + branch ACL, product/document/segment/version/effective-date filter và OOS sparse gate trước khi trả chunk.
- Response có chunk ID, dense/sparse/final score, source/document/version/section/content hash và `context_text` đóng gói cho LLM.
- Bearer service authentication ở HTTP boundary; secret không đi qua tool arguments.
- Retrieval audit lưu caller/query hash, filter, latency, result count và error code; không lưu raw query/chunk/PII/token.
- Thêm CLI seed/health/audit, official MCP client, smoke script, PowerShell/CMD launcher, Dockerfile và compose service.
- Transport E2E thật: initialize → list tools → call `rag_health`/`rag_search`; request thiếu bearer trả `401`.

Test liên quan: `tests/rag_mcp/test_service.py`, `tests/rag_mcp/test_transport.py`.

## Giới hạn còn lại sau khi đóng local MVP

- Chưa có API, dữ liệu, approval matrix và policy SHB thật; mọi adapter nghiệp vụ vẫn synthetic.
- Chưa có OCR cho PDF scan, semantic embedding/reranker thật và legal/product corpus do owner SHB ký duyệt. Pipeline legal ingestion đã có nhưng đang dùng source synthetic.
- Chưa có SSO gateway, PostgreSQL/Redis/vector DB, secret manager, OpenTelemetry backend và penetration/load/DR test.
- Golden score 100% chỉ phản ánh bộ synthetic nhỏ do repo tạo; không được suy rộng thành chất lượng production.

## Final verification — 2026-07-17

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m app.evaluation.runner --output data\eval\v2\latest_report.json
.\.venv\Scripts\python.exe -m app.evaluation.safety_reliability_runner --output data\eval\v2\latest_safety_reliability_report.json
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term -q
```

Kết quả:

- `172 passed`, `1 warning` từ dependency Starlette multipart.
- Coverage toàn repo: `92%` (`3682` statements, `308` missed).
- Golden evaluation: `40/40` pass, `unsafe_approval_rate = 0.0`.
- Security evaluation: `25/25` pass.
- Reliability evaluation: `20/20` pass.
- Parser fixture PDF/DOCX/XLSX: `3 passed`.
- API V2 có `39` routes; public sales-case facade có `19` route. Journey browser đã chạy intake → profile confirmation → analysis → approval → mock execution.
- Browser console error/warning: `0`.
- Case QA `CASE-ADAACD9BEC36`: AI Decision Log có `7` entry, tổng latency `10 ms`, token/cost `0` ở deterministic mode và `raw_pii_logged=false`.
- RAG MCP smoke: 4 tools được discover qua official client; health `ok`, 3 source/19 active chunk, bearer auth và retrieval audit hoạt động.
