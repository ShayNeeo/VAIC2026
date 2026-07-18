# Phase 2–6 Final Implementation Report

**Trạng thái thật, tóm tắt trước khi đọc chi tiết:**

| Phase | Trạng thái |
| --- | --- |
| Phase 2 (Controlled Hybrid Retrieval runtime) | IMPLEMENTED WITH LIMITATIONS — chi tiết đầy đủ ở `docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md` mục "## Phase 2" |
| Phase 3 (Advanced Retrieval Quality) | IMPLEMENTED WITH LIMITATIONS — reranker/MMR mặc định TẮT vì ablation thật cho thấy chúng KHÔNG cải thiện chất lượng trên corpus này |
| Phase 4 (Full AI Guardrail) | PARTIALLY_IMPLEMENTED — deterministic injection scanner, output-language guardrail, abstention engine đều thật; semantic claim validation, Schema Guardrail retry-loop, Risk/Action Guardrail integration đầy đủ là NOT_IMPLEMENTED |
| Phase 5 (Evaluation/Observability/Resilience/Performance) | PARTIALLY_IMPLEMENTED — benchmark/ablation/observability/resilience/performance đều có số liệu thật (scope nhỏ hơn yêu cầu, ghi rõ vì sao); drift monitoring và load test đa luồng là NOT_IMPLEMENTED |
| Phase 6 (Business Integration & Release) | **STOPPED theo đúng điều kiện dừng #2 của prompt gốc** — xem mục 14 |

Đây là một continuous-build session theo đúng yêu cầu "không dừng hỏi sau mỗi phase", nhưng KHÔNG có nghĩa mọi mục trong prompt 71 mục đều được xây — nhiều mục con trong Phase 4/5 và toàn bộ Phase 6 KHÔNG được xây, ghi rõ trong mục tương ứng, không bịa "COMPLETED".

## 1. Executive Summary

Tiếp tục trực tiếp từ Phase 1 (đã hoàn tất trong phiên trước) và Phase 2 (đã hoàn tất ngay trước lượt continuous-build này, xem `docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md`). Lượt này: (a) làm một delta nhỏ cho Phase 2 theo spec mới (thêm `SECURITY_CLASSIFICATION_DENIED`), (b) xây Phase 3 (query understanding/router/expansion, heuristic reranker, parent-child retrieval, MMR, contextual compression, cache) với ablation thật cho thấy 2 trong 3 kỹ thuật mới (reranker, MMR) KHÔNG cải thiện chất lượng và giữ mặc định tắt đúng theo yêu cầu "Không bật mặc định nếu benchmark không cải thiện", (c) xây một phần Phase 4 (injection scanner cho tài liệu, output-language guardrail, abstention engine, domain-guardrail composition demo), (d) xây một phần Phase 5 (observability event, resilience test, performance benchmark thật), (e) **dừng ở Phase 6** vì lý do nêu ở mục 14.

**Hai bug thật được tìm thấy và sửa trong lượt này** (không phải tính năng — lỗi thật phát hiện qua kiểm thử E2E):
1. Reranker's `exact_match` feature bỏ sót token 3 ký tự (như "UBO") do ngưỡng `len(tok) > 3` — sửa thành `>= 3`.
2. MMR tái tạo `RerankedCandidate` từ `fused_score` cũ thay vì dùng `rerank_score` thật, kết hợp với conflict-detection false-positive (coi nhiều rule khác nhau cùng trích "Chương 5" là "conflict") khiến câu hỏi UBO thật bị loại khỏi top-5 hoàn toàn. Sửa bằng cách (a) dùng đúng `rerank_score`, (b) bỏ việc dùng conflict-detection để "bảo vệ" candidate trong MMR (giữ nguyên phần gắn conflict vào GroundingPack, chỉ bỏ phần ép MMR ưu tiên).

## 2. Documents and Skills Used

