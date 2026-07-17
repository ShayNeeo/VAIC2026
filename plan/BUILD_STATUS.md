# BUILD STATUS — SHB Corporate Expert Workspace, theo từng khối

Tài liệu này dành cho **người đọc** (thành viên mới trong team, hoặc bạn quay lại sau vài ngày), không phải để AI nạp làm ngữ cảnh build (việc đó dùng [`INDEX.md`](INDEX.md) + [`PROGRESS.md`](PROGRESS.md)). Đọc file này khi cần biết: **hệ thống đang có gì chạy được, khối nào còn thiếu, và tôi nên bắt đầu từ đâu nếu nhận việc.**

Phân biệt 3 file dễ nhầm trong `plan/`:

| File | Dùng khi nào |
|---|---|
| `BUILD_STATUS.md` (file này) | Muốn biết tổng quan theo khối chức năng thật trong code, để nhận việc hoặc onboard người mới |
| [`PROGRESS.md`](PROGRESS.md) | Nhật ký sống: quyết định kỹ thuật, lệch so với plan, backlog theo TSK-ID — cập nhật liên tục khi code |
| [`modules/`](modules/) | Đặc tả thiết kế **gốc** (45 mục ban đầu) — dùng để tra "plan lúc đầu định làm gì", không phải trạng thái hiện tại |

Cập nhật file này mỗi khi một khối đổi trạng thái (Chưa có → Một phần → Hoàn thành), không cần cập nhật hàng ngày như PROGRESS.md.

## 0. Bức tranh tổng thể

```text
RM Workspace (UI) ─▶ FastAPI (app/main.py)
                         │
                Input Guardrail + Complexity Router
                         │
              ┌──────────┴──────────┐
        route=simple            route=complex
              │                      │
        Product RAG              Planner Agent (DAG)
        (trả lời nhanh)               │
                            ┌─────────┼─────────┐
                       Product Agent  │   Legal Agent
                            └─────────┴─────────┘
                                      │
                            Evidence Validator
                                      │
                         (blocking?) ─┴─ (không blocking?)
                              │                │
                    Operations Agent     Operations Agent
                    (checklist thiếu)    (chuẩn bị case/task)
                              │                │
                     pending_information  pending_approval
                                           │
                                  RM Approve (HMAC token)
                                           │
                                  Action Executor ─▶ Mock CRM
```

Toàn bộ pipeline này **đã chạy được thật**, có test end-to-end xác nhận (xem Khối 10). Điểm cần biết trước khi nhận việc: **hệ thống hiện là 100% deterministic (rule-based), chưa gọi LLM thật ở bất kỳ đâu** — đây là lựa chọn có chủ đích cho MVP (xem lý do ở `PROGRESS.md` mục 4), không phải thiếu sót.

Trạng thái dùng trong file này: **Hoàn thành (MVP)** = chạy được, có test xanh · **Một phần** = chạy được nhưng thiếu phần quan trọng · **Chưa có** = chưa tồn tại trong code.

## 1. Bảng tổng quan (đọc bảng này trước khi đọc chi tiết)

| # | Khối | Trạng thái | File chính | Người phù hợp* |
|---|---|---|---|---|
| 2 | Shared State & Schema | Hoàn thành (MVP) | `app/schemas/state.py`, `app/database.py` | Người 1 |
| 3 | Input Guardrail + Complexity Router | Hoàn thành (MVP) | `app/safety/guardrails.py`, `app/services/complexity_router.py` | Người 1 |
| 4 | Planner Agent | Hoàn thành (MVP) | `app/services/planner_agent.py` | Người 1 |
| 5 | Product Agent + Product RAG | Hoàn thành (MVP), RAG là bản MVP | `app/agents/product_agent.py`, `app/rag/product_retriever.py` | Người 2 |
| 6 | Legal Agent | Hoàn thành (MVP) | `app/agents/legal_agent.py`, `app/tools/legal_tools.py` | Người 2 |
| 7 | Operations Agent | Hoàn thành (MVP) | `app/agents/operations_agent.py`, `app/tools/operations_tools.py` | Người 3 |
| 8 | Evidence Validator | **Một phần** (1/3 lớp) | `app/safety/evidence_validator.py` | Người 2 |
| 9 | Tool Registry / phân quyền tool | **Một phần** (có cơ chế, chưa gắn vào luồng thật) | `app/tools/registry.py` | Người 1 hoặc 3 |
| 10 | Approval Flow + Action Executor | Hoàn thành (MVP) | `app/services/approval.py` | Người 3 |
| 11 | Orchestrator | Hoàn thành (MVP) | `app/services/orchestrator.py` | Người 1 |
| 12 | API Layer (FastAPI) | Hoàn thành (MVP), thiếu vài test nhánh lỗi | `app/main.py` | Người 3 |
| 13 | Frontend / RM Workspace UI | **Một phần** (demo tối giản) | `app/static/index.html` | Người 4 |
| 14 | Mock external services | Hoàn thành (MVP) | `app/services/mock_services.py` | Người 3 |
| 15 | Testing | **Một phần** (16 test lõi, chưa có golden 40-case) | `tests/` | Cả team |
| 16 | DevOps / Deployment / Config | **Một phần** | `Dockerfile`, `docker-compose.yml`, `requirements*.txt` | Người 3 |
| 17 | Version control & nộp bài (git, AI_LOG) | **Chưa có — khẩn cấp** | (chưa tồn tại) | Người 4 / cả team |

