# PROGRESS — Trạng thái build SHB Corporate Expert Workspace

Đây là tài liệu **sống**, cập nhật liên tục trong lúc build. Mục đích: khi một phiên AI-coding mới bắt đầu (hoặc context bị compact giữa chừng), chỉ cần đọc file này (ngắn) + `INDEX.md` để biết ngay: đã làm gì, đang làm gì, quyết định gì đã chốt, còn vướng gì — thay vì phải đọc lại toàn bộ 1156 dòng plan.

Cập nhật file này ngay sau khi hoàn thành hoặc thay đổi một task, không đợi cuối phiên.

## 1. Trạng thái tổng quan

| Trường | Giá trị |
|---|---|
| Cập nhật lần cuối | `2026-07-17` |
| Giai đoạn hiện tại (theo `11_roadmap_and_backlog.md`) | `MVP end-to-end — verified` |
| Module đang làm | `Không có — MVP đã bàn giao, backlog production còn mở` |
| Blocker hiện tại | `Không có blocker đối với hackathon MVP` |

## 2. Backlog tracker (đồng bộ ID với `11_roadmap_and_backlog.md`, mục 35)

| ID | Task | Module liên quan | Status | Ghi chú / lệch so với plan |
|---|---|---|---|---|
| TSK-001 | Định nghĩa Shared Case State schema | `07_tools_and_shared_state.md` | Done | Pydantic state, task/evidence, trace, audit, approval và timestamps |
| TSK-002 | RAG pipeline tài liệu sản phẩm | `08_data_and_rag.md` | In Progress | `MVP ProductRAGService: normalize, hybrid dense/sparse-lite, rerank, threshold, citations; persistent index chưa có` |
| TSK-003 | Parser trích xuất ĐKKD | `00_context_and_business.md`, `09_api_ui_error_observability.md` | To Do | MVP nhận metadata đã trích xuất; chưa parse PDF/PNG/OCR |
| TSK-004 | Prompt + logic Planner Agent | `02_planner_agent.md` | Done | `app/services/planner_agent.py`; deterministic DAG, blocking/escalation, max loop` |
| TSK-005 | Product Agent matching | `03_product_agent.md` | Done | Deterministic matching + Product RAG + citations; synthetic catalog |
| TSK-006 | Legal Agent KYC/UBO | `04_legal_agent.md` | Done | KYC/UBO/BCTC/business-registration rules; synthetic policy |
| TSK-007 | Evidence Validator (citation matching) | `06_evidence_guardrails_approval.md` | Done | Exact source/section/quote validation + hallucination flag |
| TSK-008 | Complexity Router | `01_architecture.md`, `02_planner_agent.md` | Done | Simple product lookup vs complex multi-agent flow |
| TSK-009 | Mock APIs CRM/Task/Email | `07_tools_and_shared_state.md`, `09_api_ui_error_observability.md` | Done | Mock CRM case/task; signed approval token trước executor |
| TSK-010 | RM Workspace UI + Trace | `09_api_ui_error_observability.md` | Done | Hackathon UI: create, resume UBO/BCTC, approve, JSON trace |

Cập nhật `Status` theo: `To Do → In Progress → Blocked → Done`. Khi `Blocked`, ghi lý do vào cột Ghi chú.

## 3. Quyết định đã chốt (decision log)

Ghi mỗi quyết định kỹ thuật quan trọng (khác với plan gốc, hoặc chọn 1 trong nhiều phương án mà plan để mở) tại đây, mới nhất lên đầu.

```
### <NGÀY GIỜ> — <TIÊU ĐỀ QUYẾT ĐỊNH>
- Bối cảnh: <TẠI SAO CẦN QUYẾT ĐỊNH>
- Phương án đã chọn: <PHƯƠNG ÁN>
- Lý do: <VÌ SAO>
- Ảnh hưởng tới module: <TÊN FILE modules/...>
```

### 2026-07-17 — Planner deterministic core
- Bối cảnh: MVP cần tạo execution plan trước khi tích hợp các specialist agent/LLM.
- Phương án đã chọn: rule-based planner với Pydantic SharedCaseState; giữ DAG validation và safety transitions deterministic.
- Lý do: planner không được gọi business tool trực tiếp; dễ kiểm thử và tránh lộ chain-of-thought.
- Ảnh hưởng tới module: `modules/02_planner_agent.md`, `modules/07_tools_and_shared_state.md`.

## 4. Lệch khỏi plan gốc (deviation log)

Nếu code thực tế phải khác plan (do giới hạn thời gian 48h, do API mock không hỗ trợ, do phát hiện lỗi thiết kế...), ghi ở đây thay vì âm thầm sửa `SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md`.

```
### <NGÀY GIỜ> — <MODULE/MỤC BỊ LỆCH>
- Plan gốc yêu cầu: <TRÍCH Ý>
- Thực tế build: <ĐÃ LÀM GÌ KHÁC>
- Lý do: <VÌ SAO KHÔNG THEO ĐÚNG PLAN>
- Cần quay lại xử lý sau hackathon không: <CÓ/KHÔNG>
```

Các deviation đã được ghi chi tiết bên dưới: RAG fallback in-memory và runtime deterministic thay cho LangGraph/Chroma thật.

## 5. Việc đã xác minh chạy được (evidence of working code)

| Thành phần | Đã chạy thử? | Cách test | Kết quả |
|---|---|---|---|
| Planner Agent | Có | `pytest -q` | Pass: DAG, dependency, cycle fallback, max loop |
| Product Agent + RAG | Có | `pytest -q` | Pass: Payroll/Cash Management/Working Capital, citation, out-of-scope |
| Legal Agent | Có | `pytest -q` | Pass: phát hiện UBO/BCTC; resume chuyển sang passed |
| Operations Agent | Có | `pytest -q` | Pass: checklist, email nháp, SLA deterministic |
| Evidence Validator | Có | `pytest -q` | Pass: source/section/quote và hallucination flag |
| Guardrails/Tool permission | Có | `pytest -q` | Pass: prompt injection chặn; `ToolRegistry` allowlist giờ chặn thật trên đường chạy của Legal/Operations (không chỉ registry dựng riêng trong test) — xem mục 6, 2026-07-17 (theo dõi) |
| FastAPI lifecycle | Có | `pytest -q tests/test_api.py` | Pass: create → resume → token → approve → mock CRM |
| End-to-end case ABC (kịch bản 34.1) | Có | `pytest -q tests/test_end_to_end.py` | Pass |
| Tổng test/coverage | Có | `pytest --cov=app --cov-report=term-missing -q` | V1: `19 passed` (`pytest tests/test_api.py tests/test_end_to_end.py tests/test_planner_agent.py tests/test_product_rag.py -q`), coverage 100% cho `evidence_validator.py`/`registry.py`/`product_tools.py`. Toàn repo (V1+V2): `76 passed`, `95%` |

## 6. Việc còn thiếu / rủi ro đang mở

Đồng bộ với `12_risks_assumptions_open_questions.md`. Chỉ liệt kê ở đây các rủi ro đang **thực sự chặn tiến độ build**, không lặp lại toàn bộ bảng risk trong plan.

Không còn blocker cho hackathon MVP. Các việc còn thiếu là backlog nâng cấp production: PDF/OCR ingestion, persistent vector index, policy thật, persistent DB, enterprise auth/observability và golden benchmark 40 cases.

### 2026-07-17 — Audit độc lập (re-grade repo)

Đã chạy lại `pytest --cov=app` độc lập và xác nhận đúng `16 passed`, coverage `91%` như bảng mục 5 (không phải số tự khai). Phát hiện thêm 2 gap về guardrail chưa được ghi trong log trước đó:

- **`ToolRegistry` (`app/tools/registry.py`) được định nghĩa và có test (`test_tool_registry_blocks_privilege_escalation`) nhưng không được instantiate/gọi ở bất kỳ đâu trong `app/agents`, `app/services` hay `app/main.py`.** Các agent gọi thẳng hàm nghiệp vụ (vd. `validate_business_registration`, `get_required_documents`) chứ không qua `registry.call(owner, name, ...)`. Nghĩa là cơ chế "allowed-tool allowlist" mới đúng ở mức unit test cô lập, **chưa thực sự chặn gì trên luồng chạy thật** — kịch bản 34.3 (Product Agent bị ép gọi `create_case`) chưa được chứng minh end-to-end như plan mô tả.
- **`EvidenceValidator` (`app/safety/evidence_validator.py:22`) mới cài Lớp 1/3 (deterministic exact-quote match)** theo thiết kế "Hybrid Validation" ở `06_evidence_guardrails_approval.md`. Lớp 2 (semantic cosine ≥0.85) và Lớp 3 (LLM-as-judge) chưa có. Đây là lựa chọn an toàn theo hướng thà chặn nhầm còn hơn bỏ sót (chỉ chấp nhận trích dẫn khớp y nguyên văn bản), nhưng chưa được nêu rõ là simplification trong README/PROGRESS trước đợt audit này.
- Repo chưa `git init`, chưa có `AI_LOG.md` — rủi ro cho việc nộp bài VAIC 2026 (cần lịch sử commit + AI collaboration log). Cập nhật 2026-07-17 (theo dõi): repo đã có `git init` + lịch sử commit từ đợt build multi-agent (xem `git log`), `AI_LOG.md` **vẫn chưa tồn tại** — vẫn còn mở.

### 2026-07-17 (theo dõi) — Đóng 2 gap guardrail đã phát hiện ở audit độc lập trên

Trước khi build sang V2-004, đã kiểm tra lại toàn repo (V1 lẫn V2) theo yêu cầu người dùng và sửa 2 gap đã ghi ở mục audit phía trên:

- **`ToolRegistry` giờ được wire thật.** Thêm `build_default_registry()` (`app/tools/registry.py`) đăng ký 5 tool thật (`validate_business_registration`, `check_document_expiry` → Legal; `get_required_documents`, `check_document_completeness`, `draft_customer_email` → Operations). `CaseOrchestrator.__init__` dựng 1 registry dùng chung, truyền vào `LegalAgent(tools=...)`/`OperationsAgent(tools=...)`; 2 agent này gọi qua `self.tools.call(self.owner, name, **kwargs)` thay vì import hàm trực tiếp. Test mới `test_default_tool_registry_enforces_owner_boundaries` (`tests/test_end_to_end.py`) chứng minh registry mà orchestrator dùng thật sự chặn cross-owner call (vd. Product không gọi được `draft_customer_email`), không chỉ registry dựng riêng trong test như trước. **Phạm vi có chủ đích:** Product Agent đọc `SHB_PRODUCT_CATALOG` (dict hằng, đọc-only) và gọi `ProductRAGService.search()` không đi qua registry — đây không phải hành động xuyên biên giới/ra ngoài hệ thống như ví dụ "Product Agent gọi CRM tạo case" trong plan gốc, nên không đưa vào allowlist. Đồng thời xoá 3 hàm tool "chết" chưa từng được gọi (`search_product_catalog`, `retrieve_product_policy` ở `product_tools.py`; `search_compliance_policy` ở `legal_tools.py`) — trùng chức năng với `ProductRAGService`/truy cập dict trực tiếp đã dùng thật, giữ lại chỉ gây hiểu nhầm là "đã implement".
- **Evidence Validator có thêm Lớp 2 (semantic-similarity fallback).** Dùng lại kỹ thuật hash-embedding + cosine của `app/rag/product_retriever.py` (không gọi model/API ngoài), so khớp quote với từng *segment* nguồn (name/description/eligibility_rules/từng required_document) và lấy điểm cao nhất — so với cả đoạn văn bản gộp sẽ làm loãng điểm số (đã tự kiểm chứng bằng script: quote đúng y nguyên chỉ đạt ~0.64 nếu so với văn bản gộp, nhưng đạt 1.0 nếu so theo từng segment). Ngưỡng giữ đúng `0.85` như plan gốc, đã kiểm chứng thực nghiệm: quote lệch case/dấu câu nhưng cùng nội dung → 1.0 (được cứu, không còn bị Lớp 1 gắn nhầm là ảo giác); quote bịa dùng từ vựng cùng miền → 0.16–0.44 (vẫn bị từ chối đúng). **Giới hạn thành thật còn lại:** đây là bag-of-tokens hash, không phải embedding ngữ nghĩa thật — một câu diễn giải lại hoàn toàn bằng từ khác (không trùng token) chỉ đạt ~0.68, dưới ngưỡng, nên **chưa cứu được paraphrase thật sự** (chấp nhận thiên về từ chối nhầm hơn là bỏ sót ảo giác). Lớp 3 (LLM-as-a-judge) **vẫn cố ý chưa làm** — cần gọi LLM thật, đợi quyết định OpenAI key ở track V2 (xem mục 2026-07-17 dưới), tránh xây 2 chỗ gọi LLM khác kiểu trong 2 track cùng lúc. Test mới: `test_evidence_validator_layer2_rescues_case_and_punctuation_paraphrase`, `test_evidence_validator_layer2_still_rejects_fabricated_claim_with_overlapping_vocabulary` (`tests/test_end_to_end.py`).
- Đã đồng bộ `.env.example` với các biến `app/config.py` thực sự đọc (`OPENAI_API_KEY`, `GOOGLE_API_KEY`, `DEFAULT_LLM`, `OPENAI_MODEL`, `GOOGLE_MODEL`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `VECTOR_DB_DIR`) — trước đó `.env.example` chỉ có 5 biến approval/host, thiếu hoàn toàn các biến LLM đã có sẵn trong code. Thêm `openai==2.46.0` (bản pip resolve thật, không đoán số) vào `requirements.txt` và cài vào `.venv` — đây là chuẩn bị nền cho V2-004, **chưa viết LLM client wrapper/prompt** (việc đó thuộc phạm vi V2-004).
- Đã thêm `outputs/` vào `.gitignore` (thư mục render/export proposal do `tools/` sinh ra — hàng trăm PNG + PDF + 1 file khoá tạm Word `~$...docx` — chưa từng được track, dễ bị commit nhầm nếu ai đó `git add -A`).
- **Chưa xử lý, cần quyết định của người dùng:** toàn bộ code V2-001/002/003 (`app/context/`, `app/integrations/`, `app/schemas/v2/`, `tests/contract/`, `tests/unit/`) và các sửa đổi ở trên hiện **chưa commit**, đang nằm trên nhánh `main` cục bộ. Rủi ro mất việc nếu có thao tác git phá huỷ; chưa chia sẻ được cho đồng đội. Đây không phải lỗi kỹ thuật mà là quyết định "khi nào commit/push" — xem báo cáo gửi người dùng.

RAG_VSF đã được tham khảo theo pipeline `QueryNormalizer → HybridFusion → HeuristicReranker → ContextBuilder`. Đã áp dụng phiên bản local-first không network/model dependency vào `app/rag/product_retriever.py` để làm nền cho Product Agent.

### 2026-07-17 — RAG_VSF-inspired local-first retrieval
- Plan gốc yêu cầu Product Catalog RAG, nhưng code khung chưa có ingestion/index.
- Thực tế build: tạo retrieval service trên catalog synthetic hiện có, dùng hash embedding deterministic + sparse token overlap, source metadata và threshold out-of-scope.
- Lý do: đảm bảo chạy offline trong MVP, không thêm dependency nặng hay gọi API ngoài.
- Cần quay lại xử lý sau hackathon không: Có — thay hash embedding bằng multilingual-e5/FAISS hoặc Chroma, thêm ingestion/versioning/eval retrieval.

### 2026-07-17 — Tách runtime MVP khỏi optional AI stack
- Plan gốc yêu cầu: LangGraph + Chroma trong runtime kiến trúc đề xuất.
- Thực tế build: orchestration deterministic chạy bằng service layer; `requirements.txt` chỉ giữ FastAPI/Pydantic/test, stack LangGraph/Chroma/LangChain chuyển sang `requirements-optional.txt`.
- Lý do: code MVP chưa import các thư viện nặng này; tách dependency giúp cài/chạy/test ổn định và tránh tuyên bố đã tích hợp vector DB khi chưa có.
- Cần quay lại xử lý sau hackathon không: Có, khi triển khai persistent vector RAG và graph runtime thật.

## 7. Giới hạn hiện tại cần giữ trong mọi báo cáo/demo

| Hạng mục | Trạng thái | Lưu ý bắt buộc |
|---|---|---|
| Embedding | MVP fallback | Hash embedding deterministic, chưa phải multilingual-e5/embedding production |
| Vector index | Chưa có | Catalog đang in-memory, chưa có FAISS/Chroma persistent index |
| Ingestion PDF/OCR | Chưa có | API chỉ nhận metadata/text tài liệu có cấu trúc; chưa parse PDF/PNG thật |
| Product Agent | Có ở mức MVP | Matching deterministic + RAG; catalog là `SYNTHETIC DEMO DATA` |
| Legal Agent | Có ở mức MVP | KYC/UBO/BCTC rules là policy giả lập, không phải quy định SHB thật |
| Operations Agent | Có ở mức MVP | Chỉ sinh checklist/email/CRM draft; không gửi email thật |
| API/UI end-to-end | Có ở mức MVP | FastAPI + UI demo; chưa có SSO, enterprise RBAC hoặc frontend production |
| Storage | MVP in-memory | Case mất khi process restart; chưa có PostgreSQL/audit store bất biến |
| Observability | Một phần | Có trace_id và audit log; chưa có OpenTelemetry, Jaeger/LangSmith, dashboard/alert |
| Evaluation | Một phần | Có unit/integration/security tests; chưa có 40-case golden dataset và benchmark RAG |
| Tool permission enforcement | Một phần | `ToolRegistry` wire thật vào Legal+Operations qua `CaseOrchestrator` (2026-07-17); Product's catalog/RAG access có chủ đích không đi qua allowlist (đọc-only, không phải hành động ra ngoài) |
| Evidence Validator (3-layer) | Một phần | Lớp 1 (exact-match) + Lớp 2 (semantic hash-similarity, ngưỡng 0.85, đã kiểm chứng thực nghiệm) xong (2026-07-17); Lớp 3 (LLM-as-judge) vẫn chưa làm, chờ quyết định OpenAI key ở V2 |
| Version control / AI_LOG | Một phần | Repo đã `git init` + có lịch sử commit; `AI_LOG.md` **vẫn chưa tồn tại** — cần trước khi nộp bài VAIC |
| Production readiness | Chưa | Không được mô tả hệ thống là production-ready cho đến khi đóng các mục trên |

## 8. Artifact đã tạo trong đợt build end-to-end

- `app/agents/`: Product, Legal, Operations agents.
- `app/rag/`: Product retrieval local-first có threshold và citation context.
- `app/safety/`: evidence validator và input/output guardrails.
- `app/services/orchestrator.py`: workflow từ route đến pending information/approval.
- `app/services/approval.py`: approval token HMAC và guarded mock executor.
- `app/main.py`, `app/static/index.html`: FastAPI API và RM Workspace demo.
- `tests/`: Planner, RAG, security, workflow và API lifecycle.
- `README.md`, `.env.example`, `Dockerfile`, `docker-compose.yml`: hướng dẫn cấu hình/chạy/đóng gói.
