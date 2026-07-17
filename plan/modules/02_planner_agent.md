> Trích từ [`SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md`](../SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md) (dòng 273-319). Đây là bản trích để AI/dev chỉ cần load đúng module đang làm, không cần load toàn bộ 1156 dòng. Xem [`INDEX.md`](../INDEX.md) để biết thứ tự đọc và bản đầy đủ khi cần đối chiếu.

## 15. Planner Agent
`[PROPOSED DESIGN]`

1.  **Mục tiêu:** Nhận bối cảnh yêu cầu nghiệp vụ phức tạp của RM, lập kế hoạch thực thi tối ưu (DAG), giao việc cho các agent chuyên môn, và thích ứng luồng xử lý khi phát hiện ngoại lệ hoặc thiếu dữ liệu.
2.  **Phạm vi trách nhiệm:** Lập kế hoạch, theo dõi tiến độ các tác vụ, tổng hợp Brief cuối cùng, và xử lý vòng lặp thu thập thông tin còn thiếu.
3.  **Những gì agent không được làm:** `[OUT OF SCOPE]` Tự đưa ra kết luận pháp lý mà không qua Legal Agent; Tự ý đề xuất sản phẩm nằm ngoài Product Agent; Tự ý chạy các vòng lặp vô hạn (Max loops = 3).
4.  **Input Schema:**
    ```json
    {
      "case_id": "string",
      "customer_request": "string",
      "company_profile": "object",
      "available_documents": "array"
    }
    ```
5.  **Output Schema:**
    ```json
    {
      "execution_plan": [
        {
          "task_id": "string",
          "owner": "string",
          "description": "string",
          "dependencies": ["string"]
        }
      ],
      "status": "string"
    }
    ```
6.  **Dữ liệu cần có:** Danh sách năng lực của từng Agent chuyên môn (Agent Capability Registry).
7.  **Knowledge base cần có:** Quy tắc phân rã tác vụ nghiệp vụ ngân hàng mẫu.
8.  **Tools được phép gọi:** Không gọi tool nghiệp vụ trực tiếp, chỉ tương tác với Graph State.
9.  **Prompt Policy:** Sử dụng cấu trúc lập luận Chain-of-Thought (CoT). Bắt buộc phải liệt kê rõ lý do phân chia task và sự phụ thuộc.
10. **Deterministic Rules:** Nếu Legal Agent báo lỗi mức độ `Blocking`, Planner bắt buộc phải pause workflow và chuyển sang node Operations soạn checklist thiếu.
11. **Workflow steps:** Nhận Input $\rightarrow$ Phân rã $\rightarrow$ Xây dựng DAG $\rightarrow$ Giao việc $\rightarrow$ Nhận phản hồi $\rightarrow$ Điều chỉnh kế hoạch nếu cần $\rightarrow$ Chuyển Validator.
12. **Điều kiện dừng:** Tất cả các task trong kế hoạch được đánh dấu `completed` hoặc có task bị đánh dấu `failed` ở mức độ không thể sửa chữa.
13. **Điều kiện retry:** Task gặp sự cố mạng hoặc lỗi cú pháp JSON của LLM chuyên môn (tối đa 2 lần retry).
14. **Điều kiện escalation:** Xung đột chính sách giữa Legal Agent và Product Agent (Ví dụ: Product đề xuất cho vay nhưng Legal chặn do thuộc ngành nghề cấm). Chuyển case sang trạng thái `pending_review` để RM tự quyết định.
15. **Các lỗi có thể xảy ra:** Sinh kế hoạch có vòng lặp phụ thuộc chéo (A chờ B, B chờ A).
16. **Cách xử lý lỗi:** Sử dụng giải thuật kiểm tra chu kỳ đồ thị trước khi thực thi; nếu phát hiện chu kỳ, lập tức giải phóng và chạy tuần tự mặc định.
17. **Logging:** Log chi tiết sơ đồ DAG dưới dạng text hoặc adjacency list.
18. **Metrics:** Tỷ lệ lập kế hoạch hợp lệ (Plan Validity Rate), Số bước thích ứng trung bình (Average Re-planning Steps).
19. **Test cases:** Test phân rã case doanh nghiệp ABC (Yêu cầu Payroll + Tín dụng thấu chi). Kế hoạch hợp lệ phải chạy Payroll trước khi thẩm định thấu chi.
20. **Definition of Done:** Kế hoạch thực thi được tạo thành công, không chứa chu kỳ, và phân bổ đúng Agent chuyên môn.

---