\* Theo đúng phân công 4 người trong plan gốc ([`modules/11_roadmap_and_backlog.md`](modules/11_roadmap_and_backlog.md) mục 10.1): Người 1 = Planner/orchestration; Người 2 = Product/Legal/RAG/eval; Người 3 = Operations/FastAPI/mock API/deploy; Người 4 = Frontend/demo/README/pitch.

---

## 2. Shared State & Schema

**Mục đích:** định nghĩa "ngôn ngữ chung" mà mọi agent đọc/ghi vào — đây là hợp đồng dữ liệu (data contract) của toàn hệ thống. Đổi field ở đây ảnh hưởng tới tất cả các khối khác.

**Đã build:**
- [`app/schemas/state.py`](../app/schemas/state.py): `SharedCaseState` (Pydantic) — case_id, customer/rm id, execution_plan, product/legal/operations_result, missing_information, evidences, risk_level, approval_status, final_status, audit_log, trace_id, timestamps. `EvidenceItem`, `TaskItem`, và DTO cho request API (`CreateCaseRequest`, `ApproveCaseRequest`, `RejectCaseRequest`, `ResumeCaseRequest`).
- [`app/database.py`](../app/database.py): `SimpleDatabase` in-memory, có `RLock` (thread-safe) và `model_copy(deep=True)` khi lưu/đọc để tránh 2 request cùng sửa chung 1 object Python trong bộ nhớ.

**Cần build thêm:**
- [ ] Thay `SimpleDatabase` bằng backend có thể persist thật (PostgreSQL/SQLite) nếu muốn case sống sót qua restart — hiện tại **mất hết case khi tắt server**.
- [ ] `audit_log` hiện là `List[Dict]` tự do, không có schema cố định cho từng loại event — nên cân nhắc union type hoặc chuẩn hoá field bắt buộc (actor/action/result/timestamp) nếu cần audit nghiêm ngặt hơn.

**Đọc thêm:** [`modules/07_tools_and_shared_state.md`](modules/07_tools_and_shared_state.md) (schema gốc dự kiến — đã khớp phần lớn với bản thực tế).

---

## 3. Input Guardrail + Complexity Router

**Mục đích:** chặn input nguy hiểm (prompt injection, PII) trước khi vào hệ thống, và quyết định một yêu cầu nên trả lời nhanh (RAG đơn) hay cần chạy toàn bộ multi-agent (tiết kiệm thời gian/chi phí cho câu hỏi đơn giản).

**Đã build:**
- [`app/safety/guardrails.py`](../app/safety/guardrails.py) — `GuardrailGate.inspect_input()`: regex chặn các cụm như "ignore previous", "bỏ qua chỉ dẫn", "bypass approval"... trên cả request text lẫn text trong tài liệu upload. `mask_pii()`: che số thẻ/tài khoản dài và mã PIN. `can_execute()`: gate cuối cùng trước khi cho phép `ActionExecutor` chạy (kiểm tra không có lỗi pháp lý blocking, đã approved, evidence đã valid hết).
- [`app/services/complexity_router.py`](../app/services/complexity_router.py) — `ComplexityRouter.route()`: đếm số domain nhắc tới (payroll, dòng tiền, thu/chi hộ, thấu chi...) và cờ rủi ro cao (thấu chi/vốn lưu động/tín dụng/kyc/ubo) để chọn `"simple"` hay `"complex"`.

