# RAG & Guardrail Implementation Report

**Trạng thái thật (cập nhật sau Phase 2):**

| Phase | Trạng thái |
| --- | --- |
| Phase 0 (provider failure taxonomy) | **IMPLEMENTED**, có test, verified_by_execution |
| Phase 0.5 (Trust Foundation & V3 Integration) | **IMPLEMENTED**, E2E tested, verified_by_execution (558/558 tests passed) |
| Phase 1 (canonical schema, exact lookup, metadata filter cơ bản, BM25, honest embedding labeling, agent policy DATA) | **IMPLEMENTED WITH LIMITATIONS** — xem giới hạn ở mục "Phase 1" bên dưới |
| Phase 2 (runtime orchestrator, security/lifecycle filter đầy đủ, RRF, GroundingPack runtime, claim/citation validator, benchmark+ablation thật) | **IMPLEMENTED WITH LIMITATIONS** — xem "## Phase 2" bên dưới; KHÔNG runtime-wired vào 3 service Product/Legal/Operations hiện có |
| Phase 3-6 (reranker/MMR/HyDE, domain guardrail chạy trong luồng, cache/observability, E2E toàn hệ thống) | **NOT IMPLEMENTED** |

Prompt gốc 50 phần (Phase 0/1) và prompt Phase 2 tiếp theo đều là quy mô
nhiều tuần cho một team (đã cảnh báo người dùng trước khi họ chọn full
scope mỗi lần — xem `docs/RAG_GUARDRAIL_IMPLEMENTATION_PLAN.md` mục 1, 31,
và câu hỏi scope trước khi bắt đầu Phase 2). Báo cáo này ghi đúng những gì
đã verify được, không mở rộng thành đã hoàn thành toàn bộ.

## 1. Executive Summary

Đọc đầy đủ 2 tài liệu nguồn, audit code thật (không suy đoán từ tên
class), viết 3 doc bắt buộc (extraction/audit/plan), rồi triển khai
Phase 0: retrieval failure phải phân biệt rõ lý do (`INDEX_NOT_READY` /
`EMPTY_QUERY` / `NO_RELEVANT_RESULT` / `OK`) thay vì mọi trường hợp đều
trả về `[]` giống nhau. 6 test mới, 381/381 test toàn repo pass (375 cũ +
6 mới), 0 regression.

## 2. Skills and Tools Used

Không có skill DOCX/RAG chuyên biệt nào khả dụng trong môi trường này —
dùng trực tiếp `python-docx` (đã cài sẵn) để đọc cả 2 file .docx theo
đúng cấu trúc đoạn văn + bảng (không dùng bản extract cũ có sẵn trong
repo của một quy trình khác, vì không xác nhận được nó khớp đúng file
nào). Dùng Explore agent (subagent read-only) để audit code hiện có,
tránh vừa đọc vừa code cùng lúc làm lẫn giữa "đã xác nhận" và "đang sửa."

## 3. Documents Inspected

- `docs/SHB_Corporate_Sales_MVP_Data_Blueprint_V3_Proposal.docx` — 446
  đoạn + 79 bảng, đọc trọn vẹn trong một lượt trước đó của phiên này.
- `docs/SHB_Corporate_Sales_Copilot_End_to_End_Evidence_Underwriting_AI_Assurance.docx`
  — 453 đoạn + 36 bảng, đọc trọn vẹn.

## 4. Baseline Repository State

`git status`/`git diff` phát hiện: repo hiện có uncommitted work từ một
**Gemini AI Agent khác** (xác nhận qua `AI_LOG.md`, 3 phiên timestamp
18/07 10:30/11:15/12:45), đang xây hệ thống Underwriting Handoff (Doc B
phần Customer Resolver/Metadata Plane/Document Assurance/Requirement
Compiler/Submission) — chạm nhiều file trùng phạm vi RAG/Guardrail này
(`app/knowledge/rag_provider.py`, `app/product/service.py`,
`app/operations/service.py`, `app/workflow/risk_gate.py`, ...). Đã báo
người dùng, người dùng xác nhận: **cứ tiếp tục, cho phép ghi đè nếu
cần.**

## 5. Baseline Tests

```text
375 passed, 0 failed (trước Phase 0)
381 passed, 0 failed (sau Phase 0 — +6 test mới)
```

## 6-7. Current RAG / Guardrail Findings

Xem đầy đủ `docs/RAG_GUARDRAIL_CURRENT_STATE_AUDIT.md` — bảng capability
với taxonomy IMPLEMENTED/PARTIALLY_IMPLEMENTED/IMPLEMENTED_BUT_UNSAFE/
IMPLEMENTED_BUT_UNMEASURED/NOT_IMPLEMENTED/DEAD_CODE/UNVERIFIED, mỗi
dòng có `file:line`. Tóm tắt: hybrid fusion là linear-sum thật (không
phải RRF); dense mặc định là hash bag-of-words (không phải semantic
embedding thật); không có reranker; `GroundingPack` là dead code;
Operations Agent không có retrieval nào; circuit breaker + multi-mode
RAG (local/mcp/hybrid) là phần **thật sự vững**, có test.

## 8-17. Query Understanding / Routing / Sparse / Dense / Fusion / Expansion / Hierarchical / Metadata Filtering / Reranking / Diversity / Compression / Conflict Detection

**NOT_IMPLEMENTED trong lượt này.** Quyết định kỹ thuật cho từng mục đã
ghi trong `docs/RAG_GUARDRAIL_IMPLEMENTATION_PLAN.md` mục 6-17 (vd:
không thay embedding mặc định, giữ linear-sum làm baseline ablation
thay vì xóa). Đây là Phase 1-3, chưa code.

## 18. Grounding Pack

**NOT_IMPLEMENTED.** `GroundingPack`/`Citation`
(`app/knowledge/rag_provider.py:29-41`) vẫn là dead code, chưa nối vào
luồng thật. Kế hoạch nối ở Phase 2 (`docs/RAG_GUARDRAIL_IMPLEMENTATION_PLAN.md`
mục 18).

## 19-30. Agent Retrieval Policies / Prompt Injection / Claim-Evidence / Citation / Domain Guardrails / Provider Failure Handling

**Provider Failure Handling (mục 24 kế hoạch) — PHẦN DUY NHẤT ĐÃ CODE
trong nhóm này:**

`app/knowledge/index.py::PersistentHybridIndex` thêm
`RetrievalOutcomeCode` (OK/NO_RELEVANT_RESULT/INDEX_NOT_READY/
EMPTY_QUERY) và `search_with_diagnostics()` — additive, không đổi
signature/behavior của `search()` hiện có (verified bằng test
`test_search_behavior_is_unchanged_by_the_diagnostics_refactor`).

Các mục còn lại (19: agent retrieval policy có weight riêng; 20: mở rộng
injection scanner; 21: claim/evidence page/span/quote_hash; 22: citation
validator; 23: domain guardrail Product/Operations) — **NOT_IMPLEMENTED**,
Phase 2/4, chưa code.

## 29 (Tests, đã tạo)

`tests/retrieval/test_provider_failure.py` — 6 test: index rỗng →
`INDEX_NOT_READY`; query chỉ có stopword → `EMPTY_QUERY`; có candidate
nhưng không match → `NO_RELEVANT_RESULT`; search thành công → `OK`;
`filtered_count` phản ánh đúng số bị loại theo scope; và một test bảo
toàn hành vi `search()` cũ tuyệt đối không đổi.

