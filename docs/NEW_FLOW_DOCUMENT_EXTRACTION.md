# Document Extraction: SHB Corporate Sales Copilot End-to-End Evidence Underwriting AI Assurance

## Mục lục thực tế của tài liệu
1. Những gì được giữ nguyên và những gì được bổ sung
2. Mô hình hai chiều
3. Flow tổng thể sau cải tiến
4. Bước 0 — Customer Resolver và Case Initializer
5. Flow A — Khách hàng hiện hữu tại SHB
6. Flow B — Khách hàng mới
7. Cách ba Expert Agent tạo thông tin và checklist
8. Evidence inventory và logic tái sử dụng
9. Checklist và trạng thái xử lý
10. Document Assurance Pipeline
11. Chữ ký số, chữ ký bản giấy và OTP
12. RM Workspace sau cải tiến
13. Customer Request Package
14. Vòng cập nhật ngược về ba Expert Agent
15. Metadata và biểu diễn dữ liệu end-to-end
16. Ví dụ 1 — Khách hàng hiện hữu yêu cầu vốn lưu động
17. Ví dụ 2 — Khách hàng mới cần payroll và cash management
18. State model ở mức case readiness
19. API và service boundary đề xuất
20. Acceptance criteria nghiệp vụ
21. Lộ trình triển khai
22. Intent chuẩn để AI triển khai
23. Kết luận
24. Flow tổng thể hoàn chỉnh sau cải tiến
25. Submission Readiness trước khi RM được bấm duyệt
26. Ý nghĩa của thao tác RM duyệt khách hàng
27. Handoff sang bộ phận thẩm định
28. Gói thông tin gửi thẩm định
29. Unified Metadata Plane từ đầu đến cuối
30. Retrieval architecture để hạn chế hallucination
31. Guardrail nhiều lớp
32. Đánh giá từng Agent và module
33. Submission state machine
34. API và database bổ sung
35. Acceptance criteria end-to-end
36. Intent chuẩn để AI triển khai
37. Flow kết luận

## Danh sách business requirements
- Bổ sung lớp nhận diện khách hàng, tái sử dụng dữ liệu/hồ sơ đã có trước khi chạy Agent.
- Sinh checklist động, đối chiếu với evidence inventory. Chỉ yêu cầu khách hàng bổ sung phần thiếu, hết hạn, mâu thuẫn.
- Customer Resolver quyết định EXISTING_CONFIRMED, EXISTING_POSSIBLE_MATCH, NEW_CUSTOMER, ACCESS_DENIED, DUPLICATE_SUSPECTED.
- RM nhìn thấy Evidence Checklist với trạng thái (SATISFIED_VERIFIED, MISSING, REFRESH_REQUIRED,...).
- Khách hàng mới có thể nhận Exploratory hoặc Conditional Recommendation mà không cần nộp đủ hồ sơ ngay từ đầu.
- Requirement Compiler gộp requirement từ Product, Legal, Operations thành một checklist duy nhất.
- Yêu cầu lại hồ sơ phải có reason code, giải thích rõ, ví dụ "thiếu trang chữ ký".
- Customer Request Package chỉ gửi yêu cầu thiếu, không hiển thị fraud score hay rule nội bộ cho khách hàng.
- Nút "Duyệt khách hàng để gửi thẩm định" chỉ xác nhận gói hồ sơ hợp lệ (không phải phê duyệt tín dụng).
- Handoff sang Underwriting với Executive, Product, Legal/Policy, Operations, Evidence, Source, Lineage, Diff, Audit Views.
- Underwriter không tự execute action, có thể issue Information Request hoặc Quyết định (APPROVED, CONDITIONALLY_APPROVED, REJECTED).

