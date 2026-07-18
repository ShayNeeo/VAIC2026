# HƯỚNG DẪN DỊCH VỤ THANH TOÁN NHÀ CUNG CẤP (SUPPLIER PAYMENT)
**(Tài liệu đào tạo nội bộ Khối Khách hàng Doanh nghiệp SHB - Cập nhật 2026)**

## 1. TỔNG QUAN GIẢI PHÁP
Dịch vụ Thanh toán nhà cung cấp giúp Khách hàng doanh nghiệp (KHDN) tạo và kiểm soát lệnh thanh toán cho nhà cung cấp/đối tác một cách tập trung, có phân quyền phê duyệt rõ ràng, giảm rủi ro sai sót và gian lận trong thanh toán thủ công.

## 2. CÁC TÍNH NĂNG CHÍNH

### 2.1. Lệnh thanh toán đơn lẻ và theo lô (Batch Payment)
- Tạo lệnh thanh toán đơn lẻ cho từng nhà cung cấp theo hợp đồng/hóa đơn cụ thể.
- Thanh toán theo lô cho hàng trăm nhà cung cấp cùng lúc bằng file định dạng chuẩn (Excel/CSV) upload qua SHB Corporate Online.
- Hỗ trợ đặt lịch thanh toán định kỳ cho các hợp đồng có chu kỳ cố định (thuê mặt bằng, dịch vụ vận hành...).

### 2.2. Phân quyền phê duyệt (Multi-level Approval)
- Thiết lập quy trình phê duyệt nhiều cấp theo hạn mức giá trị lệnh thanh toán (Người lập lệnh → Kiểm soát viên → Người duyệt cuối cùng).
- Hỗ trợ chữ ký số hoặc OTP xác thực giao dịch theo từng cấp phê duyệt.
- Ghi nhận đầy đủ lịch sử thao tác (audit trail) cho từng lệnh thanh toán để phục vụ đối soát nội bộ.

### 2.3. Theo dõi trạng thái thanh toán
- Tra cứu trạng thái lệnh thanh toán theo thời gian thực: đang chờ duyệt, đã duyệt, đã thực hiện, bị từ chối.
- Thông báo tự động cho người lập lệnh khi lệnh thanh toán bị từ chối hoặc thực hiện không thành công.

## 3. BIỂU PHÍ THAM CHIẾU (Mức tiêu chuẩn)
- Phí quản lý dịch vụ (gói Standard Corporate): thu hàng tháng theo biểu phí hiện hành, không phụ thuộc số lượng lệnh.
- Phí giao dịch USD (gói Premium Corporate, thanh toán nhà cung cấp nước ngoài): theo tỷ lệ phần trăm trên giá trị mỗi lệnh.
- Thời gian triển khai tham chiếu: theo cam kết SLA, tùy số lượng tài khoản nhà cung cấp cần khai báo ban đầu.

## 4. ĐIỀU KIỆN SỬ DỤNG DỊCH VỤ
- Doanh nghiệp đã có tài khoản thanh toán doanh nghiệp tại SHB.
- Đã đăng ký Người được ủy quyền ký duyệt lệnh thanh toán (Authorized Signer) theo đúng thẩm quyền trong hồ sơ pháp lý.
- Khách hàng ở trạng thái hoạt động (active); phân khúc rủi ro cao cần chuyên viên thẩm định trước khi kích hoạt.
- Đã có Giấy chứng nhận đăng ký doanh nghiệp còn hiệu lực.

## 5. HỒ SƠ ĐĂNG KÝ
1. Giấy đề nghị đăng ký dịch vụ thanh toán nhà cung cấp (theo mẫu SHB).
2. Bản sao Giấy chứng nhận đăng ký doanh nghiệp.
3. Văn bản chỉ định Người được ủy quyền ký duyệt lệnh thanh toán theo từng cấp hạn mức.
4. Danh sách nhà cung cấp cần khai báo ban đầu (nếu triển khai thanh toán theo lô ngay từ đầu).

## 6. LƯU Ý VẬN HÀNH
Lệnh thanh toán vượt hạn mức cấp phê duyệt cao nhất đã đăng ký sẽ bị hệ thống tự động từ chối và yêu cầu bổ sung cấp phê duyệt mới. RM cần rà soát định kỳ danh sách Người được ủy quyền để đảm bảo khớp với thay đổi nhân sự của doanh nghiệp.