**Cần build thêm:**
- [ ] Danh sách regex injection hiện còn ngắn (5 pattern) — nên mở rộng dần khi có ví dụ tấn công mới từ red-team test.
- [ ] `mask_pii` mới che số dài và PIN; chưa che CCCD/số điện thoại/email — cân nhắc thêm nếu demo có dữ liệu dạng đó.
- [ ] Chưa có test riêng cho `ComplexityRouter` (đang được test gián tiếp qua orchestrator/API test) — nên thêm 1 file test nhỏ để dễ điều chỉnh ngưỡng sau này.

**Đọc thêm:** [`modules/01_architecture.md`](modules/01_architecture.md), [`modules/06_evidence_guardrails_approval.md`](modules/06_evidence_guardrails_approval.md) mục 20.1.

---

## 4. Planner Agent

**Mục đích:** phân rã yêu cầu khách hàng thành các task giao cho Product/Legal/Operations, quản lý dependency (DAG), và ra quyết định điều chỉnh luồng khi Legal Agent báo lỗi chặn hoặc có xung đột chính sách.

**Đã build:**
- [`app/services/planner_agent.py`](../app/services/planner_agent.py) — `PlannerAgent.create_plan()`: tạo task Product/Legal/Validator/Operations tuỳ theo yêu cầu có nhắc payroll/tín dụng hay không, kèm `validate_dag()` (topological sort, phát hiện chu trình) và `_sequential_fallback()` nếu phát hiện cycle. `adapt_plan()`: xử lý 3 tình huống — Legal báo `blocking` (tạm dừng, thêm task `T-OPS-MISSING`), xung đột chính sách (`pending_review`), hoặc vượt quá `max_loops` (mặc định 3, dừng hẳn với `failed`).
- Planner **không gọi tool nghiệp vụ** và không lộ chain-of-thought ra ngoài — chỉ thao tác trên `SharedCaseState`, đúng nguyên tắc trong plan gốc.

**Cần build thêm:**
- [ ] Hiện chỉ nhận diện 2 nhóm nhu cầu (payroll, tín dụng) bằng từ khoá — khi có thêm sản phẩm mới (thu/chi hộ, cash management...) cần mở rộng logic tạo task tương ứng, không chỉ dựa vào Product Agent tự suy luận.
- [ ] `PlannerMetrics` (plan_validity_rate, average_replanning_steps) đã có nhưng chưa expose qua API/dashboard nào — cần một endpoint hoặc log định kỳ nếu muốn demo con số này.

**Đọc thêm:** [`modules/02_planner_agent.md`](modules/02_planner_agent.md).

---

## 5. Product Agent + Product RAG

**Mục đích:** phân tích hồ sơ doanh nghiệp + yêu cầu, chọn sản phẩm phù hợp trong catalog, và tạo bằng chứng (citation) cho mỗi đề xuất.

**Đã build:**
- [`app/agents/product_agent.py`](../app/agents/product_agent.py) — chọn sản phẩm bằng rule xác định (payroll nếu ≥10 nhân sự hoặc nhắc "chi lương"; cash management nếu doanh thu ≥50 tỷ và dòng tiền phân tán; v.v.), tính `match_score`, sinh `matching_reason` theo template, và tạo `EvidenceItem` cho từng sản phẩm được chọn.
- [`app/rag/product_retriever.py`](../app/rag/product_retriever.py) — `ProductRAGService`: pipeline **local-first, không gọi API/model ngoài** — chuẩn hoá query → hash-embedding (thay embedding thật) → kết hợp dense (cosine) + sparse (token overlap) → ngưỡng lọc → context có citation nguồn/section. Lấy cảm hứng từ kiến trúc RAG_VSF (normalize → hybrid retrieve → rerank → context) nhưng đơn giản hoá để chạy offline.
- Catalog 4 sản phẩm mẫu trong [`app/tools/product_tools.py`](../app/tools/product_tools.py) (Payroll, Cash Management, Collection, Working Capital) — toàn bộ là `SYNTHETIC DEMO DATA`.

