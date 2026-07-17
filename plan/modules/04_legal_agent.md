> Trích từ [`SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md`](../SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md) (dòng 380-432). Đây là bản trích để AI/dev chỉ cần load đúng module đang làm, không cần load toàn bộ 1156 dòng. Xem [`INDEX.md`](../INDEX.md) để biết thứ tự đọc và bản đầy đủ khi cần đối chiếu.

## 17. Legal & Compliance Agent
`[PROPOSED DESIGN]`

1.  **Mục tiêu:** Thẩm định tính pháp lý của doanh nghiệp và kiểm tra tính tuân thủ của giải pháp đề xuất đối với quy định hiện hành.
2.  **Phạm vi trách nhiệm:** Kiểm tra KYC/AML, xác thực hiệu lực tài liệu pháp lý, thẩm định cơ cấu sở hữu UBO, người đại diện theo pháp luật và thẩm quyền ký kết.
3.  **Những gì agent không được làm:** Tự ý bỏ qua lỗi tuân thủ nghiêm trọng; Tự động phê duyệt mở tài khoản cho khách hàng thuộc danh sách đen (Watchlist/Sanction list).
4.  **Input Schema:**
    ```json
    {
      "company_profile": "object",
      "uploaded_documents": [
        {
          "doc_type": "string",
          "issue_date": "string",
          "expiry_date": "string"
        }
      ],
      "proposed_products": ["string"]
    }
    ```
5.  **Output Schema:**
    ```json
    {
      "eligibility_status": "string",  // passed, failed, pending_info
      "failed_checks": [
        {
          "rule_id": "string",
          "reason": "string",
          "severity": "string"  // blocking, warning
        }
      ],
      "missing_documents": ["string"],
      "citations": ["object"]
    }
    ```
6.  **Dữ liệu cần có:** `<SHB_LEGAL_POLICY_DATA_REQUIRED>`
7.  **Knowledge base cần có:** `<SHB_COMPLIANCE_POLICY_DATA_REQUIRED>`, `<SHB_KYC_AML_RULES_REQUIRED>`
8.  **Tools được phép gọi:** `validate_business_registration()`, `check_document_expiry()`, `check_product_eligibility()`, `search_compliance_policy()`.
9.  **Prompt Policy:** Tuyệt đối thận trọng. Mọi rủi ro pháp lý dù nhỏ nhất đều phải báo cáo và xếp hạng rủi ro rõ ràng.
10. **Deterministic Rules:** Giấy đăng ký kinh doanh hết hạn hoặc không khớp mã số thuế $\rightarrow$ Đánh dấu trạng thái `failed` mức độ `Blocking` lập tức. Khách hàng không có thông tin UBO $\rightarrow$ Chặn đề xuất cấp tín dụng thấu chi.
11. **Workflow steps:** Đọc thông tin hồ sơ $\rightarrow$ Kiểm tra tính đầy đủ pháp lý $\rightarrow$ Gọi tool đối chiếu quy định KYC/AML $\rightarrow$ Kiểm tra hiệu lực tài liệu $\rightarrow$ Trích xuất citation $\rightarrow$ Cập nhật Shared State.
12. **Điều kiện dừng:** Hoàn thành kiểm tra tất cả các hạng mục pháp lý bắt buộc theo quy định.
13. **Điều kiện retry:** API kiểm tra danh sách cấm vận bị timeout.
14. **Điều kiện escalation:** Phát hiện dấu hiệu rửa tiền hoặc khách hàng thuộc diện PEP (Chính trị gia có ảnh hưởng) có rủi ro tuân thủ cao. Chuyển tiếp ngay lập tức sang Phòng Legal & Compliance nội bộ để hậu kiểm thủ công.
15. **Các lỗi có thể xảy ra:** Nhầm lẫn giữa người đại diện pháp luật và người được ủy quyền hợp pháp.
16. **Cách xử lý lỗi:** Bắt buộc so khớp số CCCD/Hộ chiếu giữa giấy ủy quyền và hồ sơ định danh gốc.
17. **Logging:** Ghi log chi tiết danh sách các chốt kiểm soát tuân thủ đã đi qua (Passed/Failed check logs).
18. **Metrics:** Tỷ lệ phát hiện thiếu hồ sơ pháp lý (Missing Document Recall), Tỷ lệ phê duyệt không an toàn (Unsafe Approval Rate = 0%).
19. **Test cases:** Test case doanh nghiệp ABC thiếu thông tin UBO. Kết quả mong đợi: Hệ thống phải báo trạng thái `pending_info` và yêu cầu bổ sung thông tin UBO.
20. **Definition of Done:** Báo cáo thẩm định pháp lý được xuất ra, chỉ rõ điều kiện đạt/chưa đạt kèm theo điều khoản quy chế SHB làm căn cứ đối chiếu.

---

