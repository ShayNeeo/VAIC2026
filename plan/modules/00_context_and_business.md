> Trích từ [`SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md`](../SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md) (dòng 1-102). Đây là bản trích để AI/dev chỉ cần load đúng module đang làm, không cần load toàn bộ 1156 dòng. Xem [`INDEX.md`](../INDEX.md) để biết thứ tự đọc và bản đầy đủ khi cần đối chiếu.

# KẾ HOẠCH TRIỂN KHAI CHI TIẾT: SHB CORPORATE EXPERT WORKSPACE

---

## 1. Executive Summary
`[PROPOSED DESIGN]`
**SHB Corporate Expert Workspace** là hệ thống Multi-Agent nội bộ được thiết kế đặc biệt nhằm hỗ trợ đội ngũ RM (Relationship Manager) và nhân viên nghiệp vụ của SHB trong việc xử lý, phân tích các yêu cầu phức tạp từ khách hàng doanh nghiệp. Bằng cách số hóa tri thức đa phòng ban bao gồm Sản phẩm, Pháp lý & Tuân thủ, và Vận hành, hệ thống hoạt động như một "đội chuyên gia số" đứng sau mỗi RM, giúp nâng cao năng suất xử lý hồ sơ, rút ngắn thời gian phản hồi doanh nghiệp, và đảm bảo mọi đề xuất hành động đều được kiểm duyệt chặt chẽ dựa trên bằng chứng xác thực (`Evidence`) và có sự phê duyệt trực tiếp của con người (`Human-in-the-Loop`).

---

## 2. Scope and Non-Scope
`[PROPOSED DESIGN]`

### 2.1 Scope (Phạm vi)
*   Xây dựng hệ thống Multi-Agent nội bộ sử dụng khung LangGraph để điều phối: Planner Agent, Product Agent, Legal & Compliance Agent, và Operations Agent.
*   Cơ chế xác thực bằng chứng `Evidence Validator` đối chiếu các claim của LLM với văn bản chính sách gốc.
*   Lớp kiểm soát an toàn `Risk & Guardrail Gate` ngăn chặn các hành vi vượt quyền hoặc ảo giác.
*   Quy trình phê duyệt nội bộ của RM (`Human Approval Node`) kiểm soát trước khi gọi API nghiệp vụ.
*   Môi trường lưu trữ trạng thái phiên làm việc chung (`Shared Case State`).
*   Mock APIs và cơ sở dữ liệu giả lập chất lượng cao (`SYNTHETIC DEMO DATA`) cho MVP.

### 2.2 Non-Scope (Ngoài phạm vi)
*   `[OUT OF SCOPE]` Tích hợp trực tiếp với hệ thống Core Banking và CRM thật của SHB ở giai đoạn MVP (Cần SHB cung cấp đặc tả API thật).
*   `[OUT OF SCOPE]` Tự động ra quyết định phê duyệt tín dụng hoặc tự động chấp thuận khách hàng mà không có sự kiểm duyệt của con người.
*   `[OUT OF SCOPE]` Phát triển chatbot công khai trực tiếp cho khách hàng doanh nghiệp tự giao dịch.
*   `[OUT OF SCOPE]` Fine-tuning các mô hình ngôn ngữ lớn (chỉ ưu tiên Prompt Engineering, Few-shot và RAG).

---

## 3. Stakeholders and Users
`[CONFIRMED INPUT]`

| Vai trò | Mô tả | Vai trò trong hệ thống | Quyền hạn |
| :--- | :--- | :--- | :--- |
| **SHB** | Tổ chức sở hữu, vận hành và mua giải pháp. | Đơn vị chủ quản hệ thống. | Thiết lập quy định bảo mật & phân quyền toàn hệ thống. |
| **RM / Nhân viên SHB** | Người trực tiếp sử dụng hệ thống phục vụ khách hàng doanh nghiệp. | Người dùng cuối trực tiếp (Direct User). | Nhập hồ sơ, xem trace, phê duyệt hoặc từ chối đề xuất hành động. |
| **Khách hàng doanh nghiệp** | Đối tượng được phục vụ bởi nhân viên SHB. | Đối tượng thụ hưởng gián tiếp (Indirect Stakeholder). | Không tương tác trực tiếp với hệ thống. Nhận email/checklist yêu cầu bổ sung thông tin từ RM. |

---

## 4. Business Problem
`[CONFIRMED INPUT]`
Trong quy trình hiện tại tại SHB, khi một khách hàng doanh nghiệp đưa ra các yêu cầu tài chính tích hợp (ví dụ: mở tài khoản thanh toán, dịch vụ chi lương Payroll, thu chi hộ Virtual Account, và vay vốn lưu động ngắn hạn), RM phải tự mình thực hiện chuỗi công việc liên phòng ban phức tạp:
1.  **Tra cứu phân tán:** Tra cứu hàng chục cuốn sổ tay sản phẩm khác nhau.
2.  **Rủi ro tuân thủ:** Xác minh thủ công các điều kiện pháp lý phức tạp (KYC/AML, cơ cấu UBO).
3.  **Vận hành chậm trễ:** Tra cứu quy trình SOP vận hành và chuẩn bị checklist hồ sơ cần có.
4.  **Tương tác lặp đi lặp lại:** Gửi email qua lại nhiều lần với khách hàng do phát hiện thiếu giấy tờ ở giai đoạn muộn.