Đọc trực tiếp (không giả định) 4 tài liệu RAG/Guardrail đã có từ trước (`RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md`, `CURRENT_STATE_AUDIT.md`, `IMPLEMENTATION_PLAN.md`, `IMPLEMENTATION_REPORT.md`) và `MVP_DATA_GENERATION_REPORT_V3.md` — đã đọc đầy đủ trong các lượt trước của phiên làm việc dài này, không đọc lại. Không tìm thấy `docs/CONTROLLED_HYBRID_RETRIEVAL_ARCHITECTURE.md`, `docs/GROUNDING_PACK_CONTRACT.md`, `docs/AGENT_RETRIEVAL_POLICIES.md`, `docs/RAG_EVALUATION_FRAMEWORK.md`, `docs/UNIFIED_METADATA_PLANE.md`, `docs/UNDERWRITING_SUBMISSION_ARCHITECTURE.md` — các file này chưa tồn tại (không phải "quên đọc"). Không dùng skill DOCX riêng — không cần đọc lại 2 file .docx gốc trong lượt này (đã đọc đầy đủ ở phiên trước, thông tin cần thiết đã có trong 4 doc trung gian).

## 3. Baseline

```text
git status --porcelain (loại trừ tmp_test)  →  86 file thay đổi (đầu lượt)
pytest tests/ -q  →  486 passed, 0 failed (lần 1)
pytest tests/ -q  →  486 passed, 0 failed (lần 2, ngay sau)
```

Ổn định — không phải baseline "427/427" cũ như prompt cảnh báo không nên tin, đã chạy lại thật.

## 4. Concurrent Work Detected

Trong suốt lượt continuous-build này, Gemini Agent tiếp tục hoạt động thật (không phải giả định):

- Bắt đầu: `git status` cho thấy 86 file thay đổi so với HEAD, gồm các module Underwriting/Metadata/Document-Assurance/Customer-Resolver đã có từ trước.
- Giữa lượt: một hệ thống XÁC THỰC (authentication) MỚI xuất hiện — `app/auth.py`, `app/api/v2/auth_router.py`, `tests/test_auth.py`, `lib/features/auth/` (Flutter), cùng sửa đổi `app/config.py`, `.env.v2.example`, `app/main.py` — 94 file thay đổi tại thời điểm kiểm tra sau đó.
- **Ảnh hưởng thật quan sát được**: `tests/test_auth.py::test_tampered_session_token_is_rejected` fail intermittent (fail 2/4 lần full-suite chạy trong lượt này, pass 100% khi chạy riêng lẻ) — xác nhận đây là trạng thái chưa ổn định của CHÍNH file đó (do agent kia đang sửa dở), không phải do bất kỳ thay đổi nào của lượt này (không đụng tới `app/auth.py`/`app/config.py`/`app/main.py`). Đã KHÔNG sửa file này (không phải của mình, rủi ro ghi đè công việc thật đang dở).
- Không có file nào trong danh sách Phase 2/3/4/5 tôi trực tiếp sửa (`app/knowledge/*`, `app/operations/sop_knowledge.py`, `app/safety/{citation_validator,claim_evidence_validator,document_injection_scanner,output_language_guardrail,abstention}.py`, `benchmarks/*`) bị Agent khác động vào trong suốt lượt này — xác nhận qua so sánh SHA-256 tại các checkpoint.

## 5. Phase 2 Implementation (delta so với lần trước)

Đã hoàn tất đầy đủ trong lượt TRƯỚC continuous-build này — xem `docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md` mục "## Phase 2" cho toàn bộ chi tiết (orchestrator, exact lookup, RRF, GroundingPack, claim/citation validator, benchmark 33 câu, ablation 4 config). Delta thêm trong lượt này theo spec mới:

- `MetadataFilterReason.SECURITY_CLASSIFICATION_DENIED` — reason code mới, `KnowledgeChunk.security_classification: str = "INTERNAL"` (allow-list based, không phải ordered tier — vì repo không có khái niệm "clearance level" của actor).
- Threaded `allowed_security_classifications` qua toàn bộ `_filter_eligible`/`sparse_search_bm25`/`dense_search`/`exact_lookup_by_product_id`/`eligibility_diagnostics`/`RetrievalRequest`/orchestrator.
- 2 test mới (`test_security_classification_allow_list_rejects_disallowed_chunk`, `test_security_classification_not_enforced_when_caller_omits_it`).

**KHÔNG thêm** (NOT_IMPLEMENTED, giữ nguyên từ lần trước): `TENANT_SCOPE_MISMATCH`/`BRANCH_SCOPE_MISMATCH`/`TEAM_SCOPE_MISMATCH` (không có khái niệm multi-tenant/team), `ExactLookupPort` đa-storage (policy_id/rule_id/process_id/evidence_id/customer_id/case_id/submission_id vẫn chỉ có chunk_id/product_id).

## 6. Phase 2 Tests and Gate

Đã pass ở lượt trước (486/486). Delta test mới của lượt này pass cùng bộ (`tests/retrieval/`, `tests/guardrails/`, `tests/e2e/` = 109 test sau delta).

## 7. Phase 3 Implementation

File mới, tất cả `app/knowledge/`:

| File | Nội dung |
| --- | --- |
| `query_understanding.py` | `understand_query()` — deterministic, không LLM: phát hiện entity theo ID prefix thật (`SYNTH-PROD-`, `RULE-`, `SYNTH-SOP-`...), task_type theo từ khóa, multi_hop, ambiguity |
| `query_router.py` | `route_query()` — 10 strategy theo đúng bảng rule của prompt |
| `query_expansion.py` | Từ điển đồng nghĩa CÓ VERSION (7 mục đúng ví dụ trong prompt — không bịa thêm mục nào) |
| `reranker.py` | `HeuristicReranker` — 6 feature (fusion/exact_match/authority/verification/freshness/scope_match), deterministic. `CROSS_ENCODER`/`LLM_RERANKER_EXPERIMENTAL` raise `NotImplementedError` tường minh, không fallback âm thầm |
| `diversity.py` | `mmr_select()` — Jaccard token-overlap làm proxy tương đồng (không dùng lại dense vector vì có thể là hash-BoW), bảo vệ `protected_chunk_ids` không bao giờ bị loại |
| `compression.py` | `compress_chunk_text()` — extractive, giữ offset chính xác vào text gốc (không bao giờ trích dẫn vào bản nén) |
| `retrieval_cache.py` | `RetrievalCache` — key gồm đủ 8 trường prompt yêu cầu, `invalidate_by_corpus_version()` thật (lưu `CacheKey` kèm mỗi entry để filter được, không chỉ lưu hash) |
| `observability.py` | (xem mục 12, thực ra thuộc Phase 5 nhưng liệt kê ở đây vì cùng thư mục) |

Parent-child: `KnowledgeChunk.parent_chunk_id` (mới) + `PersistentHybridIndex.expand_to_parent_context()`. Gắn THẬT vào `OperationsKnowledgeService.ingest()` — mỗi `workflow_id` giờ có 1 chunk PARENT tổng quan (`{workflow_id}:OVERVIEW`) + các step chunk con trỏ `parent_chunk_id` về đó. Corpus Operations tăng từ 11 → 15 chunk (11 step + 4 overview).

Orchestrator (`retrieval_orchestrator.py`) nhận 4 flag mới, **mặc định TẮT hết** (`query_expansion_enabled=False`, `reranker_mode=NONE`, `mmr_enabled=False`): `retrieve(request, query_expansion_enabled=, reranker_mode=, mmr_enabled=, mmr_lambda=, observer=)`.

## 8. Phase 3 Benchmark and Gate

`benchmarks/run_retrieval_benchmark.py` mở rộng thêm 4 config (F/G/H/I), chạy lại trên **cùng 33 câu** (không phải câu mới — corpus thật không đổi kích thước đáng kể):

