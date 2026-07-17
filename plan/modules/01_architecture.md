> Trích từ [`SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md`](../SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md) (dòng 103-272). Đây là bản trích để AI/dev chỉ cần load đúng module đang làm, không cần load toàn bộ 1156 dòng. Xem [`INDEX.md`](../INDEX.md) để biết thứ tự đọc và bản đầy đủ khi cần đối chiếu.

## 10. End-to-End Workflow
`[PROPOSED DESIGN]`

### Sơ đồ 1: End-to-End Workflow
```mermaid
sequenceDiagram
    autonumber
    actor RM as RM / Nhân viên SHB
    participant Workspace as RM Workspace
    participant Router as Complexity Router
    participant Planner as Planner Agent
    participant Specialists as Product/Legal/Ops Agents
    participant Validator as Evidence Validator
    participant CRM as Mock CRM System

    RM->>Workspace: Nhập nhu cầu & tải lên hồ sơ doanh nghiệp
    Workspace->>Router: Gửi case context
    alt Yêu cầu đơn giản
        Router->>Workspace: Trả kết quả tra cứu nhanh (Single-Agent/RAG)
    else Yêu cầu phức tạp
        Router->>Planner: Chuyển tiếp yêu cầu nghiệp vụ
        Planner->>Planner: Phân rã mục tiêu & lập Execution Plan
        loop Thực thi theo kế hoạch
            Planner->>Specialists: Gọi Agent chuyên môn (Song song/Tuần tự)
            Specialists->>Specialists: Tra cứu chính sách & Đối chiếu điều kiện
            Specialists->>Planner: Trả kết quả kèm nguồn trích dẫn (Evidence)
        end
        Planner->>Validator: Gửi toàn bộ kết quả để kiểm tra bằng chứng
        Validator->>Validator: Xác minh Citation & Lọc an toàn (Guardrails)
        Validator->>Workspace: Trả về Báo cáo đề xuất (Decision Brief)
        Workspace->>RM: Hiển thị phương án, checklist thiếu & email nháp
        RM->>Workspace: Duyệt phương án (Approve Action)
        Workspace->>CRM: Gọi Action Executor tạo case & lưu log
        CRM->>RM: Phản hồi kết quả thực thi
    end
```

---

## 11. Logical Architecture
`[PROPOSED DESIGN]`

Hệ thống được tổ chức thành 7 phân lớp logic tách biệt để đảm bảo tính module hóa và bảo mật:

```text
+-------------------------------------------------------------------------------+
|                            USER EXPERIENCE LAYER                              |
|   [RM Workspace]   [Case Detail Page]   [Timeline Trace]   [Approval Panel]   |
+-------------------------------------------------------------------------------+
                                      ↓ ↑
+-------------------------------------------------------------------------------+
|                            API APPLICATION LAYER                              |
|        [Case API]        [Document API]        [Workflow API]                 |
+-------------------------------------------------------------------------------+
                                      ↓ ↑
+-------------------------------------------------------------------------------+
|                          AGENT ORCHESTRATION LAYER                            |
|  [Complexity Router] -> [Planner Agent] -> [Product / Legal / Ops Agents]    |
|                                                     ↓                         |
|                         [Evidence Validator] & [Guardrail Gate]               |
+-------------------------------------------------------------------------------+
                                      ↓ ↑
+-------------------------------------------------------------------------------+
|                                 TOOL LAYER                                    |
|   [search_product_catalog]   [validate_business_reg]   [create_case_in_crm]   |
+-------------------------------------------------------------------------------+
                                      ↓ ↑
+-------------------------------------------------------------------------------+
|                                KNOWLEDGE LAYER                                |
|   [Product catalog KB]    [Compliance policy KB]    [SOP & Template KB]       |
+-------------------------------------------------------------------------------+
                                      ↓ ↑
+-------------------------------------------------------------------------------+
|                            STATE & STORAGE LAYER                              |
|     [Shared Case State]      [Relational DB]       [Vector DB (Chroma)]       |
+-------------------------------------------------------------------------------+
                                      ↓ ↑
+-------------------------------------------------------------------------------+
|                          SECURITY & GOVERNANCE LAYER                          |
|         [RBAC Gate]         [PII Masker]         [Immutable Audit Log]        |
+-------------------------------------------------------------------------------+
```

---