**Cần build thêm:**
- [ ] Đây là RAG "MVP fallback" — hash embedding không phải embedding ngữ nghĩa thật. Khi có thời gian, thay bằng embedding model thật (vd. multilingual-e5) + vector index thật (FAISS/Chroma) nếu muốn RAG chịu được câu hỏi diễn đạt khác xa văn bản gốc.
- [ ] `search_product_catalog()`/`retrieve_product_policy()` trong `app/tools/product_tools.py` (dòng 59-77) là **code chết** — không còn agent nào gọi (đã bị thay bằng `ProductRAGService`). Xoá hoặc gắn lại vào Tool Registry (xem Khối 9).
- [ ] Danh mục sản phẩm mới có 4 sản phẩm mẫu — muốn demo phong phú hơn cần thêm sản phẩm + policy tương ứng trong cùng file.

**Đọc thêm:** [`modules/03_product_agent.md`](modules/03_product_agent.md), [`modules/08_data_and_rag.md`](modules/08_data_and_rag.md).

---

## 6. Legal Agent

**Mục đích:** thẩm định điều kiện pháp lý/KYC — phát hiện thiếu đăng ký kinh doanh, thiếu UBO, thiếu báo cáo tài chính khi khách hàng cần sản phẩm tín dụng — và tạo bằng chứng dẫn chiếu đúng điều khoản.

**Đã build:**
- [`app/agents/legal_agent.py`](../app/agents/legal_agent.py) — kiểm tra 3 rule cứng: `RULE-BUSINESS-REG` (thiếu/không hợp lệ đăng ký kinh doanh), `RULE-UBO` (thiếu thông tin chủ sở hữu hưởng lợi), `RULE-CREDIT-FS` (thiếu báo cáo tài chính **chỉ khi** Product Agent đã đề xuất `PROD-WORKING-CAPITAL`). Mỗi lỗi gắn `severity: blocking`, sinh `EvidenceItem` trỏ đúng policy trong `SYNTHETIC_COMPLIANCE_POLICIES`.
- [`app/tools/legal_tools.py`](../app/tools/legal_tools.py) — `validate_business_registration()` (so khớp mã số thuế), `check_document_expiry()` (tính ngày hết hạn), `search_compliance_policy()`.

**Cần build thêm:**
- [ ] Mới có 3 rule; plan gốc còn nhắc watchlist/PEP/sanction mock (mục 5.4 trong đề xuất gốc) — chưa có trong code. Nếu muốn demo phần này, cần thêm 1 rule + 1 mock danh sách đen.
- [ ] `check_document_expiry()` hiện chưa được `LegalAgent.run()` gọi cho tài liệu ngoài đăng ký kinh doanh (vd. giấy uỷ quyền hết hạn) — coverage 75% ở `legal_tools.py` phản ánh đúng chỗ chưa dùng hết.
- [ ] Người đại diện/uỷ quyền (representatives trong `MOCK_COMPANIES`) có field `authority_limit` nhưng **chưa có rule nào kiểm tra hạn mức uỷ quyền** — đây là mục 17 điểm 15-16 trong plan gốc ("nhầm người đại diện và người được uỷ quyền") chưa được code.

**Đọc thêm:** [`modules/04_legal_agent.md`](modules/04_legal_agent.md).

---

## 7. Operations Agent

**Mục đích:** sau khi có kết quả Product + Legal, tạo checklist hồ sơ còn thiếu, soạn email nháp gửi khách hàng, và chuẩn bị payload case/task cho CRM — chỉ tạo **nháp**, không tự gửi/tạo gì thật.

**Đã build:**
- [`app/agents/operations_agent.py`](../app/agents/operations_agent.py) + [`app/tools/operations_tools.py`](../app/tools/operations_tools.py) — `get_required_documents()` gộp checklist theo sản phẩm được chọn, `check_document_completeness()` so với tài liệu đã upload, `draft_customer_email()` sinh email có bullet danh sách thiếu, `SLA_HOURS` gán SLA cứng theo loại task (missing_information=24h, open_service=48h, credit_review=72h) — **không để LLM tự bịa SLA**, đúng nguyên tắc deterministic rule trong plan gốc.

**Cần build thêm:**
- [ ] Email hiện chỉ có 1 template cố định — nếu muốn cá nhân hoá theo từng sản phẩm/mức rủi ro, cần thêm biến thể template.
- [ ] Chưa có cơ chế gửi email thật kể cả ở dạng "gửi nội bộ để review" (`EmailService.send_draft_email` trong `mock_services.py` chỉ log ra console, chưa được `OperationsAgent` gọi tới) — nối 2 phần này lại nếu muốn demo email nháp xuất hiện trong log rõ ràng hơn.