| Config | Recall@1 | Recall@3 | Recall@5 | MRR | nDCG@5 |
| --- | --- | --- | --- | --- | --- |
| A. Legacy linear-sum | 0.583 | 0.939 | 0.967 | 0.783 | 0.831 |
| E. RRF + policy filter (Phase 2 baseline) | 0.650 | 0.956 | 0.967 | 0.817 | 0.857 |
| F. + Query expansion | 0.650 | 0.956 | 0.967 | 0.817 | 0.857 |
| G. + Heuristic rerank | 0.517 | 0.872 | 0.933 | 0.719 | 0.774 |
| H. + MMR | 0.650 | 0.689 | 0.733 | 0.690 | 0.704 |
| I. Full Phase 3 (E+F+G+H) | 0.517 | 0.722 | 0.900 | 0.667 | 0.727 |

(A/B/C/E's số liệu **khác** so với báo cáo Phase 2 trước đó — nguyên nhân thật: Operations index tăng từ 11 lên 15 chunk sau khi thêm parent-child overview chunks, các overview chunk này CŨNG tham gia ranking bình thường như mọi chunk khác và cạnh tranh vị trí top-1 cho một số câu hỏi Operations. Đây là một đánh đổi kiến trúc thật đáng ghi nhận: thêm parent chunk vào CÙNG index phục vụ ranking sẽ pha loãng benchmark ranking-only trừ khi overview chunk bị lọc khỏi ranking một cách có chủ đích — KHÔNG sửa trong lượt này, ghi vào "Hạn chế".)

**Kết luận trung thực, đúng theo yêu cầu Phase Gate 3 ("quality tăng hoặc feature để disabled")**: Query expansion (F) trung tính. Heuristic reranker (G) và MMR (H) đều làm GIẢM chất lượng trên corpus 33 câu này (G giảm Recall@1 từ 0.65→0.52; H giảm Recall@3 nghiêm trọng từ 0.956→0.689). Full Phase 3 (I) cũng tệ hơn baseline E. **Quyết định: giữ cả 3 flag TẮT theo mặc định** (đã đúng ngay từ thiết kế orchestrator) — không có bất kỳ deployment/test nào trong repo bật chúng theo mặc định. Code + test được giữ lại (hữu ích cho corpus lớn hơn sau này), nhưng không báo "đã cải thiện retrieval".

**Gate 3**: full suite `531 passed, 0 failed` — chạy 2 lần liên tiếp sau khi sửa 1 flaky test thật (xem mục 19).

## 9. Phase 4 Guardrails

| File | Trạng thái |
| --- | --- |
| `app/safety/document_injection_scanner.py` | IMPLEMENTED — quét TÀI LIỆU đã index (khác `input_guardrails_v2.py` vốn quét USER input), 19 pattern (tiếng Anh + Việt, fold() diacritic-insensitive), tách business_content/untrusted_instruction_spans, offset chính xác vào text gốc |
| `app/safety/output_language_guardrail.py` | IMPLEMENTED — 8 cụm từ cấm đúng list prompt, fold()-based (robust với text không dấu) |
| `app/safety/abstention.py` | IMPLEMENTED — ghép tín hiệu THẬT từ Phase 2 (`RetrievalErrorCode`) + claim validator (`ClaimEvidenceStatus`) thành `AbstentionDecision`, không phải nguồn sự thật mới |
| `tests/guardrails/test_domain_guardrail_composition.py` | Chứng minh `app/safety/domain_guardrails.py` (module CỦA AGENT KHÁC, không sửa) hoạt động đúng khi nhận input dẫn xuất từ GroundingPack thật |

**KHÔNG xây trong lượt này (NOT_IMPLEMENTED)**:
- Prompt injection scanner CHƯA được nối vào orchestrator pipeline thật (đứng riêng, có test, chưa có call site tự động chạy nó trước khi đưa content vào GroundingItem).
- Schema Guardrail với retry-loop giới hạn (Pydantic `extra="forbid"` đã có sẵn từ trước trên mọi model, nhưng "retry rồi AGENT_OUTPUT_INVALID" là một state machine chưa xây).
- Semantic Claim Validation (lớp bổ sung sau deterministic — không có LLM call site trong repo để làm lớp này thật).
- Risk/Action Guardrail tích hợp đầy đủ (package_hash/idempotency/separation-of-duties) — các mảnh này đã tồn tại RẢI RÁC ở nơi khác trong repo (approval/service.py, risk_gate.py — không phải của Phase 2-5 RAG work) nhưng chưa được thống nhất thành 1 lớp Risk/Action Guardrail như prompt mô tả.
- Human Review context object có cấu trúc riêng (dữ liệu cần thiết đã có rải rác trong `AbstentionDecision`/`ClaimEvidenceResult`, nhưng chưa gộp thành 1 schema `HumanReviewContext`).

## 10. Phase 4 Security Tests

29 test trong `tests/guardrails/` (21 cũ từ Phase 2 + 8 mới: 5 injection scanner, 5 output-language — 4 unique sau khi trừ overlap, 5 abstention). Full suite Gate 4: `549 passed, 0 failed`, 2 lần liên tiếp.

## 11. Phase 5 Evaluation

**Không tạo bộ 100-120 câu mới.** Dùng lại đúng 33 câu benchmark của Phase 2/3 — lý do đã ghi trong `benchmarks/data/retrieval_queries.json`'s `scope_note`: corpus thật (25 bản ghi gốc, nay 29 sau parent-child) không đủ lớn để 100+ câu không suy biến thành paraphrase trùng lặp. Đây là một giới hạn thật, không phải bỏ sót — mở rộng corpus (nhiều sản phẩm/rule/SOP hơn) là điều kiện tiên quyết để một benchmark 100+ câu có ý nghĩa thật.

Per-Agent metrics: KHÔNG xây bộ đầy đủ 4 nhóm metric prompt liệt kê (Product/Legal/Operations/Underwriting Compiler) — `benchmarks/metrics.py` (đã có TỪ TRƯỚC, phục vụ một benchmark case-level khác) đã có `citation_validity`/`unsupported_claim_rate`/`product_recall` — không xây lại, nhưng cũng chưa NỐI với pipeline Phase 2-3 retrieval mới trong lượt này (2 hệ benchmark — case-level cũ và retrieval-level mới — vẫn tách biệt).

## 12. Phase 5 Observability

`app/knowledge/observability.py` — `RetrievalEvent` (dataclass, không PII/secret — chỉ chunk_id/reason code, KHÔNG BAO GIỜ chứa `content`/`raw_query`/`quote`, verify bằng test trực tiếp), `InMemoryObservabilityRecorder`. Orchestrator nhận `observer:` kwarg (mặc định `None`, không phá bất kỳ call site cũ nào). 4 test mới xác nhận: 1 event/lần gọi, log dict sạch PII, đếm được theo error_code, không bắt buộc observer.

**IMPLEMENTED_WITH_DETERMINISTIC_ADAPTER** — không có exporter Prometheus/OpenTelemetry thật (không có dependency nào cài trong repo), chỉ có in-memory recorder cho test/debug.

## 13. Phase 5 Performance

`benchmarks/run_performance_benchmark.py` — đo THẬT (không fabricate target), `LocalEmbedding` (không network):

```json
legal_corpus_size: 9, operations_corpus_size: 15
legal_cold_ms: 3.748, legal_warm_p50_ms: 2.591, legal_warm_p95_ms: 3.130
operations_cold_ms: 3.446, operations_warm_p50_ms: 3.298, operations_warm_p95_ms: 3.982
```

Live semantic provider (OpenAI/Gemini) latency **BLOCKED_BY_ENVIRONMENT** — không đo trong lượt này để tránh lặp lại rủi ro va chạm file cache dùng chung `data/vector_db/openai_vector_cache.json` với agent khác (đã ghi nhận là sự cố thật ở Phase 2). Load test đa luồng/đồng thời: **NOT_IMPLEMENTED** (đo đơn luồng, tuần tự).

Resilience: `tests/retrieval/test_resilience.py` (4 test) — xác nhận Legal fail-closed (ERROR/SOURCE_SCOPE_EMPTY) khác Product/Operations degrade (OK/NO_RELEVANT_RESULT, không GroundingPack) trên cùng tình huống index rỗng; xác nhận `INDEX_NOT_READY` (candidate_count_before_filter=0) vẫn phân biệt được với `NO_RELEVANT_RESULT` (candidate_count_before_filter>0) qua orchestrator.

**Gate 5**: full suite lần 1 có 1 fail (`tests/test_auth.py`, file của agent khác, xem mục 4) — 556 passed, 1 failed; lần 2 chạy lại sạch: 557 passed, 0 failed. Không coi đây là "hai lần liên tiếp pass" theo nghĩa chặt — ghi rõ nguyên nhân (không phải code của lượt này) thay vì che giấu.

## 14. Phase 6 — STOPPED (điều kiện dừng #2)

**Quyết định dừng, không xây Phase 6**, theo đúng điều kiện dừng #2 mà chính prompt gốc liệt kê: *"Có thay đổi đồng thời từ Agent khác làm thay đổi trực tiếp contract đang sửa."*

Bằng chứng cụ thể: toàn bộ phạm vi Phase 6 (Customer Resolver, Document Assurance, Requirement Compiler, Evidence Checklist, Submission Readiness, RM Submission Approval, Underwriting Submission/Workflow, Information Request, Metadata Lineage, API mới `/api/v2/cases/.../submissions/...`, `/api/v2/underwriting/...`) **đã và đang được một Agent khác (Gemini, xem `AI_LOG.md`) xây dựng activEly trong CHÍNH repository này**, xác nhận qua các file đã tồn tại/đang sửa trước và trong suốt phiên làm việc:

```text
app/context/customer_resolver.py       (ResolutionStatus, CustomerResolver — Phase 6 mục 53)
app/intake/document_assurance.py       (Phase 6 mục 56)
app/workflow/requirement_compiler.py   (Phase 6 mục 55)
app/workflow/submission.py             (Phase 6 mục 58-60)
app/schemas/v2/underwriting.py         (Phase 6 mục 60-62)
app/schemas/v2/metadata.py + app/metadata/models.py  (Phase 6 mục 63 — Metadata Lineage)
app/knowledge/grounding_validator.py   (P0.3 Trust Foundation — chồng lấn Phase 6's evidence validation)
```

Nếu lượt này TỰ xây một `UnderwritingCasePacket`/state machine/API endpoint MỚI song song, hậu quả thật (không phải rủi ro lý thuyết):
1. Hai bộ contract khác nhau (`ResolutionResult` của agent kia vs một schema tự tạo mới) cho CÙNG một khái niệm nghiệp vụ — sẽ phải hợp nhất sau, tốn công gấp đôi.
2. Có thể ghi đè trực tiếp lên các file agent kia đang sửa dở (`app/api/v2/router.py` đã đổi tay nhiều lần trong phiên, xem mục 4 của `docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md`).
3. Không có đủ ngữ cảnh về state machine/API mà agent kia ĐANG thiết kế để đảm bảo tương thích thật — bất kỳ đoán mò nào (ví dụ tự chọn tên trạng thái `SUBMISSION_FROZEN`) đều có nguy cơ SAI với những gì agent kia đã hoặc sẽ implement.

**Điều đã làm được liên quan Phase 6 mà KHÔNG xung đột**: `ControlledRetrievalOrchestrator`, `RetrievalGroundingPack`, `claim_evidence_validator`, `abstention` (Phase 2-4) đều là hạ tầng RETRIEVAL — đây chính xác là thứ Phase 6's Requirement Compiler/Document Assurance/Underwriting Compiler SẼ CẦN để lấy bằng chứng có trích dẫn thật, khi agent kia (hoặc một lượt sau) nối chúng vào. Không có gì trong Phase 2-5 cần xây lại khi Phase 6 thực sự bắt đầu.

**Khuyến nghị cho lượt tiếp theo**: đọc `AI_LOG.md` mới nhất + trạng thái các file Phase-6-liên-quan của agent kia TRƯỚC khi bắt đầu Phase 6, phối hợp (hoặc chờ agent kia xác nhận tạm dừng, đúng pattern đã áp dụng thành công ở giữa phiên làm việc này) thay vì xây song song.

## 15-17. Underwriting Integration / Metadata Lineage / Final E2E

NOT_IMPLEMENTED trong lượt này — hệ quả trực tiếp của quyết định dừng ở mục 14.

## 18. Final Full-suite Results

```text
pytest tests/ -q  → 531 passed, 0 failed (Gate 3, x2)
pytest tests/ -q  → 549 passed, 0 failed (Gate 4, x2)
pytest tests/ -q  → 556 passed, 1 failed (tests/test_auth.py — KHÔNG phải code lượt này, xem mục 4/13)
pytest tests/ -q  → 557 passed, 0 failed (chạy lại ngay sau, sạch)
```

## 19. Hard Safety Gates

| Gate (Phase 2/3 phạm vi thật của lượt này) | Kết quả |
| --- | --- |
| `cross_customer_source_selected = 0` | VERIFIED_BY_EXECUTION (kế thừa Phase 2, không đổi) |
| `quarantined_source_selected = 0` | VERIFIED_BY_EXECUTION |
| `superseded_source_used_as_current = 0` | VERIFIED_BY_EXECUTION |
| `critical_claim_without_grounding = 0` | VERIFIED_BY_EXECUTION (`SOURCE_UNAVAILABLE`) |
| `provider_failure_reported_as_no_result = 0` | VERIFIED_BY_EXECUTION (Legal fail-closed vẫn đúng qua Phase 3 flag) |
| `mmr/rerank làm giảm chất lượng nhưng vẫn được bật mặc định` | **KHÔNG XẢY RA** — đã kiểm chứng bằng ablation thật và giữ tắt mặc định (mục 8) |
| `prompt_injection_bypass = 0` (phạm vi hẹp: chỉ document scanner mới, chưa nối runtime) | VERIFIED_BY_EXECUTION cho MODULE ĐỨNG RIÊNG; NOT_RUNTIME_WIRED cho pipeline thật |
| `cross_customer_leakage / underwriting_fabricated_claim / action_without_approval / ...` (phạm vi Phase 6) | NOT_APPLICABLE — Phase 6 không được xây trong lượt này |

## 20. Legacy Compatibility

`search()`/`search_with_diagnostics()` (Phase 0/1) không đổi. Orchestrator (Phase 2) không đổi behavior khi không truyền flag mới. 4 flag Phase 3 mặc định giữ nguyên hành vi Phase 2. `observer=` (Phase 5) mặc định `None`, không ảnh hưởng call site cũ. Toàn bộ xác nhận bằng test hồi quy (`test_legacy_search_compatibility.py`, `test_orchestrator_phase3_flags.py::test_all_flags_off_matches_phase_2_baseline_behavior`, `test_observability.py::test_no_observer_means_no_event_recording_overhead`).

## 21. Files Created/Modified (lượt continuous-build này, không tính Phase 2 trước đó)

**Mới**: `app/knowledge/{query_understanding,query_router,query_expansion,reranker,diversity,compression,retrieval_cache,observability}.py`, `app/safety/{document_injection_scanner,output_language_guardrail,abstention}.py`, `benchmarks/run_performance_benchmark.py`, 12 file test mới (`tests/retrieval/test_{query_understanding,query_router,query_expansion,heuristic_reranker,mmr_diversity,contextual_compression,retrieval_cache,parent_child_retrieval,orchestrator_phase3_flags,observability,resilience}.py`, `tests/guardrails/test_{document_injection_scanner,output_language_guardrail,abstention,domain_guardrail_composition}.py`), file này.

**Sửa**: `app/knowledge/index.py` (SECURITY_CLASSIFICATION_DENIED, expand_to_parent_context), `app/knowledge/models.py` (security_classification, parent_chunk_id), `app/knowledge/retrieval_contracts.py` (allowed_security_classifications), `app/knowledge/retrieval_orchestrator.py` (4 flag Phase 3, observer, security_classification threading), `app/operations/sop_knowledge.py` (parent-child ingestion), `benchmarks/run_retrieval_benchmark.py` (4 config mới), `benchmarks/data/retrieval_queries.json` (không đổi câu hỏi, chỉ đổi scope_note đã có sẵn), `tests/retrieval/test_chunk_lifecycle_filters.py` (2 test mới).

## 22. Migrations

Không có migration schema SQL — mọi field mới (`security_classification`, `parent_chunk_id`) là Pydantic optional/default, đọc lại payload JSON cũ tự động hợp lệ. Không cần rebuild index.

## 23. Mocked Components

`LocalEmbedding` cho mọi test/benchmark (hash-BoW, không phải semantic thật — đã ghi nhãn `RepresentationType.HASH_BOW_VECTOR` xuyên suốt). `_config_orchestrator`/benchmark Product ingestion là dữ liệu thật từ `data/synthetic/v2/products.json`, không phải mock.

## 24. Live Integrations

Không có live OpenAI/Gemini call nào trong lượt này (cố tình, xem mục 13 — tránh va chạm cache file dùng chung). Real semantic-embedding ablation vẫn `BLOCKED_BY_ENVIRONMENT`.

## 25. Known Limitations

1. Orchestrator (toàn bộ Phase 2-5) vẫn **KHÔNG được gọi từ bất kỳ luồng request thật nào** — giới hạn lớn nhất, giữ nguyên từ Phase 2.
2. Reranker/MMR tồn tại nhưng benchmark thật cho thấy chúng làm GIẢM chất lượng trên corpus 33 câu — giữ tắt, cần corpus lớn hơn hoặc trọng số khác để đánh giá lại.
3. Parent-child overview chunks làm thay đổi (giảm) benchmark ranking-only cho Operations vì tham gia ranking như chunk thường — cần quyết định kiến trúc (lọc overview khỏi ranking mặc định?) chưa được đưa ra.
4. Prompt injection scanner, output-language guardrail, abstention engine đều ĐỨNG RIÊNG — chưa nối vào một luồng Agent-output thật nào.
5. Phase 5 evaluation set vẫn 33 câu (không phải 100+) — giới hạn bởi kích thước corpus thật.
6. `tests/test_auth.py` (không phải của lượt này) flaky — xem mục 4/13, không sửa vì không sở hữu file.
7. Toàn bộ Phase 6 không được xây — xem mục 14.

## 26. Unverified Components

Live semantic-provider performance/ablation. Load test đa luồng thật. Schema Guardrail retry-loop. Risk/Action Guardrail hợp nhất.

## 27. Acceptance Criteria

Phần lớn tiêu chí Final Hard Gates (mục 66 của prompt gốc) thuộc phạm vi Phase 6 — **NOT_APPLICABLE** vì Phase 6 không được xây. Trong phạm vi Phase 2-5 thực sự triển khai: hard gate liên quan retrieval/guardrail/observability/resilience đều đạt VERIFIED_BY_EXECUTION (mục 19), full suite pass (mục 18, có ghi chú rõ 1 lần fail không liên quan), backward compatibility giữ nguyên (mục 20). Không tuyên bố "production-ready" cho toàn hệ thống — chỉ tuyên bố đúng những gì đã verify.
