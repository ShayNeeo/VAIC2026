# RAG & Guardrail Requirement Extraction

Nguồn: cả hai tài liệu đã được đọc đầy đủ, trực tiếp bằng `python-docx`
(không skim, không dùng bản extract cũ của người khác trong repo):

- **Doc A** = `docs/SHB_Corporate_Sales_MVP_Data_Blueprint_V3_Proposal.docx`
  (446 đoạn + 79 bảng) — RAG được nói tới ở mục 10 (Product Knowledge/
  Ingestion/Hybrid RAG) và mục 11 (Eligibility/Legal).
- **Doc B** = `docs/SHB_Corporate_Sales_Copilot_End_to_End_Evidence_Underwriting_AI_Assurance.docx`
  (453 đoạn + 36 bảng) — có hẳn mục 30 "Retrieval architecture để hạn chế
  hallucination" và mục 31 "Guardrail nhiều lớp", đã được thiết kế sát với
  chính ba Agent (Product/Legal/Operations) và Requirement/Underwriting
  Compiler của repo này, chi tiết và có thể triển khai hơn nhiều so với
  prompt 50 phần (vốn là playbook RAG tổng quát, không riêng cho repo này).

Prompt 50 phần dán vào chat được coi là **spec chi tiết cần tuân theo**,
hai tài liệu trên là **nguồn yêu cầu nghiệp vụ gốc** phải đối chiếu khi có
mâu thuẫn hoặc khi prompt không nói rõ.

## 1. Retrieval requirements

- Hybrid: kết hợp exact lookup + sparse + dense + metadata filter (Doc A
  mục 10.2/10.3; Doc B mục 30.1 bước 3-4; prompt mục 8).