**Đọc thêm:** [`modules/05_operations_agent.md`](modules/05_operations_agent.md).

---

## 8. Evidence Validator — MỘT PHẦN, cần chú ý khi demo

**Mục đích:** lớp kiểm soát độc lập, đối chiếu mọi `claim` của Product/Legal Agent với văn bản nguồn gốc để chặn ảo giác (hallucination) trước khi RM nhìn thấy.

**Đã build:**
- [`app/safety/evidence_validator.py`](../app/safety/evidence_validator.py) — `EvidenceValidator.validate()`: với mỗi `EvidenceItem`, tra `(source_doc, section)` trong bộ nguồn nội bộ (ghép từ catalog + policy), rồi kiểm tra `quote` có xuất hiện **y nguyên văn bản** trong nguồn hay không (`quote in source_text`). Nếu không khớp → `is_valid=False` + ghi `hallucination_flag` vào audit log.

**Cần build thêm — quan trọng, nên biết trước khi pitch:**
- [ ] Đây mới là **Lớp 1/3** theo thiết kế gốc ([`modules/06_evidence_guardrails_approval.md`](modules/06_evidence_guardrails_approval.md) — "Phương thức kiểm tra kết hợp"). Lớp 2 (semantic similarity, ngưỡng cosine 0.85) và Lớp 3 (LLM-as-judge chấm nhị phân) **chưa tồn tại**. Vì hiện tại `claim`/`quote` đều do chính code sinh ra (không phải LLM tự do viết lại), exact-match vẫn an toàn cho MVP — nhưng nếu sau này có LLM sinh văn bản tự do, chỉ dùng Lớp 1 sẽ chặn nhầm rất nhiều câu đúng ý nhưng diễn đạt khác.
- [ ] Khi pitch/demo, nên nói đúng là "exact-citation matching", tránh nói "3-layer hybrid validation" như plan gốc mô tả — hiện chưa đúng thực tế.

**Đọc thêm:** [`modules/06_evidence_guardrails_approval.md`](modules/06_evidence_guardrails_approval.md) mục 19.

---

## 9. Tool Registry / phân quyền gọi tool — MỘT PHẦN, có lỗ hổng cần vá

**Mục đích:** đảm bảo agent chỉ được gọi đúng tool trong phạm vi được phép (vd. Product Agent không được tự gọi `create_case` trên CRM).

**Đã build:**
- [`app/tools/registry.py`](../app/tools/registry.py) — `ToolRegistry.register(name, function, *owners)` và `ToolRegistry.call(owner, name, **kwargs)` raise `ToolPermissionError` nếu `owner` không nằm trong allowlist của `name`. Cơ chế đúng, có test xác nhận hoạt động (`tests/test_end_to_end.py::test_tool_registry_blocks_privilege_escalation`).

**Cần build thêm — ưu tiên cao:**
- [ ] **`ToolRegistry` hiện không được instantiate hay gọi ở bất kỳ đâu trong `app/agents`, `app/services`, `app/main.py`.** Tất cả agent đang import và gọi thẳng hàm nghiệp vụ (`validate_business_registration`, `get_required_documents`, `CRMService.create_case`...). Nghĩa là allowlist mới đúng trên lý thuyết/unit test cô lập, **không chặn gì trên luồng chạy thật.**
- [ ] Việc cần làm: tạo 1 instance `ToolRegistry` dùng chung (vd. trong `app/tools/__init__.py`), `register()` toàn bộ tool nghiệp vụ với đúng owner (Product/Legal/Operations), rồi sửa từng agent + `ActionExecutor` gọi qua `registry.call(self.owner, "tool_name", **kwargs)` thay vì import trực tiếp. Sau khi xong, viết lại test 34.3 (Product Agent bị ép gọi `create_case`) để chạy trên registry thật thay vì registry dựng riêng trong test.

**Đọc thêm:** [`modules/07_tools_and_shared_state.md`](modules/07_tools_and_shared_state.md) mục 22, [`modules/10_evaluation_and_testing.md`](modules/10_evaluation_and_testing.md) mục 34.3 (kịch bản test tương ứng).

---

## 10. Approval Flow + Action Executor

**Mục đích:** đảm bảo không hành động nghiệp vụ nào (tạo case/task thật) chạy nếu chưa có RM bấm duyệt — đây là gate Human-in-the-loop bắt buộc.

