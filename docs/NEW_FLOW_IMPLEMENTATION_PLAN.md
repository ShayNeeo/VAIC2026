# Kế hoạch triển khai: SHB Corporate Sales Copilot End-to-End Workflow (Phase 1-10)

Bản thiết kế này phản ánh kế hoạch triển khai dựa trên Word document `SHB_Corporate_Sales_Copilot_End_to_End_Evidence_Underwriting_AI_Assurance.docx`.

## Tóm tắt Mục tiêu
Cải tổ luồng xử lý hiện tại để bao gồm nhận diện khách hàng (Customer Resolver), trích xuất Evidence từ Metadata (Unified Metadata Plane), tích hợp Document Assurance, sinh Checklist (Requirement Compiler) và hỗ trợ Submission Readiness cho RM duyệt hồ sơ trước khi chuyển qua Underwriting.

## Các giai đoạn triển khai (Phases 1-10)

### Phase 1: Unified Metadata Plane Foundation
*Xây dựng cấu trúc dữ liệu Metadata chung cho toàn bộ hệ thống.*
- Tạo `app/schemas/v2/metadata.py` với các models: `MetadataObject`, `MetadataVersion`, `MetadataRelation`, `MetadataEvent`.
- Cập nhật `V2Repository` để lưu trữ và truy xuất metadata.
- **[NEW]** `app/schemas/v2/metadata.py`
- **[MODIFY]** `app/storage/repository.py`

### Phase 2: Customer Resolver & Existing Evidence Inventory
*Phân loại khách hàng hiện hữu và khách hàng mới, tái sử dụng dữ liệu.*
- Tạo `CustomerResolver` để load evidence inventory.
- Tái cấu trúc `CustomerBusinessSnapshot` thành metadata.
- Cập nhật luồng `intake` để chạy qua Resolver trước.
- **[NEW]** `app/context/customer_resolver.py`
- **[MODIFY]** `app/intake/service.py`

### Phase 3: Agent Output Contract & Requirement Compiler
*Đồng bộ schema output của Product, Legal, Operations và gộp Checklist.*
- Cập nhật output của `ProductService`, `EligibilityEngine`, `OperationsService` để tuân thủ schema chuẩn: `agent_run_id`, `facts_used`, `requirements`, `citations`.
- Tạo `RequirementCompiler` để gộp yêu cầu thành `CaseChecklist`.
- **[NEW]** `app/workflow/requirement_compiler.py`
- **[MODIFY]** `app/product/service.py`, `app/eligibility/engine.py`, `app/operations/service.py`

### Phase 4: Customer Evidence Collection
*Thu thập hồ sơ bổ sung từ khách hàng, sinh Customer Request Package.*
- Cập nhật endpoint để lấy Checklist state.
- Hỗ trợ lưu trữ evidence nộp lên.

### Phase 5: Document Assurance
*Thẩm định tài liệu đa lớp (Classification, Authenticity, Signatures).*
- Xây dựng `DocumentAssurancePipeline`.
- Cập nhật ingestion flow để scan tài liệu trước khi thành Evidence.
- **[NEW]** `app/intake/document_assurance.py`

### Phase 6: Controlled Retrieval Plane
*Kiểm soát grounding, không hallucinate.*
- Tạo `GroundingPack` cho mỗi Agent.
- Cập nhật `RAGProvider` (hoặc dùng `rag_mcp`) để bắt buộc lấy từ source an toàn.
- **[MODIFY]** `app/knowledge/rag_provider.py`

### Phase 7: Guardrail nhiều lớp
*Cập nhật Risk Guardrail.*
- Cải tiến `RiskGuardrailGate` để block các missing info, signature conflict, non-overridable blockers.
- **[MODIFY]** `app/workflow/risk_gate.py`

### Phase 8: Submission Readiness & RM Approval
*Đóng băng Submission trước khi gửi thẩm định.*
- Tạo state `SUBMISSION_FROZEN`.
- Tính toán hash (immutable snapshot) cho package hồ sơ.
- Đảm bảo RM chỉ duyệt (không phải phê duyệt tín dụng) gói tài liệu.
- **[NEW]** `app/approval/submission_readiness.py`
- **[MODIFY]** `app/approval/service.py`

### Phase 9: Underwriting Submission và Workspace Backend
*Cấu trúc gói hồ sơ gửi Thẩm định và Xử lý Decision.*
- Khởi tạo Underwriting queue, Information Requests, Underwriting Decision models.
- Liên kết với `ActionExecutorV2`.
- **[NEW]** `app/schemas/v2/underwriting.py`

### Phase 10: API
*Mở rộng các endpoints.*
- Bổ sung các API vào `app/api/v2/router.py`: `GET /submission-readiness`, `POST /submissions/prepare`, `GET /submissions/{id}/preview`, `POST /submissions/{id}/approve`, v.v.
- **[MODIFY]** `app/api/v2/router.py`

## Kế hoạch Kiểm chứng
### Automated Tests
- Cập nhật test case `test_v2_specialist_review.py` hiện đang lỗi (fix baseline).
- Thêm unit tests cho MetadataEnvelope, CustomerResolver, RequirementCompiler, DocumentAssurance.
- Đảm bảo E2E tests bao gồm flow SUBMISSION_FROZEN.

### Manual Verification
- Test UI mock (RM Workspace / Underwriting Workspace) tích hợp với API mới.

---
Về P0: `CONTEXT_CORRECTION_POLICIES` bug đã được khắc phục trong repository (`app/workflow/impact.py`). Test suite `test_v2_context_correction_policy.py` đã bao phủ trường hợp này. Không cần implement lại, chỉ đảm bảo tương thích với flow mới.