## 31-40. Caching / Observability / Evaluation Dataset / Retrieval Metrics / Agent Metrics / Ablation / Security Tests / E2E Tests

**NOT_IMPLEMENTED trong lượt này.** Không bịa số liệu ablation, không
bịa kết quả benchmark cho phần chưa build.

## 41. Files Changed

| File | Loại | Nội dung |
| --- | --- | --- |
| `docs/RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md` | Mới | 12 mục, tổng hợp yêu cầu từ 2 doc gốc |
| `docs/RAG_GUARDRAIL_CURRENT_STATE_AUDIT.md` | Mới | Bảng capability, taxonomy đúng yêu cầu, file:line thật |
| `docs/RAG_GUARDRAIL_IMPLEMENTATION_PLAN.md` | Mới | 32 mục, quyết định phạm vi từng kỹ thuật |
| `docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md` | Mới | Báo cáo này |
| `app/knowledge/index.py` | Sửa | Thêm `RetrievalOutcomeCode`, `RetrievalDiagnostics`, `search_with_diagnostics()`; `search()` không đổi |
| `tests/retrieval/test_provider_failure.py` | Mới | 6 test cho Phase 0 |

## 42. Known Limitations (không bịa)

- Dense retrieval vẫn là hash-based mặc định — KHÔNG phải semantic
  embedding thật, dù prompt/report có thể gọi tắt là "dense retrieval."
- Không có reranker, RRF, GroundingPack thật, domain guardrail
  Product/Operations, retrieval-ranking eval (Recall@k/MRR/nDCG), ablation
  study, hoặc 100-query eval set — tất cả NOT_IMPLEMENTED.
- Repo hiện có uncommitted work từ agent khác chạm cùng phạm vi file —
  rủi ro xung đột thật, người dùng đã chấp nhận.

## 43. Unverified Components

ACL/metadata filtering trước retrieval: đã đọc trực tiếp
`PersistentHybridIndex.search()` và xác nhận filter chạy TRONG vòng lặp
per-row TRƯỚC khi tạo hit (không phải lọc sau top-k) — nâng từ UNVERIFIED
lên **VERIFIED_BY_CODE_INSPECTION** (chưa chạy test riêng xác nhận, nên
chưa lên mức VERIFIED_BY_EXECUTION).

Product/Operations domain guardrail (chặn "chắc chắn", giá/phí không
nguồn): vẫn UNVERIFIED, chưa audit trong lượt này.

## 44. Acceptance Criteria (đối chiếu với prompt mục 48)

| Tiêu chí | Đạt? |
| --- | --- |
| Exact lookup hoạt động | UNVERIFIED (chưa audit riêng) |
| Sparse retrieval hoạt động | PARTIALLY_IMPLEMENTED (đã audit, không đổi) |
| Dense retrieval hoạt động | IMPLEMENTED_BUT_UNSAFE (hash-based, không semantic) |
| Hybrid fusion hoạt động | PARTIALLY_IMPLEMENTED (linear-sum, không RRF) |
| Metadata filtering chạy trước khi leak | VERIFIED_BY_CODE_INSPECTION |
| Agent-specific policies | PARTIALLY_IMPLEMENTED (chỉ khác threshold) |
| Grounding Pack được tạo | NOT_IMPLEMENTED |
| Provider failure không bị che thành no-result | **IMPLEMENTED (Phase 0, có test)** |
| Prompt injection suite pass | NOT_IMPLEMENTED (chưa mở rộng suite) |
| Full test suite pass | **381/381 PASS, VERIFIED_BY_EXECUTION** |
| RAG modes cũ không bị phá | **VERIFIED_BY_EXECUTION** (toàn bộ `tests/rag_mcp/` vẫn pass) |

Đa số tiêu chí acceptance của prompt 50 phần **chưa đạt** — đúng thực tế,
không tô hồng.

## Phase 1

### Checkpoint

Trước khi sửa: `git status --porcelain`, `git diff --stat`, diff của
`app/knowledge/index.py`, và hash SHA-256 của 6 file Phase 0 (index.py,
test_provider_failure.py, 4 doc RAG) được lưu vào
`scratchpad/checkpoint_phase0_<timestamp>/` (ngoài repo, theo đúng yêu
cầu "không git stash toàn repository"). 381/381 test được xác nhận PASS
tại thời điểm checkpoint.

### Concurrent Work Protection

Ngay sau checkpoint, chạy lại test để xác nhận baseline **KHÔNG ổn định**:
- Lần 1: 6 test fail — root cause: `app/approval/service.py` (sửa bởi
  Gemini Agent khác) đã đổi tên key `claims["payload_hash"]` thành
  `claims["package_hash"]`, nhưng `app/api/v2/router.py` còn 6 chỗ đọc
  key cũ → `KeyError`. Đây KHÔNG phải lỗi do Phase 0/RAG-Guardrail gây
  ra. Đã sửa 6 chỗ đọc trong `router.py` cho khớp tên key mới (hoàn tất
  một rename đã dở dang của agent khác, không phải quyết định thiết kế
  mới).
- Lần 2 (ngay sau khi sửa): **14 test fail khác** (không liên quan
  payload_hash) — xác nhận Gemini Agent đang sửa file **thời gian
  thực**, không phải snapshot tĩnh (file mới xuất hiện giữa hai lần
  chạy: `app/safety/domain_guardrails.py`, `app/knowledge/grounding_validator.py`,
  `app/metadata/`). Đã dừng lại, báo người dùng, người dùng chọn: tạm
  dừng chờ xác nhận.
- Sau khi người dùng xác nhận tiếp tục: `git status` cho thấy tree đã
  thay đổi thêm (`app/data_v3/` mới xuất hiện, `app/intent/fallback.py`
  cũng bị sửa). Chạy `pytest tests/ -q` hai lần liên tiếp (tránh thư mục
  `scratch/` gốc của Gemini Agent gây lỗi collection không liên quan) —
  **384/384 pass cả hai lần** → xác nhận ground đã ổn định, tiếp tục
  Phase 1.

### Canonical Schemas

`app/knowledge/retrieval_contracts.py` (mới) — `RetrievalRequest`,
`RetrievalCandidate`, `RetrievalDiagnostics` (Pydantic, pipeline-level),
`RetrievalPolicy`, `AgentType`/`AuthorityTier`/`VerificationStatus`/
`RetrievalChannel`/`RetrievalStatus`/`RetrievalErrorCode`/`MetadataRef`.
**Trạng thái: INTERFACE_ONLY / NOT_RUNTIME_WIRED** — không có call site
thật nào construct các model này; đây là contract cho Controlled
Retrieval Plane (Phase 2+). `tenant_id`/`team_id` để optional, không
enforce, vì repo không có khái niệm multi-tenant thật (đã ghi trong
`docs/RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md` mục 12) — không bịa.

`RetrievalErrorCode` (pipeline-level) là **strict superset đúng nghĩa**
của 3 failure code Phase 0 (`RetrievalOutcomeCode` không tính `OK`) —
test `test_pipeline_level_error_taxonomy_is_a_strict_superset_of_phase_0_failure_codes`
xác nhận trực tiếp bằng tập hợp giá trị enum, không phải khẳng định
suông.