---

## 5. Pain Points
`[CONFIRMED INPUT]`
Sự thiếu nhất quán và phân tán thông tin dẫn đến các hệ quả kinh doanh:
*   **Thời gian phản hồi (SLA) kéo dài:** RM mất từ 3 - 5 ngày để tổng hợp phương án tư vấn doanh nghiệp.
*   **Chất lượng không đồng đều:** Kết quả tư vấn phụ thuộc lớn vào kinh nghiệm của từng cá nhân RM.
*   **Hậu kiểm phức tạp:** Khó khăn trong việc hậu kiểm, đối chiếu các căn cứ pháp lý và sản phẩm của hồ sơ.
*   **Trải nghiệm khách hàng kém:** Khách hàng phải bổ sung hồ sơ nhiều lần do checklist ban đầu thiếu chính xác.

---

## 6. Proposed Solution
`[PROPOSED DESIGN]`
Xây dựng một hệ thống **Controlled Multi-Agent Workspace** đóng vai trò trợ lý chuyên gia số đứng sau RM. Hệ thống tự động phân rã các yêu cầu phức tạp của khách hàng doanh nghiệp thành các nhiệm vụ nhỏ, giao cho các Agent chuyên môn (Product, Legal, Operations) xử lý song song hoặc tuần tự dựa trên đồ thị trạng thái LangGraph. 
Mọi kết luận của Agent bắt buộc phải đi kèm trích dẫn văn bản chính sách (`Evidence`) và được kiểm duyệt qua bộ lọc an toàn (`Guardrails`) trước khi hiển thị để RM phê duyệt thực thi.

---

## 7. Use Case
`[CONFIRMED INPUT]`

### 7.1 Use Case trung tâm: Corporate Client Request Resolution
*   **Mô tả:** Hỗ trợ RM giải quyết trọn vẹn yêu cầu dịch vụ tài chính phức tạp của khách hàng doanh nghiệp từ khâu nhập nhu cầu đến khâu sinh phương án, checklist hồ sơ thiếu và các tác vụ nội bộ.

### 7.2 Tình huống minh họa (`SYNTHETIC DEMO DATA`):
*   **Doanh nghiệp:** Công ty ABC là doanh nghiệp sản xuất, quy mô 500 nhân sự, nhiều nhà cung cấp. Nhu cầu: Mở tài khoản, chi lương Payroll, dịch vụ thu/chi hộ, và tìm hiểu vốn lưu động bổ sung.
*   **Hồ sơ hiện có:** Đăng ký doanh nghiệp, CCCD người đại diện pháp luật.
*   **Thông tin còn thiếu:** Cơ cấu sở hữu UBO, BCTC năm gần nhất, doanh số giao dịch dự kiến.

---

## 8. Functional Requirements
`[PROPOSED DESIGN]`
*   **FR-1 (Nhập & Chuẩn hóa):** Hệ thống phải cho phép RM nhập yêu cầu dạng text tự nhiên và upload các file tài liệu pháp lý (PDF, PNG).
*   **FR-2 (Router):** Tự động phân loại độ phức tạp của yêu cầu để kích hoạt luồng xử lý tương ứng.
*   **FR-3 (Planner):** Planner Agent phải tự động lập kế hoạch (Execution Plan) và phân phối công việc cho các agent chuyên môn.
*   **FR-4 (Product Matching):** Đề xuất bộ giải pháp sản phẩm phù hợp kèm tính điểm tương thích.
*   **FR-5 (Legal Audit):** Đối chiếu hồ sơ doanh nghiệp với quy chế KYC/AML để tìm lỗ hổng pháp lý.
*   **FR-6 (Ops Checklist):** So sánh hồ sơ thực tế với SOP để lập checklist tài liệu thiếu và soạn thảo email nháp gửi khách hàng.
*   **FR-7 (Evidence Validation):** Kiểm tra tính hợp lệ của tất cả các nguồn trích dẫn.
*   **FR-8 (Human Approval):** Cung cấp màn hình phê duyệt chi tiết cho RM trước khi gọi Mock APIs.

---

## 9. Non-Functional Requirements
`[PROPOSED DESIGN]`
*   **NFR-1 (Độ trễ):** Thời gian xử lý của đồ thị Multi-Agent không vượt quá 30 giây cho một yêu cầu phức tạp.
*   **NFR-2 (Tính chính xác):** 100% các kết luận nghiệp vụ quan trọng phải có trích dẫn tài liệu nguồn hợp lệ.
*   **NFR-3 (Bảo mật dữ liệu):** Che giấu thông tin cá nhân nhạy cảm (PII masking) trong logs.
*   **NFR-4 (Tính chịu lỗi):** Hệ thống phải chịu lỗi tốt khi các API của LLM hoặc Tool bị timeout bằng cơ chế Circuit Breaker.

---