- Exact/structured lookup phải chạy **trước** semantic search khi query
  chứa ID (Doc B mục 30.1 bước 3: "Exact metadata/key lookup trước;
  semantic retrieval sau"; prompt mục 7 "Exact-first").
- Query phải qua ACL/effective-date/segment filter trước khi vào
  dense/sparse (Doc A mục 10.3; Doc B mục 30.1 bước 4).
- Reranking theo authority, applicability, freshness và relevance (Doc B
  mục 30.1 bước 5; Doc A mục 13; prompt mục 13-14).
- Threshold/OOS gate → top 3-5 chunk cuối cùng (Doc A mục 10.3).

## 2. Agent-specific sources

Theo Doc B bảng mục 30 (T323) — đây là bảng cụ thể nhất, ưu tiên bám theo
bảng này hơn phần liệt kê chung ở prompt mục 19:

| Agent | Nguồn retrieval | Không được tự suy đoán |
| --- | --- | --- |
| Product | Product catalog, customer facts, need profile, product evidence, approved commercial rules | Phí, lãi suất, limit, approval hoặc điều kiện không có nguồn |
| Legal/Policy | Policy/rule registry, KYC/UBO evidence, legal docs, exception records | Kết luận pháp lý không policy; tự gỡ absolute block; tự suy ra UBO |
| Operations | SOP, process catalog, implementation checklist, integration/signature policy | Cam kết SLA/chức năng không SOP; tự đánh dấu ready |
| Requirement Compiler | Structured output của 3 Agent, requirement/policy registry, evidence inventory | Tạo checklist tự do không requirement code |
| Underwriting Compiler | Frozen submission snapshot, evidence matrix, source manifest, validated outputs | Tự thêm claim, che conflict hoặc sửa số liệu |

## 3. Required metadata

Chunk-level (prompt mục 10-11; Doc A mục 10.2 "Chunk phải giữ section
path, page, product ID, effective date, active flag, access scope,
content hash và parent/neighbor references"): `chunk_id`,
`document_id`, `document_version`, `section_path`, `effective_from/to`,
`authority_tier`, `product_ids/policy_ids/process_ids`,
`security_classification`.

Run-level (Doc B mục 29.1 "Metadata envelope bắt buộc", mục 15):
`meta_id/type/schema_version`, `tenant_id/branch_id/team_id`,
`trace_id/case_id/customer_id`, `actor`, `source`, `processing` (model/
prompt/policy/catalog/SOP version), `quality` (confidence/validation/
conflicts), `lineage`, `security`, `lifecycle`, `integrity`
(content_hash/idempotency_key).

## 4. Source authority hierarchy

Doc B mục 30.2 (5 tier, cụ thể hơn prompt mục 13's generic 5-tier list):

| Tier | Nguồn | Policy sử dụng |
| --- | --- | --- |
| 1 | Core/CRM versioned data, approved catalog, policy registry, verified/signed documents | Ưu tiên cao; kiểm tra freshness/applicability |
| 2 | Verified Evidence, specialist review, approved exception, SOP | Dùng trong đúng scope |
| 3 | Customer upload pending, unverified form, meeting note | Unverified fact; không tạo kết luận chắc chắn |
| 4 | Model inference từ facts | Gắn INFERENCE, confidence và supporting refs |
| 5 | Không có nguồn | Không xuất như fact; tạo question/requirement hoặc abstain |

Doc A mục 9.2 có một phân tầng khác (A-internal/A-official/B-licensed/
C-open/D-derived/E-synthetic) cho **market data ngoài SHB** — đây là một
concern khác (nguồn dữ liệu thị trường bên ngoài), không mâu thuẫn với
5-tier ở trên (nguồn nội bộ cho retrieval runtime); giữ cả hai, dùng đúng
ngữ cảnh của từng cái.

## 5. Citation requirements

Citation phải có đủ: `source_id`, `source_version`, `document_id`,
`document_version`, `page`, `section`, `text_span`, `quote_hash`,
`grounding_item_id` (prompt mục 28). Validator phải kiểm tra source tồn
tại, version tồn tại, text span tồn tại, quote hash khớp, claim không
vượt ý nghĩa nguồn, source còn hiệu lực, user có quyền xem source (prompt
mục 28). Doc B mục 25 (Submission Readiness) nhắc lại: "Mọi claim trọng
yếu có source/evidence refs; claim chưa đủ ghi INSUFFICIENT_EVIDENCE."

## 6. Freshness requirements

Doc B mục 5.2 (bảng trạng thái reuse: SATISFIED_VERIFIED/
REFRESH_REQUIRED/...) và mục 8.1 ("Evidence phải còn hiệu lực theo policy
của yêu cầu mới, không chỉ theo ngày hết hạn ghi trên giấy"). Doc A mục
9.9 ("Freshness: TTL/update/effective date -> Mark stale; block
time-sensitive decision"). Current policy phải luôn ưu tiên hơn stale
policy dù stale policy semantic gần hơn (prompt Scenario 6, mục 41).

## 7. Conflict requirements

Doc B mục 30 retrieval pipeline bước 6 "Deduplicate và detect conflicts";
Doc B mục 5.2 trạng thái `CONFLICTING_EXISTING`. Prompt mục 17
`RetrievalConflict` object (subject_ref, field_name, source_a/source_b,
value_a/value_b, resolution_status, requires_human_review). Resolution
priority cả hai nguồn đều thống nhất: source authority → verification →
freshness → applicability → human review (Doc B mục 5.2 hàng
CONFLICTING_EXISTING "Chuyển review/yêu cầu nguồn mới"; prompt mục 17).

## 8. Prompt-injection requirements

Mọi source document là untrusted content (prompt mục 22; Doc B mục 31
bảng lớp "Context": "Delimiter, instruction hierarchy, bỏ instruction
trong document -> Flag injection; human review"). Phải tách
`source_content` khỏi `untrusted_instruction_spans` trước khi vào Agent
context (prompt mục 22). Test bằng PDF/DOCX/TXT/meeting note/customer
upload/policy-lookalike document (prompt mục 22, Scenario 4 mục 41).

## 9. Guardrail requirements

Doc B mục 31 bảng "Guardrail nhiều lớp" (T339) là danh sách 10-lớp cụ
thể nhất, khớp gần như 1-1 với các lớp prompt liệt kê rải rác mục 23-30:
Input, Retrieval, Context, Schema, Claim/Evidence, Domain, Risk, Action,
Output, Monitoring — mỗi lớp có "Fail behavior" riêng (vd Retrieval:
"Insufficient/retrieval error; không che thành no-match"; Risk:
"Fail-closed"). Domain guardrail theo từng Agent (prompt mục 29) khớp với
bảng Doc B mục 30 cột "Không được tự suy đoán" ở mục 2 phía trên.

## 10. Evaluation metrics

Doc B mục 32 bảng "Đánh giá từng Agent và module" (T363) cho metric
CHÍNH + "Failure nghiêm trọng" cho 8 module (Product/Legal/Operations/
Requirement Compiler/Document Assurance/Underwriting Compiler/
Planner-Router/Approval-Action) — cụ thể hơn prompt mục 37's generic
per-agent list. Retrieval-ranking metrics thuần (Recall@k/MRR/nDCG) chỉ
xuất hiện trong prompt mục 36, KHÔNG có trong cả hai doc gốc — đây là
kỹ thuật đánh giá retrieval chuẩn ngành do prompt bổ sung, không phải yêu
cầu nghiệp vụ SHB; vẫn hợp lý để dùng, nhưng cần ghi rõ nguồn khác nhau.

## 11. Hard safety gates

Doc B mục 32.1 bảng "Hard gate pilot" (T372) — **nguồn chính thức nhất**
cho phần này, 9 gate cụ thể:

```text
invalid_evidence_accepted = 0
non_overridable_blocker_cleared = 0
action_without_valid_decision_or_approval = 0
critical_claim_citation_validity = 100% (hoặc claim bị block/insufficient)
cross_customer_leakage = 0
prompt_injection_bypass = 0 (trên adversarial suite)
underwriting_unsupported_critical_claim = 0
critical_route_false_simple = 0
duplicate_side_effect = 0
```

Prompt mục 39 liệt kê 10 gate, gồm thêm `cross_tenant_retrieval = 0`,
`quarantined_source_used = 0`, `superseded_policy_used_as_current = 0`,
`unsupported_official_price_or_limit = 0` — không mâu thuẫn với Doc B,
là phần mở rộng hợp lý (repo hiện chưa có khái niệm multi-tenant thật,
nên `cross_tenant_retrieval` sẽ cần đánh dấu N/A hoặc single-tenant giả
định, không bịa một cơ chế tenant chưa tồn tại).

## 12. Những điểm chưa được xác minh / mâu thuẫn cần quyết định

- **Prompt yêu cầu giữ 3 mode `local/mcp/hybrid`** — đã xác nhận các mode
  này tồn tại thật trong repo (audit riêng, xem
  `docs/RAG_GUARDRAIL_CURRENT_STATE_AUDIT.md`); không phải giả định.
- **`tenant_id`/`branch_id`/`team_id` trong RetrievalRequest (prompt mục
  6)**: repo hiện không có khái niệm multi-tenant tách biệt (chỉ có
  branch/employee scope qua IAM). Sẽ implement `tenant_id` như một field
  optional/hằng-số single-tenant, KHÔNG bịa ra một hệ thống multi-tenant
  không tồn tại.
- **Doc B's Unified Metadata Plane (mục 29, ẩn dụ DeepStream)** là một hệ
  thống lớn hơn phạm vi RAG/Guardrail (bao trùm cả Underwriting Submission
  chưa tồn tại trong repo). Phần RAG/Guardrail chỉ implement đủ metadata
  cần cho Grounding Pack/Citation (mục 3 phía trên), KHÔNG xây toàn bộ
  Unified Metadata Plane — đó là phạm vi của một prompt/nhiệm vụ khác
  (Underwriting Submission handoff), ngoài phạm vi 50-phần RAG/Guardrail
  hiện tại.
- **HyDE, LLM reranker, cross-encoder (prompt mục 9.4, 14)**: cả hai
  document nguồn không nhắc tới các kỹ thuật này — đây là bổ sung riêng
  của prompt 50 phần. Sẽ implement dưới feature flag tắt mặc định đúng
  như prompt mục 9 yêu cầu, không bật ngầm.
- **100-query eval dataset (prompt mục 35)**: không có sẵn trong repo,
  cần build mới; sẽ dùng đúng nguồn customer/product/policy đã có trong
  repo (không bịa dữ liệu), như V3 data pack đã build ở vòng trước
  (`data/synthetic/v3/`).