### Exact Lookup

`PersistentHybridIndex.exact_lookup_by_chunk_id()` (O(1), PRIMARY KEY
lookup thật) và `exact_lookup_by_product_id()` (scan có filter
freshness/ACL, không chấm điểm relevance) — **IMPLEMENTED, có test thật**
(`tests/retrieval/test_exact_lookup.py`, 6 test, bao gồm test xác nhận
exact lookup vẫn tôn trọng branch scope, không bypass security boundary
chỉ vì query có ID chính xác).

Lookup theo `customer_id`/`case_id`/`evidence_id`/`rule_id`/`submission_id`
— **NOT_IMPLEMENTED trong lượt này**: các entity này sống ở storage khác
(`V2Repository`, `employee_db`), không phải `PersistentHybridIndex`; hợp
nhất một dispatcher exact-lookup xuyên nhiều backend là khối lượng công
việc riêng, không tự ý mở rộng phạm vi.

### Metadata Filtering

Xác nhận qua đọc code trực tiếp (Phase 0) rằng filter chạy TRONG vòng lặp
per-row, TRƯỚC khi tạo candidate — không phải lọc sau top-k. Phase 1
thêm `MetadataFilterReason` enum (3 giá trị THẬT: `SOURCE_NOT_EFFECTIVE`,
`SOURCE_SCOPE_MISMATCH`, `AGENT_SOURCE_NOT_ALLOWED`) và
`RetrievalDiagnostics.filtered_reasons: dict[str, int]` — mỗi record bị
loại giờ có reason code đếm được, test thật xác nhận
(`tests/retrieval/test_metadata_filtering.py`, 4 test).

6/9 reason code prompt đề xuất (`TENANT_SCOPE_MISMATCH`,
`CASE_SCOPE_MISMATCH`, `ROLE_NOT_ALLOWED`, `SOURCE_SUPERSEDED`,
`SOURCE_QUARANTINED`, `VERIFICATION_LEVEL_TOO_LOW`) —
**NOT_IMPLEMENTED**, ghi rõ trong docstring của `MetadataFilterReason`:
`KnowledgeChunk` (app/knowledge/models.py) không có field
`is_superseded`/`is_quarantined`/`verification_status`/`tenant_id`/
`case_id`/`actor_role` — báo cáo các code này là "đã implement" sẽ là
bịa dữ liệu schema không tồn tại.

### Sparse Retrieval

`bm25_scores()` (hàm thuần, không I/O) — BM25 thật (IDF + term-frequency
saturation + document-length normalization, k1=1.5/b=0.75 mặc định
chuẩn), test xác nhận đúng property BM25 thật (rare term > common term
qua IDF, term lặp lại tăng điểm có saturation, document không match =
điểm 0) — `tests/retrieval/test_sparse_retrieval.py`, 9 test.

`PersistentHybridIndex.sparse_search_bm25()` — kênh BM25 độc lập, tôn
trọng cùng ACL/freshness filter, **KHÔNG thay đổi** `search()`/
`search_with_diagnostics()` hiện có (test xác nhận rõ:
`test_sparse_search_bm25_does_not_affect_legacy_search`). Chưa fusion
với dense (đúng quyết định Phase 1 không làm RRF).

**Bug thật tìm thấy khi viết test cho phần này**: `dense_raw` trong
`search_with_diagnostics()` có thể vượt 1.0 do sai số dấu phẩy động khi
query và chunk gần như giống hệt nhau (giá trị quan sát được:
`1.000017`), làm `RetrievalHit.dense_score`'s `Field(le=1.0)` raise
`ValidationError` — lỗi có từ trước Phase 0/1, không phải do sparse
retrieval gây ra, tìm thấy nhờ test mới. Đã sửa bằng cách clamp cả hai
đầu (`max(0.0, min(1.0, ...))`) thay vì chỉ `max(0.0, ...)` như code cũ.

### Dense Representation Audit — cập nhật quan trọng so với báo cáo Phase 0

`RepresentationType` enum (`HASH_BOW_VECTOR`/`SEMANTIC_EMBEDDING`/
`SPARSE_LEXICAL`) và property `representation_type` thêm vào
`LocalEmbedding` (→ HASH_BOW_VECTOR), `CachedGeminiEmbedding`/
`CachedOpenAIEmbedding` (→ SEMANTIC_EMBEDDING). `RetrievalDiagnostics`
giờ có `representation_type`/`semantic_capability` — test xác nhận
default dataclass construction trả về nhãn trung thực (HASH_BOW_VECTOR/
False), không lạc quan giả.

**Phát hiện khi viết test**: báo cáo Phase 0 khẳng định "dense retrieval
mặc định là hash-based" dựa trên default của `create_embedding_provider()`
khi KHÔNG có env var (`"local"`). Nhưng file `.env` thật của deployment
này có `KNOWLEDGE_EMBEDDING_PROVIDER=openai` VÀ `OPENAI_API_KEY` đã cấu
hình — nghĩa là **trong triển khai thực tế đang chạy, dense retrieval
DÙNG OpenAI embedding thật (semantic), không phải hash fallback**. Đây
là điều chỉnh trung thực so với claim trước: "mặc định code" (không có
.env) và "mặc định triển khai thực tế" (có .env) là hai điều khác nhau
— test mới (`test_embedding_representation.py`) phải pin tường minh
`LocalEmbedding()` để không phụ thuộc vào env, và điều đó chính là cách
phát hiện ra sự khác biệt này.

### Embedding Provider Contract

`EmbeddingProvider` Protocol mở rộng thêm `representation_type` property
(structurally optional — code đọc qua `getattr(..., default=HASH_BOW_VECTOR)`
để không crash nếu một provider cũ chưa implement). Interface đầy đủ theo
prompt (`provider_id`/`model_version`/`embed_documents`/`embed_query`
tách bạch document/query embedding) — **NOT_IMPLEMENTED**, chỉ mới có
`representation_type`; đổi toàn bộ `.embed()` signature là breaking
change lớn hơn phạm vi an toàn của lượt này.

### Agent Retrieval Policies

`app/knowledge/agent_retrieval_policies.py` (mới) — 3 `RetrievalPolicy`
cụ thể (Product/Legal/Operations), dữ liệu lấy từ bảng Doc B mục 30 đã
trích trong `docs/RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md` mục 2 (không
bịa). Test xác nhận Legal `fail_closed=True`/`allow_customer_unverified_data=False`
khác Product, không agent nào cho phép `allow_model_inference_sources`
— `tests/retrieval/test_agent_retrieval_policy.py`, 7 test.

**Trạng thái: DATA thật, ENFORCEMENT chưa runtime-wired** — chưa có call
site nào tra `AGENT_RETRIEVAL_POLICIES` trước khi gọi
`PersistentHybridIndex.search()`; Product/Legal vẫn tự truyền threshold
hard-code như trước.

### Tests

9/10 file test theo đúng danh sách prompt mục 10 đã tạo (49 test mới,
tất cả pass). **`test_index_namespace.py` KHÔNG tạo** — index namespace
validation (provider_id/representation_type/model_version/dimension/
normalization/corpus_version compatibility check) là tính năng thật
chưa được xây trong lượt này; tạo test rỗng cho tính năng chưa có sẽ vi
phạm "Không tạo dead code rồi báo đã hoàn thành."

