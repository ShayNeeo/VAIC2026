# RAG & Guardrail Implementation Plan

## 1. Executive Summary

Nâng cấp Controlled Hybrid Retrieval & AI Assurance Plane cho Product/
Legal/Operations Agent, theo prompt 50 phần người dùng cung cấp, đối
chiếu với `docs/RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md` (yêu cầu gốc từ
2 tài liệu docx) và `docs/RAG_GUARDRAIL_CURRENT_STATE_AUDIT.md` (trạng
thái thật, đã audit bằng code inspection). Baseline: **375/375 test pass**
(bao gồm cả uncommitted work của một Gemini Agent khác đang chạy song
song trong cùng repo — xem mục 3).

## 2. Current RAG Architecture

Tóm tắt từ audit: hybrid fusion tuyến tính (`0.6*dense + 0.4*sparse +
exact_bonus`, `app/knowledge/index.py:312`) trên `PersistentHybridIndex`
(SQLite, không có vector DB thật); dense mặc định là hash bag-of-words
(`LocalEmbedding`), không phải semantic embedding thật; không có reranker;
Legal/Product dùng chung index, chỉ khác threshold; Operations không có
retrieval; `GroundingPack`/`Citation` đã định nghĩa nhưng dead code;
Legal có một implementation RAG trùng lặp, dead code
(`app/legal/legal_rag.py`). Chi tiết đầy đủ, có `file:line`, xem audit
doc.

## 3. Current Safety Architecture

`app/safety/evidence_validator.py::validate_claim` làm re-verification
thật (substring match quote vào chunk đã index, kiểm tra version/expiry,
conflict detection). `app/safety/input_guardrails_v2.py::screen_input`
là 5-pattern regex injection scanner, dùng thống nhất ở input/document
quarantine/benchmark. Domain guardrail cho Legal (non-overridable
blocker) đã có, test thật (`BLOCK_NOT_OVERRIDABLE`, xây dựng ở vòng
specialist-review trước trong cùng repo). Product/Operations domain
guardrail: UNVERIFIED, cần audit riêng trước Phase 4.

**Ràng buộc mới phát sinh giữa chừng:** một Gemini AI Agent khác đang có
uncommitted changes chạm nhiều file trùng với phạm vi RAG/Guardrail này
(`app/knowledge/rag_provider.py`, `app/product/service.py`,
`app/operations/service.py`, `app/workflow/risk_gate.py`, ...), đang xây
dựng hệ thống Underwriting Handoff (Customer Resolver/Metadata Plane/
Document Assurance/Requirement Compiler/Submission — theo Doc B nhưng là
phần khác, không phải phần RAG/Guardrail). Người dùng đã xác nhận: **cứ
tiếp tục, cho phép ghi đè nếu cần** — quyết định này được ghi lại ở đây
để có căn cứ, không phải tự ý quyết định.

## 4. Repository Gaps

Xem bảng đầy đủ trong `docs/RAG_GUARDRAIL_CURRENT_STATE_AUDIT.md`. Tóm
tắt các gap ưu tiên cao nhất (ảnh hưởng trực tiếp tới hallucination/
cross-scope risk — đúng tinh thần Phase 0 của prompt mục 44):

1. Reranking không tồn tại (NOT_IMPLEMENTED).
2. `GroundingPack` chưa từng chạy (DEAD_CODE).
3. Operations Agent không qua retrieval nào (NOT_IMPLEMENTED).
4. Legal có RAG implementation trùng, dead code, rủi ro bảo trì.
5. Fusion là linear sum, không phải RRF (PARTIALLY_IMPLEMENTED).
6. Injection scanner chỉ 5 regex pattern tĩnh (IMPLEMENTED_BUT_UNSAFE).
7. Citation validator chưa kiểm `page`/`text_span`/`quote_hash`
   (PARTIALLY_IMPLEMENTED).
8. Không có retrieval-ranking eval (Recall@k/MRR/nDCG) — chỉ có outcome
   metric end-to-end (IMPLEMENTED_BUT_UNMEASURED).
9. ACL/metadata filter TRƯỚC retrieval — UNVERIFIED, cần xác nhận trước
   khi tuyên bố an toàn.

## 5. Target Architecture

Theo đúng pipeline prompt mục 5, với một điều chỉnh thực tế: **không xây
song song một "Controlled Retrieval Plane" tách rời khỏi
`PersistentHybridIndex` hiện có** — sẽ mở rộng module hiện có
(`app/knowledge/`) thay vì tạo một tầng trừu tượng hoàn toàn mới, đúng
nguyên tắc "Không tạo module song song nếu repository đã có nơi phù hợp"
(prompt mục 45). Layout đề xuất, bám sát cấu trúc `app/` hiện có:

```text
app/knowledge/
  index.py           (mở rộng: + RRF option, + reranker hook)
  rag_provider.py     (mở rộng: wire GroundingPack thật, không tạo lại)
  grounding.py         (MỚI: lắp ráp GroundingPack từ index results)
  reranker.py           (MỚI: RerankerPort + heuristic reranker)
  conflict.py            (MỚI: conflict detection giữa candidate)

app/safety/
  evidence_validator.py (mở rộng: + page/text_span/quote_hash check)
  input_guardrails_v2.py (mở rộng: pattern set rộng hơn, giữ tên hàm cũ)
  citation_validator.py   (MỚI)
  domain_guardrails.py     (MỚI: product/legal/operations forbidden-action check)

app/operations/
  service.py (mở rộng: retrieval thật thay vì đọc JSON tĩnh)
```

Không tạo `app/retrieval/`/`app/guardrails/` song song như prompt mục 45
gợi ý, vì `app/knowledge/`+`app/safety/` đã đóng đúng vai trò đó.

## 6-16. Query Understanding / Routing / Sparse / Dense / Fusion / Expansion / Hierarchical / Metadata Filtering / Reranking / Diversity / Compression

Do phạm vi thật sự lớn (đúng như đã cảnh báo người dùng trước khi họ chọn
scope đầy đủ), các mục 6-16 được triển khai theo thứ tự ưu tiên Phase
0-3 (mục 24 dưới), KHÔNG triển khai đồng thời toàn bộ trong một lượt.
Quyết định kỹ thuật cho từng mục:

- **Query Understanding/Routing (6-7)**: KHÔNG xây `RetrievalRequest`
  Pydantic model đầy đủ 20+ field như prompt mục 6 ngay — quá lớn so với
  call site hiện tại (retrieval được gọi trực tiếp bằng
  query+threshold+scope trong `index.py`/`legal_service.py`). Thay vào
  đó Phase 1 thêm một `RetrievalContext` tối giản (agent_type, customer_id,
  case_id, security_scope) đủ để agent-specific policy và ACL hoạt động,
  không bịa field cho concept chưa tồn tại (tenant/team — xem mục 12 của
  extraction doc).
- **Sparse (8.1)**: giữ token-overlap hiện tại làm baseline A cho ablation
  (mục 38 prompt); KHÔNG thay bằng BM25 thật trong lượt này (out of
  scope Phase 0-3, ghi rõ UNVERIFIED/NOT_IMPLEMENTED, không bịa đã có
  BM25).
- **Dense (8.2)**: giữ nguyên `LocalEmbedding` hash-based làm baseline B;
  không đổi provider mặc định (tránh phá test suite phụ thuộc
  deterministic hash embedding).
- **Fusion (8.3)**: Phase 2 thêm RRF như một `fusion.method` config option
  cạnh linear-sum hiện có, KHÔNG xóa linear-sum (đó là baseline C/D cho
  ablation).
- **Query expansion/HyDE/step-back (9)**: NOT_IMPLEMENTED trong lượt này,
  ghi rõ trong report, không bịa.
- **Hierarchical parent-child (10)**: NOT_IMPLEMENTED trong lượt này.
- **Metadata filtering (12)**: Phase 0 xác nhận (hoặc sửa nếu sai) rằng
  filter chạy trước khi trả candidate — đây là hard security boundary,
  ưu tiên cao nhất trong Phase 0.
- **Reranking (14)**: Phase 3 thêm `RerankerPort` + `HeuristicReranker`
  (deterministic, không LLM) — đúng khuyến nghị MVP của prompt mục 14.
- **Diversity/MMR (15), Contextual compression (16)**: NOT_IMPLEMENTED
  trong lượt này.

## 17. Conflict Detection

Mở rộng `detect_conflicts` đã có (`evidence_validator.py:195`, hiện chỉ
phát hiện cùng claim_id khác quote) thành `RetrievalConflict` object đầy
đủ field theo prompt mục 17, dùng cho cả evidence-level và
retrieval-candidate-level conflict. Phase 2.

## 18. Grounding Pack

Nối `GroundingPack`/`Citation` (`app/knowledge/rag_provider.py:29-41`,
hiện dead code) vào luồng thật: `app/knowledge/grounding.py` (mới) lắp
ráp từ kết quả `PersistentHybridIndex.search` + reranker + conflict
detector. Phase 2.

## 19. Agent Retrieval Policies

