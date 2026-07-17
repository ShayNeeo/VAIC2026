> Trích từ [`SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md`](../SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md) (dòng 433-485). Đây là bản trích để AI/dev chỉ cần load đúng module đang làm, không cần load toàn bộ 1156 dòng. Xem [`INDEX.md`](../INDEX.md) để biết thứ tự đọc và bản đầy đủ khi cần đối chiếu.

## 18. Operations Agent
`[PROPOSED DESIGN]`

1.  **Mục tiêu:** Thiết lập các bước xử lý nghiệp vụ tiếp theo cho nhân viên SHB sau khi có kết quả từ khối Sản phẩm và Pháp lý.
2.  **Phạm vi trách nhiệm:** Lập checklist hồ sơ cần thu thập, soạn thảo email nháp gửi khách hàng yêu cầu bổ sung, và chuẩn bị dữ liệu gọi API tạo Case/Task trên CRM nội bộ.
3.  **Những gì agent không được làm:** Tự động tạo case thật trên hệ thống CRM lõi khi chưa được RM bấm nút duyệt thông qua.
4.  **Input Schema:**
    ```json
    {
      "case_id": "string",
      "recommended_products": ["string"],
      "legal_status": "string",
      "missing_documents_from_legal": ["string"]
    }
    ```
5.  **Output Schema:**
    ```json
    {
      "proposed_crm_case": {
        "case_title": "string",
        "priority": "string",
        "tasks": [
          {
            "task_description": "string",
            "assigned_team": "string",
            "sla_hours": "integer"
          }
        ]
      },
      "customer_email_draft": {
        "subject": "string",
        "body": "string"
      }
    }
    ```
6.  **Dữ liệu cần có:** `<SHB_OPERATIONAL_SOP_DATA_REQUIRED>`
7.  **Knowledge base cần có:** `<SHB_REQUIRED_DOCUMENT_CHECKLIST_REQUIRED>`, `<SHB_SERVICE_LEVEL_AGREEMENT_REQUIRED>`
8.  **Tools được phép gọi:** `get_required_documents()`, `check_document_completeness()`, `draft_customer_email()`, `generate_decision_brief()`.
9.  **Prompt Policy:** Sử dụng văn phong giao tiếp ngân hàng chuẩn mực, lịch sự, và rõ ràng. Email nháp gửi khách hàng phải phân tách rõ ràng danh sách tài liệu cần bổ sung bằng dấu đầu dòng.
10. **Deterministic Rules:** SLA của từng task nghiệp vụ được tạo phải tuân thủ chính xác quy định thời gian xử lý dịch vụ của SHB, không được để LLM tự tính toán bừa bãi.
11. **Workflow steps:** Thu thập kết quả Product và Legal $\rightarrow$ Gọi tool lấy SOP và checklist tương ứng $\rightarrow$ Đối chiếu tài liệu hiện có để tìm tài liệu thiếu $\rightarrow$ Soạn email nháp $\rightarrow$ Sinh payload CRM case nháp.
12. **Điều kiện dừng:** Soạn thảo thành công toàn bộ email nháp, checklist thiếu và các task nghiệp vụ tương ứng.
13. **Điều kiện retry:** Lỗi sinh email mẫu do token output bị cắt ngắn.
14. **Điều kiện escalation:** Các yêu cầu dịch vụ cần xử lý gấp (VIP case) vượt quá khả năng tính toán SLA chuẩn $\rightarrow$ Chuyển luồng ưu tiên đặc biệt.
15. **Các lỗi có thể xảy ra:** Email nháp chứa thông tin chưa được kiểm chứng của khách hàng.
16. **Cách xử lý lỗi:** Chỉ sử dụng các biến có cấu trúc từ `SharedCaseState` để điền vào template email.
17. **Logging:** Lưu lại bản nháp email và các tác vụ CRM được đề xuất vào Shared State.
18. **Metrics:** Tỷ lệ đầy đủ của checklist hồ sơ (Checklist Completeness), Tỷ lệ RM chỉnh sửa email nháp (Email Edit Rate).
19. **Test cases:** Test sinh email cho doanh nghiệp ABC. Email nháp bắt buộc phải có câu yêu cầu cung cấp: "Thông tin chủ sở hữu hưởng lợi (UBO)" và "Báo cáo tài chính năm gần nhất".
20. **Definition of Done:** Checklist hồ sơ và email nháp được sinh ra đầy đủ, chính xác, không chứa lỗi chính tả và sẵn sàng cho RM phê duyệt.

---