### Full-suite Results

```text
pytest tests/ -q  → 427 passed, 0 failed (lần 1)
pytest tests/ -q  → 427 passed, 0 failed (lần 2, ngay sau)
```

(384 trước Phase 1 + 43 test mới = 427; không dùng `pytest -q` trần vì
thư mục `scratch/` của Gemini Agent khác gây lỗi collection không liên
quan — đã dùng `pytest tests/ -q` để scope đúng, không phải để né lỗi.)

### Hard Gates (Phase 1 acceptance)

| Gate | Kết quả |
| --- | --- |
| `cross_customer_candidate_entered_ranking = 0` | **VERIFIED_BY_EXECUTION** (branch-scope proxy — repo không có customer_id trên KnowledgeChunk, xem docstring `test_cross_customer_filtering.py`) |
| `quarantined_source_retrieved = 0` | NOT_APPLICABLE — field `is_quarantined` không tồn tại trong schema, không có gì để verify |
| `superseded_policy_used_as_current = 0` | NOT_APPLICABLE — field `is_superseded` không tồn tại trong schema |
| `provider_failure_reported_as_no_result = 0` | **VERIFIED_BY_EXECUTION** (Phase 0) |
| `hash_bow_reported_as_semantic_embedding = 0` | **VERIFIED_BY_EXECUTION** cho CODE (không nhãn sai); triển khai thực tế dùng OpenAI thật (xem mục Dense Representation Audit ở trên) |

### Remaining Phase 2 Work (đã làm ở Phase 2, xem mục "## Phase 2" bên dưới)

