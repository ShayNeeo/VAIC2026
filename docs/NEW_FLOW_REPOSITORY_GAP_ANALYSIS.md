# Repository Gap Analysis: SHB Corporate Sales Copilot End-to-End Workflow

| Requirement từ Word | Code hiện tại | Trạng thái | Gap | File liên quan | Kế hoạch |
| ------------------- | ------------- | ---------- | --- | -------------- | -------- |
| V2WorkflowEngine | `V2WorkflowEngine` (app/workflow/engine.py) | IMPLEMENTED | Không có gap về cơ bản, nhưng cần cập nhật flow để lấy từ CustomerResolver thay vì direct intake | `app/workflow/engine.py` | Sẽ cập nhật để hỗ trợ flow mới. |
| V2Repository | `V2Repository` (app/storage/repository.py) | IMPLEMENTED | Cần mở rộng cho Metadata Envelope | `app/storage/repository.py` | Phase 1 sẽ mở rộng lưu trữ metadata. |
| SharedCaseState | `SharedCaseState` | IMPLEMENTED | Thiếu fields mới như `customer_snapshot_ref`, `submission_draft_ref` | `app/schemas/v2/shared_case_state.py` | Cập nhật theo Phase 2 & 8. |
| CustomerBusinessSnapshot | `CustomerBusinessSnapshot` | IMPLEMENTED_BUT_BROKEN | Đang dùng như dict đơn giản, thiếu metadata envelope | `app/schemas/v2/shared_case_state.py` | Sẽ được định nghĩa lại bằng Metadata Object (Phase 1, 2). |
| EmployeeContextSnapshot | `EmployeeContextSnapshot` | IMPLEMENTED_BUT_BROKEN | Đang dùng dict | `app/schemas/v2/shared_case_state.py` | Sẽ được định nghĩa bằng Metadata Object. |
| Evidence | `Evidence` (app/schemas/v2/shared_case_state.py) | IMPLEMENTED | Thiếu versioning, metadata refs, validity span | `app/schemas/v2/shared_case_state.py` | Tái cấu trúc thành Metadata Evidence (Phase 1, 2). |
| RiskGuardrailGate | `RiskGuardrailGate` (app/workflow/risk_gate.py) | IMPLEMENTED | Phân tách risk logic ổn nhưng thiếu hard safety block theo Metadata | `app/workflow/risk_gate.py` | Nâng cấp theo Phase 7 (Guardrail). |
| ApprovalServiceV2 | `ApprovalServiceV2` (app/approval/service.py) | IMPLEMENTED | Chưa có khái niệm RMSubmissionApproval với immutable snapshot hash | `app/approval/service.py` | Cập nhật Phase 8 (Submission Readiness). |
| ActionExecutorV2 | `ActionExecutorV2` | IMPLEMENTED | Cần ràng buộc chặt chẽ với UnderwritingDecision | `app/actions/executor.py` | Cập nhật theo Phase 9. |
| IntakeService | `IntakeService` | IMPLEMENTED | Không có CustomerResolver logic (chỉ intake data thuần) | `app/intake/service.py` | Thay thế bằng/tích hợp với CustomerResolver. |
| ProductService | `ProductService` | IMPLEMENTED | Output chưa theo schema chuẩn có `agent_run_id`, `requirements` | `app/product/service.py` | Nâng cấp output Phase 3. |
| EligibilityEngine / Legal | `EligibilityEngine` | IMPLEMENTED | Tương tự ProductService, thiếu requirement compiler output | `app/eligibility/engine.py`, `app/legal/*` | Nâng cấp output Phase 3. |
| OperationsService | `OperationsService` | IMPLEMENTED | Tương tự ProductService, thiếu requirement compiler output | `app/operations/service.py` | Nâng cấp output Phase 3. |
| specialist_reviews | `specialist_reviews` endpoint / db logic | IMPLEMENTED | Review manual vẫn đang hoạt động | `app/api/v2/router.py`, `app/storage/employee_db.py` | Không phá vỡ, giữ nguyên tương thích. |
| OperationalReadinessChecklist | `OperationalReadinessChecklist` | IMPLEMENTED | Chỉ áp dụng cho operations, chưa hợp nhất với Evidence Checklist chung | `app/api/v2/router.py` | Kết hợp với Requirement Compiler (Phase 3). |
| human_review_allowed | `human_review_allowed` flag trong Evidence | IMPLEMENTED | Đã có và hoạt động tốt để gỡ risk | `app/schemas/v2/shared_case_state.py` | Giữ nguyên. |
| expected_case_version / snapshot_hash / content_hash | Versioning & Hashing cơ bản | PARTIALLY_IMPLEMENTED | Có cơ chế optimistic locking nhưng thiếu Unified Metadata Plane | `app/schemas/v2/*`, `app/storage/*` | Xây dựng MetadataEnvelope & Hashing (Phase 1). |
| source_document_id / source_text_span / Grounding / citation | RAG / Grounding | PARTIALLY_IMPLEMENTED | RAGProvider hỗ trợ trả refs, nhưng thiếu Grounding Pack tier và Validation | `app/knowledge/*` | Nâng cấp Controlled Retrieval (Phase 6). |
| impacted_nodes / correct_context | Impact analysis (bug P0) | IMPLEMENTED | Đã sửa: sử dụng chung `CONTEXT_CORRECTION_POLICIES` | `app/workflow/impact.py` | Bug P0 đã được fix, chỉ cần thêm test hồi quy nếu thiếu. |
| CustomerResolver / EvidenceInventoryService | Resolvers | NOT_IMPLEMENTED | Chưa có logic tái sử dụng hồ sơ hay resolve khách hàng hiện hữu | `app/context/*` (dự kiến) | Phase 2. |
| RequirementCompiler | Gộp checklist | NOT_IMPLEMENTED | Chưa có service compiler | `app/workflow/*` (dự kiến) | Phase 3. |
| DocumentAssurance | Thẩm định tài liệu đa lớp | NOT_IMPLEMENTED | Chưa có pipeline assurance | `app/intake/*` (dự kiến) | Phase 5. |
| SubmissionReadiness / Underwriting Submission | Hand-off thẩm định | NOT_IMPLEMENTED | Chưa có package hash và submission draft | `app/approval/*` (dự kiến) | Phase 8 & 9. |
| MetadataEnvelope / MetadataAccessService | Unified Metadata | NOT_IMPLEMENTED | Chưa có | `app/schemas/v2/metadata.py` (dự kiến) | Phase 1. |
