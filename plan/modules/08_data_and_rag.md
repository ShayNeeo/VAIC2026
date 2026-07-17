> Trích từ [`SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md`](../SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md) (dòng 697-761). Đây là bản trích để AI/dev chỉ cần load đúng module đang làm, không cần load toàn bộ 1156 dòng. Xem [`INDEX.md`](../INDEX.md) để biết thứ tự đọc và bản đầy đủ khi cần đối chiếu.

## 24. Data Requirements
`[DATA REQUIRED]`

Bản kế hoạch yêu cầu chuẩn bị các bộ dữ liệu sau trước khi chuyển sang giai đoạn Pilot:

| Tên Dataset | Đơn vị sở hữu | Nguồn cung cấp | Định dạng dữ liệu | Vai trò trong hệ thống | Trạng thái hiện tại |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Product Catalog** | Phòng Phát triển Sản phẩm | `<SHB_PRODUCT_CATALOG_DATA_REQUIRED>` | PDF / Excel | Tri thức tra cứu sản phẩm doanh nghiệp | `DATA REQUIRED` |
| **Credit & Product Policies** | Khối Quản trị Rủi ro | `<SHB_PRODUCT_POLICY_DATA_REQUIRED>` | PDF | Quy tắc xác định điều kiện cấp hạn mức | `DATA REQUIRED` |
| **Legal & Compliance Policies** | Phòng Pháp lý & Tuân thủ | `<SHB_LEGAL_POLICY_DATA_REQUIRED>` | PDF | Các quy định tuân thủ KYC/AML của SHB | `DATA REQUIRED` |
| **KYC & AML Rules** | Phòng Pháp lý & Tuân thủ | `<SHB_KYC_AML_RULES_REQUIRED>` | JSON / Word | Quy tắc lọc danh sách cấm vận và PEP | `DATA REQUIRED` |
| **Operational SOP** | Khối Vận hành | `<SHB_OPERATIONAL_SOP_DATA_REQUIRED>` | PDF | Quy trình mở tài khoản và xử lý hồ sơ | `DATA REQUIRED` |
| **Case Integration API Spec** | Khối Công nghệ thông tin | `<SHB_CASE_MANAGEMENT_API_REQUIRED>` | Swagger / OpenAPI | Tài liệu kết nối CRM | `DATA REQUIRED` |
| **Task Integration API Spec** | Khối Công nghệ thông tin | `<SHB_TASK_MANAGEMENT_API_REQUIRED>` | Swagger / OpenAPI | Tài liệu kết nối hệ thống giao việc | `DATA REQUIRED` |

### Dữ liệu giả lập tối thiểu cho demo (`SYNTHETIC DEMO DATA`):
*   **Hồ sơ doanh nghiệp mẫu:** 5 hồ sơ doanh nghiệp giả lập (ABC, XYZ, MNP...) với các quy mô và ngành nghề khác nhau để test tính năng Router và Product Matching.
*   **Sản phẩm mẫu:** 5 sản phẩm mẫu (Tài khoản thanh toán, Payroll, Cash Sweeping, Thu hộ Virtual Account, Thấu chi vốn lưu động).
*   **Quy chế giả lập:** 3 văn bản pháp lý giả lập thiết lập các quy tắc kiểm tra người đại diện và UBO.

---

## 25. RAG Design
`[PROPOSED DESIGN]`

### 25.1 Product RAG Pipeline
*   **Parsing & Chunking:** Tài liệu sản phẩm được parse và chia nhỏ thành các chunk từ 300 - 500 tokens. Mỗi chunk bắt buộc phải đính kèm tiêu đề sản phẩm mẹ để không mất ngữ cảnh.
*   **Metadata Filtering:** Gắn metadata cho mỗi chunk bao gồm: `segment` (Doanh nghiệp lớn/SME), `industry` (Sản xuất/Thương mại/Dịch vụ), `effective_date`, và `version`. Khi RM tìm kiếm, hệ thống tự động lọc metadata trước khi thực hiện so khớp vector để loại bỏ các chính sách cũ hoặc không áp dụng cho phân khúc khách hàng.
*   **Reranking:** Sử dụng mô hình Cohere Rerank hoặc tương đương để sắp xếp lại top 10 kết quả tìm kiếm vector nhằm lấy ra 3 chunk có điểm tương thích cao nhất đưa vào ngữ cảnh prompt của Product Agent.

### 25.2 Legal & Compliance RAG Pipeline
*   **Structure-aware Chunking:** Quy chế pháp lý không được cắt chuỗi thô. Quy trình chunking phân tách theo phân cấp chương - điều - khoản của văn bản pháp luật.
*   **Superseded-document handling:** Thiết lập cơ chế đánh dấu phiên bản hiệu lực. Khi một quy chế mới được cập nhật, hệ thống tự động đánh dấu quy chế cũ là `inactive` và loại khỏi cơ sở dữ liệu vector hoạt động để tránh agent trích dẫn các điều khoản đã hết hiệu lực.

---

## 26. Database Design
`[PROPOSED DESIGN]`

Đề xuất thiết kế cơ sở dữ liệu quan hệ lưu trữ thông tin phiên làm việc và audit trail:

### Bảng: `cases`
*   `case_id` (VARCHAR - Primary Key): ID duy nhất của case.
*   `rm_id` (VARCHAR): ID của RM tạo case.
*   `customer_id` (VARCHAR): ID của khách hàng doanh nghiệp.
*   `status` (VARCHAR): Trạng thái (new, in_analysis, pending_information, pending_approval, completed, rejected).
*   `created_at` (TIMESTAMP): Thời gian khởi tạo.

### Bảng: `case_states`
*   `state_id` (SERIAL - Primary Key): ID của bản ghi trạng thái.
*   `case_id` (VARCHAR - Foreign Key -> `cases.case_id`): Liên kết với case.
*   `state_json` (TEXT): Toàn bộ cấu trúc JSON của Shared State tại thời điểm ghi nhận.
*   `updated_at` (TIMESTAMP): Thời gian cập nhật.

### Bảng: `audit_events`
*   `event_id` (VARCHAR - Primary Key): ID duy nhất của sự kiện.
*   `case_id` (VARCHAR - Foreign Key -> `cases.case_id`): Liên kết với case.
*   `actor` (VARCHAR): Tên tác nhân thực hiện (Planner, Legal, RM-999...).
*   `action` (VARCHAR): Hành động thực hiện (validate_document, approve_case...).
*   `payload` (TEXT): Chi tiết tham số đầu vào và đầu ra.
*   `timestamp` (TIMESTAMP): Thời gian xảy ra sự kiện.
*   `signature` (VARCHAR): Chữ ký mã hóa đảm bảo tính toàn vẹn, chống sửa đổi log (Immutable log hash).

---