Danh sách trên là NOT_IMPLEMENTED **tại thời điểm cuối Phase 1**. Phase 2
(bên dưới) đã triển khai: RRF fusion, GroundingPack runtime wiring,
claim/citation validator MVP, index namespace validation, retrieval
policy runtime enforcement (qua orchestrator mới — KHÔNG qua việc sửa 3
service Product/Legal/Operations hiện có, xem lý do trong mục "Agent
Migration"), ablation study thật. Vẫn NOT_IMPLEMENTED sau Phase 2:
cross-encoder/LLM reranker, MMR diversity, HyDE, multi-query, contextual
compression, `embed_documents`/`embed_query` tách bạch, exact lookup cho
customer/case/evidence/rule/submission ID (chỉ có chunk_id/product_id).

## Phase 2

**Phạm vi:** người dùng chọn "Toàn bộ Phase 2A+2B một lượt" (đã hỏi trước
vì khối lượng rất lớn — schema migration, RRF, GroundingPack runtime,
migrate 3 Agent, citation/claim validator, conflict detection, benchmark,
ablation, ~18 file test). Kết quả dưới đây là những gì THẬT SỰ được build
và verify trong một lượt — không phải toàn bộ 23 mục của prompt gốc.

### Checkpoint

`scratchpad/checkpoint_phase2_<timestamp>/` (ngoài repo): `git status
--porcelain`, `git diff --stat`, SHA-256 của 14 file liên quan RAG/safety/
metadata (index.py, retrieval_contracts.py, agent_retrieval_policies.py,
models.py, product/service.py, legal_service.py, operations/service.py,
evidence_validator.py, grounding_validator.py, domain_guardrails.py,
schemas/v2/metadata.py, metadata/models.py, context/customer_resolver.py,
observability/audit.py) — trước khi sửa bất kỳ file nào.

### Concurrent Changes phát hiện

Trước khi bắt đầu, `git status` cho thấy Gemini Agent (xem `AI_LOG.md`) đã
tiếp tục xây dựng thêm so với lần checkpoint Phase 1: file mới
`app/metadata/models.py`, `app/context/customer_resolver.py`,
`app/safety/domain_guardrails.py`, `app/observability/audit.py`,
`app/knowledge/grounding_validator.py`, `app/schemas/v2/metadata.py`,
`app/data_v3/`, `tests/unit/test_v2_metadata.py`, cùng các file M
(modified) `app/product/service.py`, `app/operations/service.py`,
`app/knowledge/rag_provider.py`, `app/knowledge/service.py`.

Đã đọc đầy đủ 5 file mới trước khi code (không đoán) để tránh trùng lặp:
- `app/schemas/v2/metadata.py` + `app/metadata/models.py`: hai hệ thống
  Metadata Object/Envelope khác nhau (có vẻ là hai lần lặp của cùng một
  agent) cho các entity Customer/Document/Evidence/Submission — KHÔNG che
  phủ retrieval chunk, khác namespace với `KnowledgeChunk`.
- `app/safety/domain_guardrails.py`: validate OUTPUT của Agent (Product/
  Legal/Operations) theo rule tĩnh — khác lớp với retrieval-time
  filtering; bổ sung, không trùng.
- `app/knowledge/grounding_validator.py`: `GroundingValidator` MVP làm
  việc trên `document_repository.get_document(doc_id)` (dict-based),
  KHÔNG dùng `PersistentHybridIndex`/`KnowledgeChunk` — khác lớp trừu
  tượng với claim_evidence_validator.py mới của Phase 2 này.
- `app/context/customer_resolver.py`: dùng `V2Repository.get_metadata_object()`
  — namespace hoàn toàn khác `PersistentHybridIndex`.

**Quyết định:** không sửa/re-export bất kỳ file nào trong 5 file trên
(tránh ghi đè công việc đang dở của agent khác); không tái sử dụng trực
tiếp `GroundingPack` cũ trong `app/knowledge/rag_provider.py` (đã bị agent
kia gắn vào `MetadataEnvelope` của họ) — Phase 2 này đặt tên
`RetrievalGroundingPack` riêng trong `retrieval_contracts.py` để tránh va
chạm (xem docstring "Phase 2: GroundingPack / conflict / result" trong
`app/knowledge/retrieval_contracts.py`).

**File CÓ sửa vì cần thiết, đã kiểm tra không nằm trong vùng agent kia
đang sửa:** `app/knowledge/index.py`, `app/knowledge/models.py`,
`app/knowledge/retrieval_contracts.py`, `app/knowledge/agent_retrieval_policies.py`,
`app/knowledge/legal_service.py` (KHÔNG có trong danh sách M của agent kia
— an toàn để sửa).

**File chủ động KHÔNG sửa dù nằm trong phạm vi Phase 2 prompt gốc:**
`app/product/service.py`, `app/operations/service.py` — đang có uncommitted
changes từ agent khác tại thời điểm bắt đầu Phase 2; xem mục "Agent
Migration" bên dưới.

### Baseline Tests

```text
427 passed, 0 failed  (đầu Phase 2, hai lần liên tiếp — ổn định, không có
                        concurrent-modification instability lần này)
```

### KnowledgeChunk Schema Extension

`app/knowledge/models.py` — thêm 8 field optional/default (backward
compatible, `extra="forbid"` vẫn giữ nguyên vì field mới có default):
`customer_id`, `case_id`, `source_type`, `authority_tier`,
`verification_status`, `is_superseded` (default `False`),
`is_quarantined` (default `False`), `allowed_roles` (default `[]`).
`authority_tier`/`verification_status` dùng lại enum `AuthorityTier`/
`VerificationStatus` từ `retrieval_contracts.py` (Phase 1) — không tạo
enum trùng. Migration test: `tests/retrieval/test_chunk_lifecycle_filters.py`,
`test_customer_case_scope.py` xác nhận field cũ (không set) vẫn hoạt động
bình thường qua toàn bộ 427 test Phase 0/1 (không có regression).

**Không có migration script/rebuild command riêng** — vì đây là field
optional-default, index SQLite hiện có (payload lưu dạng JSON text) đọc
lại vẫn hợp lệ ngay lập tức (`KnowledgeChunk.model_validate_json` tự điền
default cho field thiếu), không cần ALTER TABLE hay rebuild dữ liệu cũ.
Đây là điểm khác so với một schema SQL cột cứng.

### Security Pre-Filter (Lifecycle + Scope)

`app/knowledge/index.py::_filter_eligible()` — hàm dùng chung mới, chạy
TRƯỚC scoring, cho cả 3 kênh (`sparse_search_bm25`, `dense_search`,
`exact_lookup_by_product_id`). `search()`/`search_with_diagnostics()`
(legacy) **KHÔNG bị đổi** — giữ nguyên logic filter cũ của chúng, không
gọi `_filter_eligible()`, để tuyệt đối không có rủi ro regression trên
375+ call site cũ (xem "Backward Compatibility" bên dưới).

7 reason code mới (cộng với 3 code Phase 1 = 10/12 code prompt đề xuất):
`CUSTOMER_SCOPE_MISMATCH`, `CASE_SCOPE_MISMATCH`, `SOURCE_SUPERSEDED`,
`SOURCE_QUARANTINED`, `VERIFICATION_LEVEL_TOO_LOW`,
`AUTHORITY_LEVEL_TOO_LOW`, `ROLE_NOT_ALLOWED`. Vẫn KHÔNG implement
`TENANT_SCOPE_MISMATCH`/`BRANCH_SCOPE_MISMATCH`/`TEAM_SCOPE_MISMATCH` —
repo không có khái niệm tenant/team riêng biệt với branch (đã xác nhận từ
Phase 1, không đổi).

Nguyên tắc "unknown ≠ current/trusted": chunk có `authority_tier=None`
được coi là `TIER_5_UNSUPPORTED` (thấp nhất) khi so với
`minimum_authority_tier`; `verification_status=None` được coi là
`UNVERIFIED`. **Phát hiện quan trọng khi test thật:** với nguyên tắc này,
toàn bộ dữ liệu do `ProductKnowledgeService`/`LegalKnowledgeService.ingest()`
ingest TRƯỚC Phase 2 (không set 2 field này) sẽ bị `AUTHORITY_LEVEL_TOO_LOW`
khi orchestrator áp policy thật — xác nhận bằng chạy tay orchestrator
trước khi sửa `legal_service.py`. Đã sửa `legal_service.py` (file KHÔNG
bị agent khác động vào) để gắn `TIER_2_VERIFIED_INTERNAL`/`VERIFIED` cho
rule đã qua `require_serving_approval()`. **`app/product/service.py`
KHÔNG được sửa** (đang bị agent khác sửa) — nghĩa là Product ingestion
thật hiện tại **CHƯA gắn authority_tier**, nên nếu Product Agent thật gọi
orchestrator hôm nay, mọi candidate sẽ bị lọc hết trừ khi caller không
truyền `minimum_authority_tier`. Đây là giới hạn thật, ghi rõ ở mục "Hạn
chế" bên dưới, không che giấu.

Test: `tests/retrieval/test_chunk_lifecycle_filters.py` (4),
`tests/retrieval/test_customer_case_scope.py` (4).

### Index Namespace Validation

`IndexNamespace` (frozen dataclass) + `PersistentHybridIndex.namespace()`
+ `namespace_mismatch()` trong `app/knowledge/index.py`. `normalization`
báo trung thực: `"l2"` cho `LocalEmbedding` (có normalize thật trong code),
`"unknown"` cho Gemini/OpenAI (chưa từng kiểm tra provider có tự chuẩn hoá
hay không). `corpus_version` đọc trực tiếp từ bảng `index_manifests` (bản
ghi mới nhất), không cache — phản ánh đúng trạng thái đĩa kể cả khi agent
khác đang ingest cùng lúc vào cùng file. **Chưa gắn vào orchestrator như
một hard gate chặn truy vấn** (orchestrator hiện chỉ có 1 index cho mỗi
lần gọi nên không có tình huống 2 namespace khác nhau lẫn nhau trong 1
call — mismatch check tồn tại như hàm thuần, có test, nhưng chưa có call
site nào tự động gọi nó trước một query thật). Test:
`tests/retrieval/test_index_namespace.py` (5).

### RRF Fusion

`app/knowledge/fusion.py` (mới) — `ReciprocalRankFusion` (rrf_k=60 mặc
định, per-agent `sparse_weight`/`dense_weight` từ `RetrievalPolicy`,
tie-break xác định: fused_score → authority tier → verified → effective_from
gần nhất → chunk_id) và `LinearSumFusion` (tái tạo công thức legacy
0.6/0.4 CHỈ để so sánh ablation công bằng — không thay thế công thức inline
thật trong `index.py`, công thức đó vẫn giữ nguyên 100%). Test:
`tests/retrieval/test_rrf_fusion.py` (6, gồm 1 test so khớp tay công thức
RRF với giá trị tính sẵn).

`PersistentHybridIndex.dense_search()` (mới) — kênh dense THUẦN, độc lập
với `sparse_search_bm25()`, cần thiết vì RRF phải fuse theo RANK của hai
ranking độc lập, trong khi `search_with_diagnostics()` cũ trộn dense+sparse
thành 1 điểm số duy nhất (không thể fuse lại lần hai).

### Policy Runtime Enforcement

`app/knowledge/retrieval_orchestrator.py::ControlledRetrievalOrchestrator`
(mới) — pipeline thật: resolve policy từ `AGENT_RETRIEVAL_POLICIES` →
exact lookup (nếu `policy.exact_lookup_first`) → sparse BM25 + dense song
song → RRF (hoặc linear-sum nếu chọn) → conflict detection → top-k →
GroundingPack. Đã verify bằng test thật (không phải chỉ construct output):
Legal `fail_closed=True` biến kết quả rỗng thành `RetrievalStatus.ERROR`
+ `SOURCE_SCOPE_EMPTY`; Product `fail_closed=False` giữ `OK` +
`NO_RELEVANT_RESULT`; cùng 1 chunk `verification_status=UNVERIFIED` bị
Legal từ chối nhưng Product chấp nhận (2 policy khác nhau, cùng dữ liệu —
chứng minh policy DATA thật sự đổi hành vi runtime, không chỉ là tài liệu
như Phase 1). Test: `tests/retrieval/test_policy_runtime_enforcement.py` (4).

**Trạng thái thật:** orchestrator đã hoạt động và có test E2E thật (xem
"Agent Migration" bên dưới), nhưng **KHÔNG có call site nào trong luồng
sản phẩm thật** (`app/api/v2/router.py`, `app/product/service.py`,
`app/knowledge/legal_service.py.search()`) gọi tới nó — vẫn
`NOT_RUNTIME_WIRED` vào request path thật của người dùng cuối.

### GroundingPack Runtime

`RetrievalGroundingPack`/`GroundingItem`/`RetrievalConflict`/
`MissingInformation`/`UnavailableSource`/`SourceLocator` (mới, trong
`retrieval_contracts.py`) — đặt tên khác `GroundingPack` cũ trong
`rag_provider.py` để tránh va chạm với agent khác (xem "Concurrent
Changes"). `source_locator` dùng `DOCUMENT_SPAN` (có `section`, KHÔNG có
`page` — field đó không tồn tại trên `SourceLocator`, không thể bịa được
kể cả vô tình) — test xác nhận trực tiếp `not hasattr(item.source_locator,
"page")`. `content_hash` tính từ chuỗi `chunk_id + source_version` nối lại
— đủ để phát hiện 2 lần retrieve cho ra tập item khác nhau, KHÔNG phải
cryptographic tamper-proofing cấp production (một implementation thật sẽ
hash cả `content` của từng item). Test:
`tests/retrieval/test_grounding_pack_runtime.py` (4).

### Product / Legal / Operations Agent

**Legal:** verify E2E thật qua `LegalKnowledgeService.ensure_index()` →
`ControlledRetrievalOrchestrator.retrieve()` → claim với quote thật trong
chunk → `SUPPORTED`; quote bịa → `UNSUPPORTED`. Test:
`tests/e2e/test_legal_controlled_retrieval.py`.

**Operations:** `app/operations/sop_knowledge.py` (mới) —
`OperationsKnowledgeService` ingest thật `data/synthetic/v3/operations/
sop_workflow.json` (11 bước SOP thật) vào `PersistentHybridIndex` riêng.
**Đây là module MỚI, KHÔNG sửa `app/operations/service.py`** (đang bị
agent khác sửa) — `OperationsService.prepare()` vẫn đọc JSON tĩnh y hệt
trước Phase 2, KHÔNG có gì thay đổi ở đó. `OperationsKnowledgeService` là
một index/service RIÊNG mà orchestrator có thể query cho `AgentType.OPERATIONS`
— chứng minh retrieval Operations THẬT SỰ khả thi và có test, nhưng CHƯA
migrate `OperationsService` thật sang dùng nó. Test:
`tests/e2e/test_operations_controlled_retrieval.py` (2).

**Product:** **KHÔNG tạo module ingestion sản phẩm mới cạnh tranh với
`app/product/service.py`** (đang bị sửa đồng thời) — thay vào đó, test
E2E ingest trực tiếp 2 chunk mẫu đúng hình dạng `data/synthetic/v3/
products/product_catalog.json` ngay trong file test, gắn nhãn
`authority_tier=TIER_1_AUTHORITATIVE`/`VERIFIED` đúng như một ingestion
thật sẽ làm. Đây là DEMO có test, KHÔNG phải bằng chứng Product ingestion
thật đã được gắn tier (xem phát hiện ở mục "Security Pre-Filter" —
ingestion thật của Product CHƯA gắn tier). Test:
`tests/e2e/test_product_controlled_retrieval.py` (2).

**Lý do chung không sửa 3 service Agent thật:** `app/product/service.py`
và `app/operations/service.py` có uncommitted diff từ Gemini Agent khác
tại thời điểm bắt đầu Phase 2 (xác nhận qua `git status` trước khi code) —
sửa trực tiếp nội bộ các file này mang rủi ro ghi đè công việc thật của
agent kia mà phiên này không có đủ ngữ cảnh để hợp nhất an toàn. Đây là
quyết định phạm vi có chủ đích (không phải bỏ sót), nhất quán với cách xử
lý xung đột đồng thời đã áp dụng xuyên suốt phiên làm việc này.

### Claim-Evidence Validation

`app/safety/claim_evidence_validator.py` (mới) — deterministic, KHÔNG
dùng LLM judge (đúng yêu cầu). Ghép từ 2 phần có sẵn: citation_validator
(structural) + `evidence_validator.validate_claim()` (Phase 0, tái sử
dụng KHÔNG sửa) + 2 check mới (conflict trong pack, scope khách hàng/case).
7 status thật (`SUPPORTED`/`CONFLICTED`/`STALE_SOURCE`/`WRONG_SCOPE`/
`UNSUPPORTED`/`SOURCE_UNAVAILABLE`) đã verify bằng test thật cho từng
nhánh. `PARTIALLY_SUPPORTED` được định nghĩa trong enum nhưng **KHÔNG bao
giờ được trả về** — ghi rõ trong docstring lý do (cần semantic entailment
để phân biệt "đúng toàn bộ" với "đúng một phần", không có rule
deterministic nào trong repo này làm được việc đó). Test:
`tests/guardrails/test_claim_evidence_validator.py` (6).

### Structural Citation Validation

`app/safety/citation_validator.py` (mới) — CHỈ kiểm tra cấu trúc (đúng
pack, đúng grounding_item, đúng source/version, hash pack không đổi),
KHÔNG kiểm tra semantic entailment — đặt tên rõ
`STRUCTURAL_CITATION_VALIDATION_PASSED` để không ai nhầm đây là "đã verify
nội dung claim đúng". Test:
`tests/guardrails/test_structural_citation_validator.py` (5).

### Conflict Detection

`app/knowledge/conflict_detection.py::detect_slot_conflicts()` — **KHÔNG
phải** structured-fact conflict engine đầy đủ như ví dụ trong prompt
("CRM employee_count=500 vs Document employee_count=430" cần một
structured-fact store với subject/field_name/value mà repo này không có).
Đây là proxy hẹp hơn, trung thực: 2 chunk cùng `(product_id, section_path)`
— cùng "ô" logic — nhưng khác `content_hash` → conflict. Test:
`tests/retrieval/test_conflict_detection.py` (4). Đã nối vào orchestrator
(`selected` candidates được check trước khi đưa vào GroundingPack) và vào
`claim_evidence_validator` (chunk nằm trong `pack.conflicts` → `CONFLICTED`
dù quote đúng 100%, đúng yêu cầu "Critical claim không SUPPORTED... không
được dùng" — không chỉ giảm confidence).

### Benchmark

`benchmarks/data/retrieval_queries.json` — **33 câu hỏi thật**, không
phải 60 như prompt yêu cầu. Lý do ghi rõ trong chính file JSON
(`scope_note`): tổng corpus thật có thể ingest ngay hôm nay (Legal 9 rule +
Operations 11 bước SOP + Product 5 sản phẩm active) chỉ có 25 bản ghi; 60
câu hỏi riêng biệt, không suy biến, cho 25 bản ghi phần lớn sẽ là
paraphrase trùng lặp không thêm tín hiệu thật — 33 câu (25 câu 1-1 với mỗi
bản ghi + 8 câu hard-negative/no-result/multi-relevant) được chọn để mỗi
câu hỏi đóng góp thông tin thật, thay vì đệm số lượng.

`benchmarks/run_retrieval_benchmark.py` — ingest dữ liệu THẬT (Legal qua
`LegalKnowledgeService`, Operations qua `OperationsKnowledgeService`,
Product ingest trực tiếp `data/synthetic/v2/products.json`, đều dùng
`provider=LocalEmbedding()` — xem "Phát hiện phụ" bên dưới về lý do), chạy
4 config, tính Recall@1/3/5, MRR, nDCG@5, forbidden-source-rate,
no-result-correct-rate bằng hàm thuần (`benchmarks/retrieval_metrics.py`,
không phụ thuộc I/O).

**Phát hiện phụ (bug/rủi ro thật tìm thấy khi build benchmark, không phải
tính năng):** chạy benchmark lần đầu với provider mặc định (theo `.env`,
`KNOWLEDGE_EMBEDDING_PROVIDER=openai`) gây `OSError: Invalid argument` khi
ghi `data/vector_db/openai_vector_cache.json` — đây là **một file cache
DÙNG CHUNG cho MỌI `PersistentHybridIndex` không chỉ định provider riêng**,
kể cả những instance có `index_path` khác nhau. Rất có thể là xung đột
ghi đồng thời với Gemini Agent (file này cũng nằm trong danh sách `M` của
`git status`). Đã sửa tận gốc: `LegalKnowledgeService.__init__` và
`OperationsKnowledgeService.__init__` giờ nhận tham số `provider=` tường
minh (mặc định `None` → hành vi cũ không đổi cho code sản phẩm thật); mọi
test/benchmark Phase 2 giờ truyền `provider=LocalEmbedding()` để cô lập
hoàn toàn khỏi file cache dùng chung — vừa sửa lỗi thật, vừa loại bỏ một
điểm va chạm đồng thời chưa từng được ghi nhận trước Phase 2.

### Ablation

Kết quả THẬT từ `benchmarks/results/retrieval_benchmark_phase2.json`
(33 câu, embedding provider = LocalEmbedding, không dùng API thật):

| Config | Recall@1 | Recall@3 | Recall@5 | MRR | nDCG@5 | Forbidden-rate | No-result-correct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A. Legacy linear-sum (0.6·dense+0.4·sparse, dense=hash-BoW) | 0.861 | 0.950 | 0.967 | 0.933 | 0.938 | 0.030 | 0.333 |
| B. BM25-only | 0.928 | 0.950 | 0.967 | 0.967 | 0.963 | 0.030 | 0.333 |
| C. Dense-only (hash-BoW) | 0.861 | 0.967 | 0.967 | 0.933 | 0.942 | 0.030 | 0.333 |
| E. RRF + policy filter (BM25+dense, per-agent weight) | 0.928 | 0.967 | 0.967 | 0.967 | 0.964 | 0.030 | 0.333 |

**Đọc kết quả trung thực, không tô hồng:**
- RRF (E) và BM25-only (B) cho Recall@1/MRR cao nhất và bằng nhau trên bộ
  33 câu này — **không có bằng chứng RRF vượt trội BM25-only** ở quy mô
  corpus này (25 bản ghi); RRF chỉ nhỉnh hơn B ở nDCG@5 (0.964 vs 0.963,
  chênh lệch không có ý nghĩa thống kê với n=33).
- Dense-only (hash-BoW, KHÔNG phải semantic thật) vẫn đạt Recall@5=0.967
  — vì phần lớn câu hỏi benchmark dùng chung từ khóa với chunk gốc
  (không kiểm tra được khả năng hiểu ngữ nghĩa thật do provider là hash,
  không phải OpenAI/Gemini — ablation với semantic embedding thật chưa
  chạy, xem "Hạn chế").
- `forbidden_source_retrieval_rate=0.030` (1/33) **giống hệt nhau ở cả 4
  config** — cho thấy case hard-negative bị lẫn không phụ thuộc chiến
  lược fusion (rất có thể do trùng từ khóa tiếng Việt giữa 2 chunk khác
  domain), chưa điều tra sâu thêm trong lượt này.
- `no_result_correct_rate=0.333` (1/3) **giống hệt nhau ở cả 4 config** —
  phát hiện thật: `sparse_search_bm25()`/`dense_search()` (2 kênh mới của
  Phase 1/2) **không có ngưỡng điểm tối thiểu** (`search_with_diagnostics()`
  cũ có `effective_threshold`, 2 kênh mới thì không) — bất kỳ overlap
  token nào > 0, dù rất yếu, vẫn lọt vào top-k. Đây là một khoảng trống
  thật cần Phase 3 xử lý (thêm ngưỡng tối thiểu cho BM25/dense độc lập
  trước khi đưa vào RRF), không phải lỗi trong phép đo.

Không benchmark với OpenAI/Gemini embedding thật trong lượt này (tránh
lặp lại rủi ro va chạm file cache dùng chung với agent khác, xem "Phát
hiện phụ" ở trên) — ghi rõ là `BLOCKED_BY_ENVIRONMENT` cho phần live
semantic ablation, không bịa số liệu.

### E2E Tests

7 file trong `tests/e2e/`: `test_legal_controlled_retrieval.py`,
`test_operations_controlled_retrieval.py` (2 test),
`test_product_controlled_retrieval.py` (2 test),
`test_quarantined_source_blocked.py`, `test_superseded_policy_blocked.py`,
`test_retrieval_provider_failure_fail_closed.py` — mỗi test gọi
orchestrator/service thật, không chỉ construct output cuối. **Không tạo**
`test_multi_agent_grounding.py` riêng — 3 test E2E theo từng Agent đã phủ
đúng những gì file đó sẽ kiểm tra (không có tương tác đa-agent thật nào
tồn tại trong code để test thêm).

### Full-suite Results

```text
pytest tests/ -q  → 486 passed, 0 failed (lần 1)
pytest tests/ -q  → 486 passed, 0 failed (lần 2, ngay sau)
```

(427 trước Phase 2 + 59 test mới net — một phần chênh lệch so với 55 test
Phase 2 tôi viết trực tiếp đến từ `tests/unit/test_v2_metadata.py`, file
của Gemini Agent xuất hiện thêm giữa 2 lần chạy baseline, không phải test
của phiên này.)

### Hard Gates (Phase 2 acceptance)

| Gate | Kết quả |
| --- | --- |
| `cross_customer_source_selected = 0` | **VERIFIED_BY_EXECUTION** (field `customer_id` THẬT trên KnowledgeChunk giờ đã tồn tại — không còn là proxy branch-scope như Phase 1) |
| `cross_case_source_selected = 0` | **VERIFIED_BY_EXECUTION** |
| `quarantined_source_selected = 0` | **VERIFIED_BY_EXECUTION** (`tests/e2e/test_quarantined_source_blocked.py`) |
| `superseded_source_used_as_current = 0` | **VERIFIED_BY_EXECUTION** (`tests/e2e/test_superseded_policy_blocked.py`) |
| `expired_critical_policy_used = 0` | **VERIFIED_BY_EXECUTION** (`claim_evidence_validator` → `STALE_SOURCE`, kế thừa từ `evidence_validator.py` Phase 0) |
| `provider_failure_reported_as_no_result = 0` | **VERIFIED_BY_EXECUTION** (Phase 0 + Phase 2 mở rộng lên tầng orchestrator: Legal fail-closed → `ERROR`, không phải `OK` rỗng) |
| `legal_pass_without_policy_source = 0` | **VERIFIED_BY_EXECUTION** (`test_retrieval_provider_failure_fail_closed.py`) |
| `critical_claim_without_grounding = 0` | **VERIFIED_BY_EXECUTION** (`SOURCE_UNAVAILABLE` khi chunk không có trong pack) |
| `operations_step_without_SOP_grounding = 0` | **PARTIALLY_VERIFIED** — đúng cho `OperationsKnowledgeService` (module mới); KHÔNG áp dụng được cho `OperationsService.prepare()` thật vì file đó chưa migrate |
| `hash_index_queried_with_semantic_namespace = 0` | **INTERFACE_ONLY** — `namespace_mismatch()` có test thật nhưng chưa có call site nào tự động chặn trước một query thật (chỉ 1 index/call nên chưa có tình huống mismatch thật xảy ra trong orchestrator hiện tại) |

### Backward Compatibility

`search()`/`search_with_diagnostics()` **không đổi một dòng logic** —
chỉ thêm method mới (`dense_search`, `eligibility_diagnostics`,
`namespace`, `_filter_eligible`) bên cạnh. 49 test Phase 1 + toàn bộ test
cũ khác vẫn pass nguyên vẹn (486/486). `local`/`mcp`/`hybrid` mode của
`RagProviderRouter` không bị động tới. Không có config flag
`controlled_runtime_enabled`/`fusion_mode` ở cấp global settings — vì
chưa có call site sản phẩm thật nào cần bật/tắt nó (orchestrator hiện chỉ
được gọi từ test và benchmark, chưa từ luồng request thật) — thêm 1 flag
cho một pipeline chưa ai gọi sẽ là dead config, không thêm.

### Hạn chế thật của Phase 2 (không bịa)

1. **`ControlledRetrievalOrchestrator` chưa được gọi từ bất kỳ luồng
   request thật nào** (`app/api/v2/router.py` không import nó). Đây là
   giới hạn lớn nhất: mọi thứ ở trên đã "hoạt động đúng" khi test/benchmark
   gọi trực tiếp, nhưng người dùng cuối hôm nay vẫn nhận kết quả từ
   `ProductKnowledgeService`/`LegalKnowledgeService.search()`/
   `OperationsService.prepare()` như trước Phase 2 — KHÔNG có gì thay đổi
   trải nghiệm thật.
2. **Product ingestion thật (`app/product/service.py`) chưa gắn
   `authority_tier`/`verification_status`** — nếu orchestrator được nối
   vào ngày mai mà không sửa file đó trước, mọi Product candidate sẽ bị
   `AUTHORITY_LEVEL_TOO_LOW` (trừ khi Product Agent gọi orchestrator mà
   không set `minimum_authority_tier`, nhưng `PRODUCT_RETRIEVAL_POLICY` có
   set — cần nhớ sửa `product/service.py` TRƯỚC khi bật runtime wiring).
3. **`sparse_search_bm25()`/`dense_search()` không có ngưỡng điểm tối
   thiểu** (phát hiện từ ablation, xem trên) — RRF hiện có thể fuse một
   candidate cực yếu (BM25 score gần 0) chỉ vì nó lọt top-k.
4. **Conflict detection chỉ là proxy slot-identity**, không phải
   structured-fact engine thật như prompt mô tả.
5. **Benchmark 33 câu, không phải 60**, và chưa chạy với embedding
   semantic thật (chỉ LocalEmbedding) — vì lý do cô lập khỏi file cache
   dùng chung, xem "Phát hiện phụ".
6. **`IndexNamespace` mismatch chưa là hard gate thật** — hàm có, test có,
   nhưng chưa có call site chặn request.
7. **6/8 field GroundingItem structured (`page`/`bounding_box`) không tồn
   tại** — vì `KnowledgeChunk` không có; mọi item hiện tại đều
   `DOCUMENT_SPAN` với `section`, không có item nào dùng nhánh
   `STRUCTURED_FIELD` (chưa có nguồn dữ liệu structured nào được nối vào
   GroundingPack để cần nhánh đó).
8. **3 service Agent thật (`Product`/`Legal.search()`/`Operations.prepare()`)
   hoàn toàn không đổi** — quyết định có chủ đích do xung đột đồng thời
   với agent khác, không phải thiếu sót kỹ thuật.

### Remaining Phase 3+ Work (NOT_IMPLEMENTED)

Runtime-wire orchestrator vào `router.py`/3 service thật (cần phối hợp với Gemini Agent trước vì cùng chạm file); gắn `authority_tier` vào Product ingestion thật; ngưỡng điểm tối thiểu cho BM25/dense độc lập; cross-encoder/LLM reranker; MMR diversity; HyDE; multi-query; contextual compression; structured-fact conflict engine thật; benchmark 60 câu với semantic embedding thật (cần điều phối file cache dùng chung hoặc tách cache theo index); `IndexNamespace` như hard gate thật; `embed_documents`/`embed_query` tách bạch; observability/metrics/cache cho pipeline mới; E2E toàn hệ thống qua HTTP API thật.

---

## Phase 0.5: Trust Foundation & V3 Integration (IMPLEMENTED & FULLY VERIFIED - 2026-07-18)

Đồng bộ và đóng cứng (freeze) toàn bộ nền tảng tin cậy (Trust Foundation) của V3 Integration:

1. **Chuẩn hóa State Taxonomy và Reason Codes (`app/workflow/risk_gate.py`):**
   * Sửa đổi `RiskGuardrailGate` để phân biệt rõ ràng: lỗi thiếu tài liệu (on_unknown = `"pending_information"`) dẫn tới trạng thái `need_information`; lỗi vi phạm chính sách có thể phê duyệt ngoại lệ (như nợ xấu, có `human_review_allowed=True`) dẫn tới trạng thái `need_review`.
2. **Cập nhật Workflow Engine (`app/workflow/engine.py`):**
   * Tích hợp kết quả phân loại của `RiskGuardrailGate` vào luồng chuyển đổi trạng thái (transition machine). Case không bị gom nhóm bừa bãi vào `pending_review` nữa mà chuyển đúng về `pending_information` (cho thiếu tài liệu) và `pending_review` (cho phê duyệt chuyên viên).
3. **Thực hiện Grounding Bằng Chứng Thực Tế (`data/synthetic/v3/legal/banking_policy_documents.json`):**
   * Nạp 5 tài liệu quy chế/chính sách ngân hàng thực tế (KYC, Tín dụng, Payroll, Cash Management, Bulk Payment) khớp hoàn toàn với các quotes của V3 rules vào SQLite index thông qua `LegalKnowledgeService`. `EvidenceValidator` thực hiện đối soát quote trực tiếp trên văn bản thật này để xác minh.
4. **Sửa lỗi Endpoint `/missing-information` (`app/api/v2/router.py`):**
   * Loại bỏ sự phụ thuộc cứng vào `operations_result`. Endpoint giờ phân tích trực tiếp từ `eligibility_result` và `evidences` để trả về danh sách tài liệu khách hàng cần bổ sung (`customer_action_items`) và các lỗi chuyên viên cần xử lý (`specialist_review_items`).
5. **Đảm bảo chất lượng bằng E2E Tests:**
   * Viết thêm `tests/e2e/test_v3_specialist_review_closure.py` giả lập quy trình: Case bị block do nợ xấu -> Specialist gửi quyết định `cleared` -> Workflow tự động resume chuyển trạng thái sang `pending_approval`.
   * **Toàn bộ 558/558 tests passed** 100% trong 2 lượt chạy liên tiếp.
