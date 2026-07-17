> Trích từ [`SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md`](../SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md) (dòng 960-1013). Đây là bản trích để AI/dev chỉ cần load đúng module đang làm, không cần load toàn bộ 1156 dòng. Xem [`INDEX.md`](../INDEX.md) để biết thứ tự đọc và bản đầy đủ khi cần đối chiếu.

## 39. Risks and Mitigations
`[PROPOSED DESIGN]`

*   **Rủi ro 1: Chất lượng OCR tài liệu scan kém.**
    *   *Mô tả:* Đăng ký kinh doanh hoặc CCCD do khách hàng cung cấp bị mờ, lệch góc khiến Input Validator trích xuất sai thông tin (ví dụ: nhầm mã số thuế), dẫn đến Legal Agent thẩm định sai.
    *   *Biện pháp khắc phục:* Tích hợp thư viện OCR chất lượng cao có chức năng lọc nhiễu ảnh và bắt buộc hiển thị lại bảng thông tin trích xuất có cấu trúc trên UI để RM kiểm tra và sửa tay trước khi truyền vào đồ thị Agent.
*   **Rủi ro 2: Chi phí token và Độ trễ cao của mô hình Multi-Agent.**
    *   *Mô tả:* Việc gọi liên tục nhiều mô hình LLM qua các Node (Planner $\rightarrow$ Product $\rightarrow$ Legal $\rightarrow$ Validator) tạo độ trễ phản hồi lớn và tiêu tốn nhiều chi phí API.
    *   *Biện pháp khắc phục:* Tối ưu hóa chạy song song các Node không phụ thuộc (Product và Legal). Áp dụng **Semantic Cache** để lưu trữ kết quả xử lý của các câu hỏi hoặc hồ sơ tương tự đã được duyệt trước đó.

---

## 40. Assumption Register
`[ASSUMPTION]`

Đăng ký các giả định cần được xác minh lại với SHB:

| ID Giả định | Nội dung giả định | Lý do giả định | Hậu quả nếu giả định sai | Người xác minh | Phương pháp xác minh | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ASM-001** | Hệ thống CRM của SHB hỗ trợ gọi API tạo case và task từ bên ngoài. | Để Action Executor thực thi nghiệp vụ tự động sau khi RM duyệt. | Hệ thống chỉ dừng ở mức soạn nháp email và checklist, RM phải tự tạo case thủ công trên CRM. | Đại diện IT SHB | Đánh giá tài liệu kỹ thuật API CRM của SHB. | `TO BE VALIDATED` |
| **ASM-002** | Dữ liệu chính sách sản phẩm và quy chế KYC có thể được xuất ra dưới dạng text sạch (hoặc PDF gốc). | Để xây dựng cơ sở dữ liệu tri thức RAG chính xác cho Product/Legal Agent. | RAG hoạt động kém hiệu quả, trích xuất sai nguồn do file PDF scan bị lỗi font hoặc mất cấu trúc. | Đội phát triển sản phẩm SHB | Kiểm tra cấu trúc tệp tài liệu chính sách hiện có. | `TO BE VALIDATED` |

---

## 41. Open Questions
`[DATA REQUIRED]`

Các câu hỏi nghiệp vụ và kỹ thuật cần SHB phản hồi để hoàn thiện hệ thống:

| ID Câu hỏi | Nội dung câu hỏi | Mức độ ảnh hưởng | Thành phần liên quan | Độ ưu tiên | Người chịu trách nhiệm | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Q-001** | Quy trình phê duyệt cấp thấu chi vốn lưu động của SHB có bắt buộc phải thẩm định Báo cáo tài chính đã được kiểm toán hay chấp nhận báo cáo thuế? | Quyết định logic kiểm tra của Legal Agent đối với điều kiện cho vay. | Legal Agent / Product eligibility rules | High | Khối Quản trị Rủi ro SHB | `DATA REQUIRED` |
| **Q-002** | SHB có yêu cầu cô lập dữ liệu khách hàng doanh nghiệp theo từng chi nhánh/vùng quản lý của RM không? | Quyết định thiết kế kiến trúc phân quyền truy cập cơ sở dữ liệu Shared State. | Security Architecture / State Layer | High | Khối Công nghệ thông tin SHB | `DATA REQUIRED` |

---

## 42. Traceability Matrix
`[PROPOSED DESIGN]`

Bản đồ truy xuất nguồn gốc từ yêu cầu nghiệp vụ đến kịch bản kiểm thử:

```text
Yêu cầu nghiệp vụ (Business Requirement)
  └─> Quy trình phối hợp Multi-Agent (E2E Workflow)
        └─> Thiết kế Agent chuyên môn (Product / Legal / Ops Agent)
              └─> Công cụ hỗ trợ nghiệp vụ (Tool Registry)
                    └─> Kịch bản kiểm thử tương ứng (Test Case ID)
                          └─> Tiêu chí nghiệm thu (Acceptance Criteria)
```

*   *Ví dụ cụ thể:* Yêu cầu kiểm tra KYC doanh nghiệp ABC $\rightarrow$ Luồng xử lý Legal Node $\rightarrow$ Legal Agent $\rightarrow$ Gọi tool `check_beneficial_owner_information()` $\rightarrow$ Test Case 34.1 (ABC Case) $\rightarrow$ Nghiệm thu thành công khi hệ thống phát hiện thiếu UBO và chuyển trạng thái pending_information.

---