**Đã build:**
- [`app/services/approval.py`](../app/services/approval.py) — `ApprovalService.issue()`/`verify()`: token dạng `base64(payload).hmac_sha256`, có `case_id`, `rm_id`, hạn `APPROVAL_TOKEN_TTL_SECONDS` (mặc định 300s), verify bằng `hmac.compare_digest` (an toàn trước timing attack). `ActionExecutor.execute()`: gọi `GuardrailGate.can_execute()` trước, chỉ khi pass mới gọi `CRMService.create_case`/`create_task`.

**Cần build thêm:**
- [ ] Token issue/verify đang chạy tốt nhưng `APPROVAL_SECRET` mặc định trong `.env.example` là placeholder — **phải đổi giá trị thật khi deploy demo công khai**, không dùng giá trị mẫu.
- [ ] Chưa có cơ chế revoke token đã issue nhưng chưa dùng (vd. RM bấm duyệt 2 lần) — rủi ro thấp cho demo nhưng nên biết.

**Đọc thêm:** [`modules/06_evidence_guardrails_approval.md`](modules/06_evidence_guardrails_approval.md) mục 21.

---

## 11. Orchestrator

**Mục đích:** "nhạc trưởng" nối toàn bộ pipeline — route → planner → product/legal → validator → adapt → operations → set trạng thái cuối. Đây là nơi duy nhất hiểu toàn bộ luồng end-to-end.

**Đã build:**
- [`app/services/orchestrator.py`](../app/services/orchestrator.py) — `CaseOrchestrator.run()`. Điểm đáng chú ý: mỗi lần `run()` được gọi lại (vd. sau khi RM bổ sung hồ sơ qua `/resume`) sẽ **reset các field dẫn xuất** (execution_plan, product/legal/operations_result, evidences...) nhưng giữ nguyên `audit_log` và case context — tức là chạy lại toàn bộ suy luận trên dữ liệu mới, không cố "vá" kết quả cũ.

**Cần build thêm:**
- [ ] Route `"simple"` hiện chỉ chạy Product Agent + Evidence Validator, bỏ qua Legal/Operations hoàn toàn — đúng thiết kế cho tra cứu đơn giản, nhưng nếu sau này có câu hỏi đơn giản thuộc domain Legal (vd. "phí KYC bao nhiêu"), route này sẽ không có agent nào trả lời đúng. Cân nhắc thêm route "simple-legal" nếu phát sinh nhu cầu.
- [ ] Chưa có giới hạn số lần gọi `/resume` liên tiếp (khác với `max_loops` bên trong Planner) — nên thêm nếu lo ngại demo bị loop.

**Đọc thêm:** [`modules/01_architecture.md`](modules/01_architecture.md) (Sơ đồ 1, Sơ đồ 2).

---

## 12. API Layer (FastAPI)

**Mục đích:** expose toàn bộ workflow qua HTTP cho UI và cho việc test tự động.

**Đã build:** [`app/main.py`](../app/main.py) — 7 endpoint:

| Method | Endpoint | Việc | Test? |
|---|---|---|---|
| GET | `/health` | Kiểm tra sống | Có |
| GET | `/` | Trả UI demo (`static/index.html`) | Không |
| POST | `/api/v1/cases` | Tạo case, chạy orchestrator | Có |
| GET | `/api/v1/cases` | Liệt kê case (lọc theo `rm_id`) | Không |
| GET | `/api/v1/cases/{case_id}` | Xem state đầy đủ | Không |
| POST | `/api/v1/cases/{case_id}/resume` | Bổ sung hồ sơ, chạy lại | Có |
| POST | `/api/v1/cases/{case_id}/approval-token` | Xin token duyệt | Có |
| POST | `/api/v1/cases/{case_id}/approve` | Duyệt + thực thi mock action | Có |
| POST | `/api/v1/cases/{case_id}/reject` | Từ chối case | Không |
| GET | `/api/v1/search/products` | Product RAG trực tiếp | Không |

**Cần build thêm:**
- [ ] 4 endpoint chưa có test (`GET /cases`, `GET /cases/{id}`, `POST /reject`, `GET /search/products`) — coverage `app/main.py` đang 77%, đúng bằng phần này.
- [ ] Chưa có phân trang cho `GET /api/v1/cases` — không vấn đề với demo (ít case) nhưng sẽ chậm nếu tạo nhiều case.