Theo bảng Doc B mục 30 (đã trích trong extraction doc mục 2) — implement
`AGENT_RETRIEVAL_POLICIES` config (sparse/dense weight, allowed sources,
forbidden claim types) cho Product/Legal/Operations, đặc biệt: cho
Operations retrieval THẬT lần đầu tiên (Phase 1, vì đây là gap nghiêm
trọng nhất — Operations hiện 0% retrieval).

## 20. Prompt Injection

Mở rộng `screen_input` pattern set (Phase 4), KHÔNG tuyên bố "đã chặn
prompt injection" nếu vẫn chỉ regex — báo cáo phải ghi rõ
IMPLEMENTED_BUT_UNSAFE→PARTIALLY_IMPROVED, không phải "solved."

## 21. Claim/Evidence Guardrail

Mở rộng `Evidence` schema (`app/schemas/v2/shared_case_state.py`) thêm
`page`, `text_span`, `quote_hash` optional fields; `validate_claim` kiểm
thêm các field này khi có. Phase 4.

## 22. Citation Validation

`app/safety/citation_validator.py` (mới) — kiểm tra citation đủ field
theo prompt mục 28, dùng lại logic re-verification đã có trong
`evidence_validator.py` thay vì viết lại từ đầu. Phase 4.

## 23. Domain Guardrails

Product/Operations domain guardrail (forbidden phrase "chắc chắn",
"đã được phê duyệt", official price/limit không nguồn — prompt mục 29-30)
là phần MỚI hoàn toàn, chưa có gì để mở rộng. Phase 4.

## 24. Failure Handling

Phase 0: phân biệt rõ `NO_RELEVANT_RESULT` vs `PROVIDER_UNAVAILABLE` vs
`INDEX_NOT_READY` thay vì mọi lỗi retrieval hiện đổ về "no results" —
đây là gap an toàn cụ thể nhất và rẻ nhất để sửa ngay, ưu tiên P0 thật
sự đầu tiên.

## 25. Cache

UNVERIFIED trong audit — Phase 5 sẽ audit trước khi thiết kế, tránh xây
trùng cache đã có ở tầng khác (vd `app/observability/`).

## 26. Observability

Bổ sung metrics tối thiểu prompt mục 33 đòi (retrieval_requests_total,
candidate_count, filtered_candidate_count, citation_validity,
prompt_injection_detection_rate) vào `app/observability/runtime.py`'s
`metrics` object đã có (không tạo hệ thống metrics mới song song).

## 27. Evaluation

Dùng lại `data/synthetic/v3/` (V3 data pack đã build ở vòng trước) làm
nguồn customer/product/policy cho eval queries — không bịa dữ liệu mới.
Bổ sung retrieval-ranking metric riêng (Recall@k/MRR/nDCG) vào
`benchmarks/metrics.py`. Phase 5.

## 28. Ablation

So sánh sparse-only / dense-only / hybrid-linear (hiện có) / hybrid-RRF
(mới) / +reranker (mới) trên cùng eval set. Phase 5, sau khi Phase 2-3
xong.

## 29. Tests

Theo đúng danh sách file prompt mục 40, nhưng chỉ tạo file cho phần THẬT
SỰ implement ở mỗi Phase — không tạo test rỗng/skip cho phần chưa code
(vi phạm "no bịa test result").

## 30. Rollout

Không đổi `RAG_PROVIDER` mode/API contract hiện có (`local/mcp/hybrid`
giữ nguyên). Mọi thay đổi backward-compatible, full suite phải xanh sau
mỗi Phase trước khi qua Phase kế tiếp.

## 31. Risks

- Xung đột file với Gemini Agent khác đang chạy song song (đã xác nhận
  với người dùng, chấp nhận rủi ro ghi đè — mục 3).
- Thời lượng thật sự cần cho đủ 6 Phase vượt xa một phiên chat (đã cảnh
  báo người dùng trước khi họ chọn full scope).
- Dense retrieval mặc định vẫn là hash-based sau Phase 0-5 (không đổi
  embedding provider mặc định) — báo cáo cuối phải nói rõ đây KHÔNG phải
  semantic dense retrieval thật, tránh overclaim.

## 32. Out of Scope

- BM25 thật, embedding ngữ nghĩa thật, vector DB thật, LLM/cross-encoder
  reranker, HyDE, multi-query, hierarchical parent-child chunking,
  contextual compression, diversity/MMR, retrieval cache mới, 100-query
  full eval dataset — ghi rõ NOT_IMPLEMENTED trong report cuối, không
  bịa.
- Toàn bộ hệ thống Underwriting Handoff (Customer Resolver/Document
  Assurance/Metadata Plane/Submission) — đó là phạm vi của Gemini Agent
  khác đang chạy song song (Doc B phần lớn), không phải phạm vi
  RAG/Guardrail 50-phần này.
