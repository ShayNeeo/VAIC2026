# QUY TRÌNH NHẬN DIỆN KHÁCH HÀNG (KYC) VÀ MỞ TÀI KHOẢN DOANH NGHIỆP
**(Áp dụng cho hệ thống SHB - Cập nhật chống Rửa tiền AML 2026)**

## 1. MỤC ĐÍCH
Quy trình này quy định các bước bắt buộc trong việc Nhận diện Khách hàng (KYC), Thẩm định chuyên sâu (EDD) và phê duyệt mở Tài khoản thanh toán cho Khách hàng doanh nghiệp nhằm tuân thủ quy định của Ngân hàng Nhà nước và Luật Phòng chống rửa tiền.

## 2. QUY TRÌNH KYC CƠ BẢN (Standard KYC)

### 2.1. Yêu cầu Hồ sơ Pháp lý
Mọi KHDN khi yêu cầu mở tài khoản tại SHB phải cung cấp đủ các chứng từ sau (Bản chính hoặc Bản sao y công chứng không quá 06 tháng):
- Giấy chứng nhận Đăng ký doanh nghiệp/Đăng ký kinh doanh (ĐKKD).
- Quyết định bổ nhiệm/Hợp đồng lao động của Kế toán trưởng (nếu có).
- CCCD/Hộ chiếu còn hiệu lực của Người đại diện theo pháp luật (NĐĐPL) và Kế toán trưởng.
- Điều lệ công ty (có chữ ký giáp lai của NĐĐPL).

### 2.2. Nhận diện Chủ sở hữu hưởng lợi (Ultimate Beneficial Owner - UBO)
Ngân hàng bắt buộc phải xác định được cá nhân thực tế sở hữu chi phối doanh nghiệp (Nắm giữ trực tiếp hoặc gián tiếp từ 25% vốn điều lệ trở lên).
- **Yêu cầu:** Doanh nghiệp phải điền "Bản khai thông tin Chủ sở hữu hưởng lợi" và cung cấp CCCD/Hộ chiếu của các cá nhân UBO.
- **Xử lý ngoại lệ:** Nếu không có cổ đông nào nắm giữ trên 25%, NĐĐPL sẽ được coi là UBO mặc định.

## 3. THẨM ĐỊNH CHUYÊN SÂU (Enhanced Due Diligence - EDD)
Quy trình EDD tự động kích hoạt đối với các Doanh nghiệp thuộc "Nhóm Rủi ro Cao" (High Risk), bao gồm:
1. Doanh nghiệp có vốn đầu tư nước ngoài (FDI) nhưng UBO đến từ các quốc gia thuộc "Danh sách xám/Danh sách đen" của FATF.
2. Doanh nghiệp hoạt động trong lĩnh vực: Kinh doanh vàng, tiền ảo, game online, sàn giao dịch tài chính, hoặc sòng bạc (casino).
3. Doanh nghiệp có sự xuất hiện của "Cá nhân có ảnh hưởng chính trị" (PEP) trong HĐQT hoặc Ban Giám đốc.

**Yêu cầu thêm của EDD:**
- Thẩm định thực tế tại trụ sở làm việc của doanh nghiệp (On-site visit) và chụp ảnh lưu hồ sơ.
- Thu thập Báo cáo tài chính đã kiểm toán.
- Xác minh nguồn gốc tài sản và dòng tiền dự kiến giao dịch qua tài khoản.
- Việc mở tài khoản cho nhóm EDD phải được **Giám đốc Chi nhánh phê duyệt trực tiếp**.

## 4. XỬ LÝ DỮ LIỆU VÀ QUÉT DANH SÁCH (Screening)
Trước khi tạo CIF (Mã khách hàng) trên hệ thống Core Banking, thông tin NĐĐPL, Kế toán trưởng và UBO phải được quét qua hệ thống AML của SHB để đối chiếu với:
- Danh sách cấm cấm vận của Liên Hợp Quốc (UN), OFAC.
- Danh sách cảnh báo rủi ro gian lận nội bộ của SHB.
*Nếu hệ thống cảnh báo "Hit" (Trùng khớp), Giao dịch viên phải lập tức tạm dừng quy trình mở tài khoản và báo cáo cho Bộ phận Tuân thủ (Compliance).*
