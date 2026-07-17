> Trích từ [`SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md`](../SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md) (dòng 904-959). Đây là bản trích để AI/dev chỉ cần load đúng module đang làm, không cần load toàn bộ 1156 dòng. Xem [`INDEX.md`](../INDEX.md) để biết thứ tự đọc và bản đầy đủ khi cần đối chiếu.

## 35. Development Backlog
`[PROPOSED DESIGN]`

Bảng kế hoạch chi tiết các đầu việc kỹ thuật phục vụ quá trình phát triển dự án:

| ID | Epic | User Story | Technical Task | Agent/Module | Priority | Dependency | Owner Role | Acceptance Criteria | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TSK-001** | Foundation | RM tạo Case mới | Định nghĩa Shared Case State schema | Shared State | High | None | Orchestration Engineer | JSON Schema chứa đủ các trường case_id, evidences, approval_status. | `To Do` |
| **TSK-002** | Knowledge | Tra cứu chính sách | Xây dựng RAG pipeline cho tài liệu sản phẩm | Product RAG | High | None | Data Engineer | Truy xuất đúng chính sách sản phẩm theo metadata filter phân khúc doanh nghiệp. | `To Do` |
| **TSK-003** | Ingestion | Đọc tài liệu | Viết parser trích xuất thông tin ĐKKD | Input Validator | Medium | None | Backend Engineer | Trích xuất chính xác MST, Tên doanh nghiệp, Người đại diện từ PDF. | `To Do` |
| **TSK-004** | Agent | Phân rã mục tiêu | Viết Prompt và logic lập kế hoạch cho Planner | Planner Agent | High | TSK-001 | Orchestration Engineer | Planner phân tách đúng yêu cầu ABC thành 3 task của Product, Legal, Ops. | `To Do` |
| **TSK-005** | Agent | Tư vấn giải pháp | Phát triển Product Agent matching sản phẩm | Product Agent | High | TSK-002 | Data Engineer | Đề xuất đúng gói Payroll cho doanh nghiệp có >10 nhân viên. | `To Do` |
| **TSK-006** | Agent | Thẩm định KYC | Phát triển Legal Agent kiểm tra UBO/KYC | Legal Agent | High | TSK-004 | Security Engineer | Phát hiện lỗi và chặn quy trình khi hồ sơ thiếu thông tin UBO. | `To Do` |
| **TSK-007** | Safety | Kiểm soát bằng chứng | Xây dựng công cụ so khớp trích dẫn nguồn | Evidence Validator | High | TSK-005 | Security Engineer | Chặn đứng 100% các claim của Agent không có quote trùng khớp trong văn bản gốc. | `To Do` |
| **TSK-008** | Ingestion | Phân loại luồng | Phát triển Complexity Router | Router | Medium | TSK-004 | Orchestration Engineer | Định tuyến đúng 100% câu hỏi tra cứu đơn giản sang RAG đơn lẻ. | `To Do` |
| **TSK-009** | Action | Kết nối CRM | Phát triển Mock APIs CRM/Task/Email | Tool Registry | Medium | None | Backend Engineer | CRM nhận được payload và tạo case trạng thái pending sau khi RM duyệt. | `To Do` |
| **TSK-010** | UI | Workspace | Xây dựng màn hình RM Workspace và Trace UI | Frontend | Medium | TSK-009 | Frontend Engineer | Hiển thị trực quan Thought Trace của Agent và nút bấm Approve/Reject. | `To Do` |

---

## 36. 48-Hour Plan
`[PROPOSED DESIGN]`

Lộ trình triển khai nước rút 48 giờ tại Hackathon:

*   **0 – 4h (Thiết kế & Khởi tạo):** Thống nhất Shared State JSON schema; Khởi tạo khung mã nguồn FastAPI và cấu hình LangGraph; Thiết lập bộ dữ liệu giả lập (`SYNTHETIC DEMO DATA`) gồm 5 hồ sơ doanh nghiệp và 10 tài liệu sản phẩm mẫu.
*   **4 – 12h (Xây dựng Knowledge & RAG):** Tạo cơ sở dữ liệu Vector (ChromaDB In-Memory) lưu trữ các tài liệu chính sách; Viết pipeline trích xuất văn bản và metadata.
*   **12 – 24h (Xây dựng Agents Core):** Hoàn thiện prompt và logic cho Planner Agent, Product Agent, và Legal Agent; Tích hợp các agent node vào đồ thị LangGraph.
*   **24 – 32h (Kiểm soát & Actions):** Viết logic cho Evidence Validator đối chiếu quote; Xây dựng Operations Agent soạn email nháp và checklist; Thiết lập Mock APIs cho CRM và Email.
*   **32 – 40h (Frontend & Dashboard):** Thiết kế giao diện RM Workspace (hiển thị timeline suy luận, bảng so khớp bằng chứng, email nháp và nút Approval).
*   **40 – 44h (Kiểm thử & Đánh giá):** Chạy toàn bộ 40 test cases trong Golden Dataset; Đo lường tỷ lệ ảo giác và ghi nhận kết quả so sánh với Single-Agent baseline.
*   **44 – 48h (Đóng gói & Thuyết trình):** Cấu hình môi trường docker-compose; Viết README và AI collaboration log; Tập dượt demo kịch bản end-to-end (Wow moment).

---

## 37. Pilot Plan
`[PROPOSED DESIGN]`

Kế hoạch triển khai thử nghiệm diện hẹp (Pilot) trong vòng 3 tháng:
*   **Tháng 1 (Chuẩn bị & Sandbox):** Phối hợp với SHB để thu thập dữ liệu thật về danh mục sản phẩm và quy chế KYC (`<SHB_PRODUCT_CATALOG_DATA_REQUIRED>`, v.v.). Tiến hành làm sạch, chunking và lưu trữ vào Vector DB nội bộ. Thiết lập môi trường thử nghiệm bảo mật (Sandbox).
*   **Tháng 2 (Thử nghiệm nội bộ):** Triển khai hệ thống cho nhóm nhỏ từ 5 - 10 RM dùng thử trên các case thật. Ghi nhận phản hồi nghiệp vụ và đo lường Tỷ lệ RM chỉnh sửa email nháp (Email Edit Rate).
*   **Tháng 3 (Đánh giá & Tối ưu):** Tinh chỉnh prompt của các Agent dựa trên dữ liệu logs thực tế; Đánh giá hiệu quả giảm thời gian xử lý hồ sơ của RM trước khi quyết định mở rộng toàn hệ thống.

---

## 38. Production Readiness
`[PROPOSED DESIGN]`

Để hệ thống sẵn sàng đưa vào vận hành chính thức (Production), các tiêu chuẩn sau phải được đáp ứng:
1.  **Chất lượng RAG:** Retrieval hit rate đạt tối thiểu 95% trên tập dữ liệu chính sách thật của ngân hàng.
2.  **Độ chính xác thẩm định:** Tỷ lệ bỏ sót lỗi pháp lý (KYC/AML) của Legal Agent bằng 0%.
3.  **Tích hợp hệ thống:** Thay thế hoàn toàn các Mock APIs bằng các API thật có xác thực bảo mật của CRM và Core Banking của SHB.
4.  **Bảo mật:** Đạt chứng nhận an toàn thông tin nội bộ của SHB, bảo vệ thành công trước các cuộc tấn công prompt injection và rò rỉ PII.

---