## Danh sách technical requirements
- Mọi file/hồ sơ nộp phải đi qua Document Assurance Pipeline (File security, readability, classification, completeness, validity, consistency, authenticity, signature).
- Authenticity risk chỉ sinh signal, không dùng 1 model quyết định tài liệu giả tuyệt đối.
- Evidence/Document cập nhật tạo version mới, Snapshot version mới.
- Chỉ chạy lại Agent/node bị ảnh hưởng (Impact Analyzer) thay vì chạy lại toàn bộ quy trình.
- Metadata end-to-end: ID, type, schema, version, trace_id, hashes (content_hash, previous_hash). Mọi thay đổi không đè payload cũ.
- Retrieval Plane riêng cho mỗi Agent, có Grounding Pack (source, version, page, quote, authority). LLM không tự lấy context từ memory.
- Agent Output trả JSON schema chuẩn (`agent_run_id`, `facts_used`, `recommendations`, `requirements`, `citations`, `confidence`).
- Dùng Grounding với Source Tiers (1-5), không được fallback vào hallucination nếu không tìm thấy sources.

## Danh sách metadata types
- `evidence_requirement`
- `case_checklist_item`
- `raw_artifact`
- `document`
- `extracted_fact`
- `document_assessment`
- `authenticity_signal`
- `signature_request` / `otp_verification`
- `evidence`
- `customer_snapshot`
- `agent_run` / `decision` / `approval` / `action`
- `submission_readiness_assessment`
- `rm_submission_approval`
- `underwriting_submission`
- `submission_section`
- `source_manifest`
- `underwriting_assignment`
- `underwriting_review`
- `underwriting_information_request`
- `underwriting_decision`
- `decision_condition`
- `submission_diff`
- `review_access_event`

## Danh sách state machines
- **Case Readiness / Checklist State:** REQUIRED/REQUESTED, RECEIVED/PROCESSING, UNREADABLE/WRONG_TYPE/MALWARE, INCOMPLETE/INCONSISTENT/EXPIRED, AUTHENTICITY_SUSPECTED, MANUAL_REVIEW, VERIFIED, REJECTED/WAIVED/SUPERSEDED/NOT_APPLICABLE.
- **Underwriting Submission State Machine:** 
  DRAFT → READY_FOR_RM_REVIEW → RM_APPROVED → SUBMISSION_FROZEN → SENT_TO_UNDERWRITING → UNDER_REVIEW → INFORMATION_REQUESTED → RESUBMISSION_READY → RESUBMITTED → UNDER_REVIEW → APPROVED | CONDITIONALLY_APPROVED | REJECTED | WITHDRAWN

## Danh sách API được đề xuất
- `POST /api/v2/customers/resolve`
- `GET /api/v2/customers/{customer_id}/evidence-inventory`
- `GET /api/v2/cases/{case_id}/workspace`
- `GET /api/v2/cases/{case_id}/checklist`
- `POST /api/v2/cases/{case_id}/customer-requests`
- `GET /api/v2/customer-requests/{request_id}`
- `GET /api/v2/cases/{case_id}/submission-readiness`
- `POST /api/v2/cases/{case_id}/submissions/prepare`
- `GET /api/v2/cases/{case_id}/submissions/{submission_id}/preview`
- `POST /api/v2/cases/{case_id}/submissions/{submission_id}/approve`
- `POST /api/v2/submissions/{submission_id}/send`
- `GET /api/v2/underwriting/queue`
- `GET /api/v2/underwriting/submissions/{submission_id}`
- `GET /api/v2/underwriting/submissions/{submission_id}/lineage`
- `GET /api/v2/underwriting/submissions/{submission_id}/diff`
- `POST /api/v2/underwriting/submissions/{submission_id}/assign`
- `POST /api/v2/underwriting/submissions/{submission_id}/information-requests`
- `POST /api/v2/underwriting/submissions/{submission_id}/reviews`
- `POST /api/v2/underwriting/submissions/{submission_id}/decision`
- `GET /api/v2/metadata/{meta_id}`
- `GET /api/v2/metadata/{meta_id}/versions`
- `GET /api/v2/metadata/{meta_id}/lineage`
- `GET /api/v2/cases/{case_id}/timeline`