**Đọc thêm:** [`modules/09_api_ui_error_observability.md`](modules/09_api_ui_error_observability.md).

---

## 13. Frontend / RM Workspace UI — MỘT PHẦN

**Mục đích:** giao diện để RM demo trực tiếp thay vì gọi API bằng tay.

**Đã build:**
- [`app/static/index.html`](../app/static/index.html) — 1 file HTML/CSS/JS thuần (22 dòng, không framework), có đủ 3 nút thao tác chính: **Phân tích case** (POST `/cases`), **Bổ sung UBO + BCTC** (POST `/resume`), **RM Approve** (xin token rồi POST `/approve`). Kết quả hiển thị dạng JSON thô trong khối `<pre>`.

**Cần build thêm — đây là khối yếu nhất về mặt trải nghiệm, phù hợp cho Người 4:**
- [ ] Chưa có **Evidence Panel** như plan gốc mô tả (mục 28: đề xuất bên trái, đoạn trích dẫn nguồn bên phải, tô xanh khi Validator xác nhận) — hiện chỉ có JSON thô.
- [ ] Chưa có **Missing Information Drawer** trực quan (danh sách đỏ + nút gửi yêu cầu bổ sung) — hiện phải tự đọc trong JSON.
- [ ] Chưa có Timeline/Trace hiển thị từng bước Planner → Product → Legal → Validator → Operations — audit_log có đủ dữ liệu, chỉ thiếu phần hiển thị.
- [ ] Dropdown khách hàng đang hard-code 2 công ty mẫu (`COMP-ABC`, `COMP-XYZ`) khớp với `MOCK_COMPANIES` — nếu Người 2/3 thêm công ty mẫu mới, nhớ cập nhật cả dropdown này.

**Đọc thêm:** [`modules/09_api_ui_error_observability.md`](modules/09_api_ui_error_observability.md) mục 28.

---

## 14. Mock external services

**Mục đích:** giả lập Core Banking (hồ sơ công ty), CRM (tạo case/task) và Email — để demo không phụ thuộc hệ thống SHB thật.

**Đã build:** [`app/services/mock_services.py`](../app/services/mock_services.py) — `MOCK_COMPANIES` (COMP-ABC thiếu UBO/BCTC để demo nhánh pending_information; COMP-XYZ đầy đủ để demo nhánh pass thẳng), `CoreBankingService.get_company_profile()`, `CRMService.create_case()`/`create_task()` (sinh ID giả `CRM-CASE-xxxxxx`), `EmailService.send_draft_email()` (mới log ra console).

**Cần build thêm:**
- [ ] Chỉ có 2 công ty mẫu — nên thêm ít nhất 3-5 công ty nữa (nhiều ngành/quy mô khác nhau) nếu muốn test Product Agent đa dạng hơn, đúng khuyến nghị "5-10 hồ sơ doanh nghiệp" trong đề xuất gốc.
- [ ] `EmailService.send_draft_email()` chưa được gọi ở đâu trong luồng thật (xem Khối 7).

**Đọc thêm:** [`modules/08_data_and_rag.md`](modules/08_data_and_rag.md).

---

## 15. Testing

**Mục đích:** đảm bảo mỗi thay đổi không phá vỡ luồng đã chạy được.

**Đã build (4 file, 16 test, coverage 91% — đã tự chạy lại xác nhận, không chỉ tin số tự báo cáo):**
- [`tests/test_planner_agent.py`](../tests/test_planner_agent.py) — DAG hợp lệ, phát hiện cycle, blocking pause, escalation, giới hạn retry.
- [`tests/test_product_rag.py`](../tests/test_product_rag.py) — retrieval đúng sản phẩm, có citation, lọc câu ngoài phạm vi, chuẩn hoá query.
- [`tests/test_end_to_end.py`](../tests/test_end_to_end.py) — case ABC đầy đủ (thiếu UBO/BCTC → resume → approve → mock CRM), chặn prompt injection, evidence validator phát hiện nguồn lạ, tool registry chặn vượt quyền (cô lập — xem Khối 9).
- [`tests/test_api.py`](../tests/test_api.py) — vòng đời case qua HTTP thật (`TestClient`), kiểm tra RM khác không truy cập được case của người khác.

