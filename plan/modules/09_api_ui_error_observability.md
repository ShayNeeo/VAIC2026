> Trích từ [`SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md`](../SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md) (dòng 762-847). Đây là bản trích để AI/dev chỉ cần load đúng module đang làm, không cần load toàn bộ 1156 dòng. Xem [`INDEX.md`](../INDEX.md) để biết thứ tự đọc và bản đầy đủ khi cần đối chiếu.

## 27. API Design
`[PROPOSED DESIGN]`

Đặc tả các endpoints chính phục vụ ứng dụng:

### Endpoint: `POST /api/v1/cases`
*   **Mục đích:** Khởi tạo case mới từ yêu cầu của RM.
*   **Request body:**
    ```json
    {
      "customer_id": "string",
      "rm_id": "string",
      "request_text": "string"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "case_id": "CORP-2026-001",
      "status": "new",
      "created_at": "2026-07-17T16:10:00Z"
    }
    ```

### Endpoint: `POST /api/v1/cases/{case_id}/approve`
*   **Mục đích:** RM phê duyệt đề xuất để thực thi hành động.
*   **Request headers:** `X-Approval-Token: jwt-token-signed-by-rm`
*   **Response (200 OK):**
    ```json
    {
      "case_id": "CORP-2026-001",
      "approval_status": "approved",
      "actions_executed": [
        {
          "action_type": "create_crm_case",
          "crm_case_id": "CRM-88820"
        }
      ]
    }
    ```

---

## 28. UI Design
`[PROPOSED DESIGN]`

Thiết kế giao diện Workspace của RM (RM Workspace) hướng tới trải nghiệm trực quan và an toàn:

*   **Bảng điều khiển Case (Case Detail Dashboard):** Hiển thị tóm tắt thông tin doanh nghiệp, biểu đồ tiến độ xử lý của từng agent dưới dạng Timeline.
*   **Khung trích dẫn Bằng chứng (Evidence Panel):** Hiển thị các đề xuất của Agent ở cột bên trái và đoạn tài liệu chính sách đối chiếu trực tiếp ở cột bên phải. Các đoạn trích dẫn được tô màu xanh lá cây nếu Validator xác thực thành công.
*   **Khung cảnh báo thiếu hồ sơ (Missing Information Drawer):** Hiển thị rõ danh sách tài liệu còn thiếu bằng màu đỏ kèm theo nút bấm cho phép RM nhấn nhanh để gửi email yêu cầu bổ sung cho doanh nghiệp.
*   **Nút duyệt hành động (Approval Panel):** Bắt buộc hiển thị hộp thoại xác nhận chi tiết các hành động hệ thống chuẩn bị thực hiện trên CRM/Core Banking kèm mã pin duyệt của RM.

---

## 29. Error Handling
`[PROPOSED DESIGN]`

Bảng xử lý sự cố hệ thống và phương án dự phòng (Fallback):

| Sự cố phát sinh | Phương thức phát hiện | Tác động hệ thống | Có thể retry? | Phương án dự phòng (Fallback) | Cơ chế Escalation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **API LLM bị Timeout** | Hệ thống gateway kiểm tra thời gian phản hồi quá 15 giây. | Tiến trình của Agent bị đình trệ. | Có (Tối đa 2 lần) | Tự động chuyển truy vấn sang mô hình dự phòng (Backup LLM Model). | Nếu cả 2 mô hình đều lỗi, báo lỗi hệ thống và lưu trạng thái case là `failed`. |
| **Agent sinh JSON lỗi** | Khối Pydantic validator báo lỗi parse schema. | Không thể cập nhật thông tin vào Shared State. | Có (1 lần) | Gửi lại prompt yêu cầu sửa định dạng kèm thông tin thông báo lỗi cú pháp. | Nếu retry vẫn lỗi, Planner tự động bỏ qua agent này và đánh dấu task là `failed` để RM tự nhập tay. |
| **Lỗi kết nối Tool API** | Http Status code trả về 5xx hoặc Connection Refused. | Không thể lấy thông tin KYC hoặc Product Policy. | Không | Trả về dữ liệu trống và ghi nhận cảnh báo "Mất kết nối dữ liệu". Agent sẽ chuyển sang chế độ nghi ngờ và báo thiếu thông tin. | Gửi thông báo sự cố mạng cho đội ngũ quản trị kỹ thuật (DevOps). |

---

## 30. Observability
`[PROPOSED DESIGN]`

Nhật ký hoạt động của hệ thống được giám sát thông qua 3 thành phần:
1.  **Traces:** Sử dụng thư viện Jaeger hoặc LangSmith để theo dõi chi tiết luồng chạy của Graph. Mỗi lần chạy của Planner được cấp một `trace_id` để kiểm tra thứ tự gọi các agent node.
2.  **Metrics:** Giám sát thời gian phản hồi của từng Node (Node Latency), Số lượng tokens sử dụng trên mỗi Case, Tỷ lệ lỗi cú pháp JSON của LLM.
3.  **Audit Logs:** Lưu lại toàn bộ lịch sử thay đổi của `SharedCaseState` sau mỗi Node thực thi để RM có thể kiểm tra lại nguồn gốc quyết định khi có hậu kiểm.

---

## 31. Security and Governance
`[PROPOSED DESIGN]`

*   **Role-Based Access Control (RBAC):** Chỉ có RM được phân quyền quản lý khách hàng đó mới có thể xem và thực thi case. Nhân viên thẩm định tuân thủ chỉ có quyền đọc `legal_result` và audit log.
*   **On-Premise Deployment Option:** Để bảo mật tuyệt đối dữ liệu khách hàng theo quy định của ngân hàng nhà nước, hệ thống hỗ trợ đóng gói Docker để triển khai toàn bộ ứng dụng, Vector DB và mô hình ngôn ngữ lớn (thông qua Ollama/vLLM) hoàn toàn trong hạ tầng mạng nội bộ (On-Premise) của SHB.

---

