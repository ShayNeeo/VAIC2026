# Kiến trúc thông tin giao diện RM Workspace

Mục tiêu của bố cục là để RM trả lời được trong một lần nhìn:

1. Tôi đang phục vụ khách hàng nào?
2. Khách hàng đang cần gì?
3. Sản phẩm nào được đề xuất?
4. Điều kiện đã đạt hay đang bị chặn?
5. Tôi phải làm gì tiếp theo?
6. Tôi kiểm chứng kết luận ở đâu?

## Chức năng của từng khối

| Khối | Chức năng | RM cần đọc gì | Không nên hiểu là |
|---|---|---|---|
| Header nhận diện | Xác định RM và khách hàng/workspace đang phục vụ | `RM-999`, `Minh Phát · COMP-MP` | Form nhập lại toàn bộ hồ sơ khách hàng |
| Thanh tóm tắt case | Tóm tắt nhu cầu, sản phẩm, trạng thái và số điều kiện đang chặn | Đặc biệt nhìn `Tình trạng` và `Đang chặn xử lý` | Tổng số hồ sơ cần cho triển khai |
| Thanh tiến trình | Cho biết workflow đã hoàn thành và đang dừng ở bước nào | Bước viền đậm là bước hiện tại | Phần trăm hoàn thành SLA |
| Cột Đầu vào | Chọn case demo, upload/process hồ sơ, review field và xác nhận context | Input mẫu, nguồn field và “RM làm tiếp” | Kết quả phân tích thật |
| Khối Kết luận xử lý | Trình bày lần lượt Nhu cầu → Sản phẩm → Điều kiện | Đọc từ trái sang phải | Quyết định tín dụng cuối cùng |
| Checklist chuẩn bị | Phân biệt hồ sơ đã có, hồ sơ đang chặn và hồ sơ chỉ phục vụ triển khai | Cột `Mục đích` | Mọi hồ sơ thiếu đều đang chặn workflow |
| Cột Hành động ưu tiên | Chỉ hiển thị hành động phù hợp với trạng thái hiện tại | Nút chính và lý do phải làm | Cho phép agent tự thực thi ngoài quyền RM |
| Output kỳ vọng | Cho biết case mẫu phải ra gì ở lần đầu và cuối luồng | So sánh trạng thái/sản phẩm thực tế | Cam kết chất lượng trên dữ liệu thật |
| Evidence | Hiển thị tài liệu, phiên bản và vị trí nguồn | Mở khi cần đối chiếu claim | Nội dung chính cần đọc trong mọi case |
| Nhật ký AI | Cho biết module/model/rule/retrieval nào đã tạo kết quả, latency/token/cost và nguồn | Mở khi cần giải thích hoặc QA một quyết định | Raw prompt hoặc dữ liệu PII đầy đủ |
| Audit/JSON | Phục vụ điều tra, debug và kiểm toán | Mở khi cần kiểm chứng sâu | Thông tin nghiệp vụ chính cho RM |

## Quy tắc bố trí

- **Trái:** dữ liệu RM đưa vào.
- **Giữa:** kết luận nghiệp vụ quan trọng nhất.
- **Phải:** hành động RM cần thực hiện ngay.
- **Trên cùng:** context và trạng thái để tránh xử lý nhầm khách hàng/case.
- **Phía dưới, thu gọn:** evidence, audit và JSON kỹ thuật.
- Màu xanh: có thể tiếp tục; màu vàng: thiếu thông tin/cần chú ý; màu đỏ: bị chặn hoặc lỗi.

## Output của các case demo

| Case | Output lần đầu | Sản phẩm | Hành động tiếp | Output sau cùng |
|---|---|---|---|---|
| Payroll đủ điều kiện sơ bộ | Chờ RM duyệt tạo case/task | `PROD-PAYROLL` | Xem payload → RM duyệt → mock execute | `completed`, `MOCK-CRM-*`, `MOCK-TASK-*` |
| Payroll + vốn lưu động | Thiếu thông tin/hồ sơ; 2 blocker | `PROD-PAYROLL`, `PROD-WORKING-CAPITAL` | Bổ sung UBO + BCTC | 0 blocker, chờ RM duyệt case/task |
| Nhu cầu cần làm rõ | Cần RM xác nhận thêm | Chưa đề xuất | Sửa nhu cầu cụ thể | Chỉ tiếp tục khi intent đủ rõ |
| Prompt injection | `UNSAFE_INPUT` | Không có | Nhập lại nhu cầu hợp lệ | Không tạo case hoặc external action |
