> Trích từ [`SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md`](../SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md) (dòng 320-379). Đây là bản trích để AI/dev chỉ cần load đúng module đang làm, không cần load toàn bộ 1156 dòng. Xem [`INDEX.md`](../INDEX.md) để biết thứ tự đọc và bản đầy đủ khi cần đối chiếu.

## 16. Product Agent
`[PROPOSED DESIGN]`

1.  **Mục tiêu:** Phân tích nhu cầu của khách hàng doanh nghiệp để đề xuất gói sản phẩm tài chính hoặc bộ giải pháp tích hợp tối ưu.
2.  **Phạm vi trách nhiệm:** Tra cứu danh mục sản phẩm, tính toán mức độ phù hợp (matching score), đóng gói giải pháp (bundling).
3.  **Những gì agent không được làm:** Tự ý cam kết lãi suất đặc thù ngoài chính sách; Tự quyết định doanh nghiệp đủ điều kiện pháp lý để mở dịch vụ hay không.
4.  **Input Schema:**
    ```json
    {
      "company_profile": {
        "industry": "string",
        "employees_count": "integer",
        "annual_revenue": "number"
      },
      "customer_objectives": ["string"]
    }
    ```
5.  **Output Schema:**
    ```json
    {
      "recommended_bundle": {
        "bundle_name": "string",
        "products": [
          {
            "product_id": "string",
            "name": "string",
            "matching_reason": "string",
            "prerequisites": ["string"]
          }
        ]
      },
      "missing_parameters": ["string"],
      "citations": [
        {
          "claim": "string",
          "source_doc": "string",
          "section": "string",
          "quote": "string"
        }
      ]
    }
    ```
6.  **Dữ liệu cần có:** `<SHB_PRODUCT_CATALOG_DATA_REQUIRED>`
7.  **Knowledge base cần có:** `<SHB_PRODUCT_POLICY_DATA_REQUIRED>`
8.  **Tools được phép gọi:** `search_product_catalog()`, `retrieve_product_policy()`.
9.  **Prompt Policy:** Chỉ được đưa ra các đề xuất nằm trong cơ sở tri thức sản phẩm được cung cấp. Cấm tự bịa tên sản phẩm.
10. **Deterministic Rules:** Nếu doanh thu năm dưới 50 tỷ VND, cấm đề xuất gói Cash Sweeping tự động (áp dụng quy định cứng của chính sách quản lý dòng tiền).
11. **Workflow steps:** Phân tích bối cảnh doanh nghiệp $\rightarrow$ Gọi tool tìm kiếm sản phẩm ứng viên $\rightarrow$ Đối chiếu điều kiện cơ bản $\rightarrow$ Thiết lập bundle $\rightarrow$ Trích xuất bằng chứng trích dẫn $\rightarrow$ Ghi kết quả vào Shared State.
12. **Điều kiện dừng:** Đã tạo được danh mục đề xuất sản phẩm kèm match score hoặc không tìm thấy bất kỳ sản phẩm nào phù hợp.
13. **Điều kiện retry:** Kết quả tìm kiếm từ RAG rỗng do lỗi kết nối vector db.
14. **Điều kiện escalation:** Doanh nghiệp có quy mô và tính chất quá đặc biệt không khớp bất kỳ sản phẩm chuẩn nào. Đề xuất RM chuyển sang luồng thiết kế gói sản phẩm may đo (Tailor-made solution).
15. **Các lỗi có thể xảy ra:** Đề xuất trùng lặp sản phẩm trong cùng một gói.
16. **Cách xử lý lỗi:** Áp dụng bộ lọc deduplication ở đầu ra của Agent.
17. **Logging:** Ghi log các truy vấn gửi tới Product Vector DB và điểm số cosine similarity.
18. **Metrics:** Tỷ lệ đề xuất sản phẩm chính xác (Recommendation Accuracy), Tỷ lệ trích dẫn đầy đủ (Citation Coverage).
19. **Test cases:** Chạy test case với Công ty ABC (500 nhân viên). Giải pháp đề xuất bắt buộc phải có Dịch vụ chi lương (Payroll) và Cash Management.
20. **Definition of Done:** Trả về JSON đúng cấu trúc, chứa đầy đủ các sản phẩm phù hợp và 100% đề xuất có trích dẫn nguồn tài liệu hợp lệ.

---