**Cần build thêm:**
- [ ] Golden dataset 40 case theo đúng benchmark trong plan gốc ([`modules/10_evaluation_and_testing.md`](modules/10_evaluation_and_testing.md) mục 32/34: 10 đơn giản, 10 đa domain, 10 thiếu hồ sơ, 5 rủi ro cao, 5 adversarial) — hiện có 16 test nhắm đúng các kịch bản trọng tâm nhưng chưa đủ số lượng/độ phủ để gọi là "golden benchmark".
- [ ] Test cho 4 API endpoint còn thiếu (Khối 12).
- [ ] Chưa có test đo latency/cost dù plan gốc có NFR-1 (dưới 30s) — vì hệ thống hiện deterministic nên rất nhanh, nhưng nên có 1 test/benchmark ghi lại con số thật để trích dẫn khi pitch.

Chạy test: `pytest -q` (nhanh) hoặc `pytest --cov=app --cov-report=term-missing -q` (có coverage).

---

## 16. DevOps / Deployment / Config

**Mục đích:** cài đặt, chạy và đóng gói hệ thống nhất quán giữa các máy trong team.

**Đã build:**
- [`Dockerfile`](../Dockerfile) — build image `python:3.11-slim`, cài `requirements.txt`, chạy `uvicorn`.
- [`docker-compose.yml`](../docker-compose.yml) — 1 service `workspace`, map port 8000, đọc `.env`.
- [`requirements.txt`](../requirements.txt) (runtime tối thiểu: fastapi/uvicorn/pydantic/pytest/httpx) tách riêng khỏi [`requirements-optional.txt`](../requirements-optional.txt) (langgraph/langchain/chromadb — chưa dùng, dành cho nâng cấp sau).
- [`.env.example`](../.env.example) — `APPROVAL_SECRET`, `APPROVAL_TOKEN_TTL_SECONDS`, `HOST`, `PORT`, `LOG_LEVEL`.

**Cần build thêm:**
- [ ] `docker-compose.yml` chưa có volume cho DB thật (vì đang in-memory) — cần thêm khi chuyển sang PostgreSQL.
- [ ] Chưa có CI (GitHub Actions) chạy `pytest` tự động khi push — nên thêm ngay sau khi có git repo (Khối 17), để tránh commit code làm vỡ test mà không ai biết.
- [ ] Chưa có healthcheck trong `docker-compose.yml` dù `/health` endpoint đã có sẵn — chỉ cần thêm vài dòng cấu hình.
- [ ] `app/config.py` vẫn còn field `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `VECTOR_DB_DIR`... không dùng ở đâu trong MVP hiện tại — nên dọn để tránh hiểu lầm là đã tích hợp LLM thật.

**Đọc thêm:** [`README.md`](../README.md) mục "Chạy local".

---

## 17. Version control & nộp bài (git, AI_LOG) — CHƯA CÓ, ƯU TIÊN SỐ 1

**Mục đích:** đây không phải một khối kỹ thuật, mà là điều kiện bắt buộc để nộp bài VAIC 2026 — không có git thì không có lịch sử build để chứng minh, không có `AI_LOG.md` thì thiếu hẳn 1 hạng mục chấm điểm.

**Hiện trạng:** repo chưa `git init`. Chưa có `AI_LOG.md`.

**Cần làm ngay (bất kỳ ai rảnh tay trước có thể làm, không cần hiểu code):**
- [ ] `git init`, tạo `.gitignore` đã có sẵn ở root, `git add`, commit đầu tiên.
- [ ] Tạo `AI_LOG.md` ở root theo đúng template trong [`docs/VAIC_README_AI_LOG_PROMPT.md`](../docs/VAIC_README_AI_LOG_PROMPT.md) — điền các mốc đã build (tham khảo decision log/deviation log có sẵn trong [`PROGRESS.md`](PROGRESS.md) mục 3-4, đã đúng định dạng audit-được).
- [ ] Từ giờ, mỗi tính năng lớn hoàn thành → 1 commit riêng, message rõ ràng — để `AI_LOG.md` có thể trỏ tới commit hash thật thay vì placeholder.
- [ ] Cân nhắc đẩy lên GitHub riêng tư/công khai và có live URL trước hạn nộp — cả hai hiện đều chưa có.

**Đọc thêm:** [`docs/VAIC_README_AI_LOG_PROMPT.md`](../docs/VAIC_README_AI_LOG_PROMPT.md) (toàn bộ file là hướng dẫn cho khối này).