## 12. Runtime Architecture
`[PROPOSED DESIGN]`

### Sơ đồ 2: Agent Orchestration Graph (LangGraph)
Đồ thị biểu diễn luồng điều phối động, quản lý vòng lặp khi thiếu thông tin:

```mermaid
graph TD
    Start([Bắt đầu Case]) --> Router{Complexity Router}
    Router -- Simple --> RAG[Single Agent RAG]
    Router -- Complex --> Plan[Planner Agent: Lập Execution Plan]
    
    Plan --> ProductNode[Product Node: Tìm giải pháp & Bundle]
    Plan --> LegalNode[Legal Node: Thẩm định KYC/UBO/Hiệu lực]
    
    ProductNode --> MergeState[Hợp nhất Shared State]
    LegalNode --> MergeState
    
    MergeState --> ValidateNode{Evidence Validator}
    
    ValidateNode -- Claim không hợp lệ --> FailNode[Đánh dấu Lỗi & Báo Planner]
    FailNode --> Plan
    
    ValidateNode -- Claim hợp lệ --> GuardrailNode{Risk & Guardrail Gate}
    
    GuardrailNode -- Thiếu thông tin quan trọng --> OpsPending[Ops Node: Soạn Checklist thiếu & Email nháp]
    OpsPending --> StatePending[Cập nhật trạng thái pending_information]
    StatePending --> RMReviewPending[RM Workspace: RM Duyệt gửi yêu cầu bổ sung]
    RMReviewPending --> StopPending([Dừng chờ RM nhập bổ sơ])
    
    GuardrailNode -- Đầy đủ & An toàn --> OpsComplete[Ops Node: Tạo Case CRM nháp & Báo cáo đề xuất]
    OpsComplete --> StateComplete[Cập nhật trạng thái pending_approval]
    StateComplete --> RMReviewComplete[RM Workspace: RM Duyệt mở dịch vụ]
    RMReviewComplete --> ExecNode[Action Executor: Gọi APIs tạo case/task thật]
    ExecNode --> Completed([Hoàn thành Case])
```

---

## 13. Data Architecture
`[PROPOSED DESIGN]`

### Sơ đồ 3: Data Flow Diagram
Biểu diễn đường đi của dữ liệu từ khi RM nhập vào cho đến khi lưu trữ và hậu kiểm:

```mermaid
flowchart TD
    RawInput[RM Input: Văn bản & Hồ sơ doanh nghiệp] -->|1. Upload| Ingest[Input Validator]
    Ingest -->|2. Masking PII| Masker[PII Masker]
    Masker -->|3. Trích xuất text| TextExtractor[Text Extractor]
    
    TextExtractor -->|4. Lưu trữ| DocStore[(Storage: Files & Metadata)]
    TextExtractor -->|5. Ghi nhận| StateDB[(Shared Case State)]
    
    StateDB -->|6. Đọc context| Planner[Planner Agent]
    
    subgraph Knowledge Retrieval
        ProductRAG[(Vector Store: Product Catalog)]
        LegalRAG[(Vector Store: Compliance & Regulatory)]
    end
    
    Planner -->|7. Query RAG| ProductRAG
    Planner -->|8. Query RAG| LegalRAG
    
    ProductRAG -->|9. Context| StateDB
    LegalRAG -->|10. Context| StateDB
    
    StateDB -->|11. Đọc kết quả đề xuất| Validator[Evidence Validator]
    DocStore -->|12. Trích dẫn đối chứng| Validator
    
    Validator -->|13. Đánh giá nguồn| AuditDB[(Immutable Audit Event Store)]
```

---

## 14. Security Architecture
`[PROPOSED DESIGN]`

### Ranh giới Tin cậy (Trust Boundaries)
*   **User Space Boundary:** Giao diện RM Workspace chạy trên thiết bị đầu cuối của nhân viên SHB. Xác thực thông qua Single Sign-On (SSO).
*   **Application Boundary:** FastAPI App triển khai trên máy chủ nội bộ của SHB. Mọi kết nối ra ngoài (như gọi API LLM) đều phải đi qua Model Gateway bảo mật.
*   **System Integration Boundary:** Kết nối giữa Action Executor và hệ thống CRM/Core Banking mô phỏng. Bắt buộc sử dụng token phê duyệt tạm thời (`Approval Token`) được sinh ra sau khi RM nhấn nút duyệt.

---