## Danh sách database tables
- `metadata_objects`, `metadata_versions`, `metadata_relations`, `metadata_events`, `metadata_access_logs`
- `evidence_requirements`, `case_checklist_items`, `customer_document_requests`, `customer_document_request_events`, `artifact_uploads`, `document_processing_runs`, `document_assessments`, `authenticity_signals`, `signature_requests`, `signature_events`, `otp_challenges`, `otp_verifications`, `evidence_records`
- `underwriting_submissions`, `underwriting_submission_versions`, `underwriting_submission_sections`, `underwriting_submission_evidence_links`, `underwriting_assignments`, `underwriting_reviews`, `underwriting_information_requests`, `underwriting_decisions`, `underwriting_decision_conditions`, `underwriting_access_logs`
- `guardrail_events`, `agent_evaluation_runs`

## Danh sách guardrail
- **Input Guardrail:** Auth, role, scope, prompt injection, PII, file safety.
- **Retrieval Guardrail:** Source allowlist, version/freshness, tenant, conflict. Không fallback vào memory.
- **Context Guardrail:** Delimiter, instructions hierarchy, detect prompt injection trong văn bản tải lên.
- **Schema Guardrail:** Pydantic/JSON schema, enum validation, required refs.
- **Claim/Evidence Guardrail:** Claim có source, quote tồn tại, invalid claim block.
- **Domain Guardrail:** Hạn chế quyền Agent (không tự ý approve, không giả lập fee/limit, Legal không tự suy diễn UBO, Ops không tự đánh dấu ready).
- **Risk Guardrail:** Absolute blocker, high-risk authenticity, conflict → Fail-closed.
- **Action Guardrail:** Approval hash, SoD (Separation of duties), version, idempotency. Không duplicate side effect.
- **Output Guardrail:** Lọc lộ PII, wording calibrated, luôn display citations.

## Danh sách evaluation metrics
- **Product Agent:** product_precision, recall, bundle_completeness, need_product_fit, evidence_coverage, unsupported_product_claim_rate, missing_data_detection.
- **Legal Agent:** rule_accuracy, missing_info_recall, blocker_recall, false_clear_rate, policy_citation_validity, non_overridable_detection, conflict_detection.
- **Operations Agent:** process_step_completeness, dependency_accuracy, checklist_recall, readiness_accuracy, action_validity, owner_accuracy.
- **Requirement Compiler:** requirement_precision, requirement_recall, deduplication_accuracy, policy_mapping_accuracy, evidence_reuse_accuracy, false_re_request_rate.
- **Document Assurance:** classification_f1, field_extraction_f1, provenance_coverage, completeness_recall, conflict_recall, freshness/signature_accuracy.
- **Underwriting Compiler:** section_completeness, source_coverage, summary_faithfulness, unsupported_claim_rate, contradiction_rate, diff_accuracy, source_manifest_completeness.
- **Planner/Router:** routing_accuracy, false_simple_rate, unnecessary_multi_agent_rate, dependency_order_accuracy.

## Các phần cần làm MVP, pilot và production
**Các Phase thực hiện MVP/Pilot theo thứ tự:**
- **Phase 1:** Unified Metadata Plane Foundation
- **Phase 2:** Customer Resolver & Existing Evidence Inventory
- **Phase 3:** Agent Output Contract & Requirement Compiler
- **Phase 4:** Customer Evidence Collection
- **Phase 5:** Document Assurance
- **Phase 6:** Controlled Retrieval Plane
- **Phase 7:** Guardrail nhiều lớp
- **Phase 8:** Submission Readiness & RM Approval
- **Phase 9:** Underwriting Submission và Workspace Backend
- **Phase 10:** API

## Những điểm chưa rõ hoặc chưa thể xác minh
- Việc kết nối Authentication/SSO cho các tenant, team cụ thể có sẵn framework hay cần thiết lập từ đầu?
- External integration cho Signature provider, Fraud check, OTP provider, OCR services hiện có interface nào không hay đều phải tạo mock provider cho MVP?
- Cơ chế lưu trữ file (Object storage) có sẵn MinIO/S3 không, hay chỉ lưu local disk?
- DB Schema cho Metadata có chấp nhận dùng SQLite cho MVP theo yêu cầu không hay bắt buộc dùng Postgres?
