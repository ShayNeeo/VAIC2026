# SHB Opportunity OS — Mobile PWA Demo

Phiên bản mobile-first dành cho RM khách hàng doanh nghiệp. Giao diện được tối ưu cho thao tác nhanh khi RM đang di chuyển, sau cuộc họp khách hàng hoặc cần duyệt payload ngoài bàn làm việc.

## Chạy nhanh

Từ thư mục gốc của gói demo:

```bash
python -m http.server 8080
```

Mở:

```text
http://localhost:8080/mobile/
```

Mở file `mobile/index.html` trực tiếp vẫn chạy được ở chế độ standalone. PWA/offline cache chỉ hoạt động khi phục vụ qua HTTP/HTTPS.

## Luồng demo 90 giây

1. **Trang chủ:** xem case ưu tiên, SLA và next-best-action.
2. Mở **Công ty ABC** để vào Decision Brief.
3. Kiểm tra context, intent, fact có nguồn và bốn opportunity.
4. Bấm **Bằng chứng** hoặc **Chi tiết** trên opportunity.
5. Mở **Agent trace** từ nút robot.
6. Sang **Hành động** để xem các draft sẽ được tạo.
7. Bấm **Bổ sung UBO + BCTC** để mô phỏng partial resume.
8. Bấm **Duyệt**, xác nhận bốn checkbox và xem Execution Receipt.

## Màn hình

- Opportunity Queue dạng card, tìm kiếm và filter.
- Decision Brief mobile với context card, fact grid và opportunity selection.
- Evidence/detail/agent trace bằng bottom sheet.
- Action Center với task, email draft, dedup và hồ sơ thiếu.
- Approval sheet có payload diff và xác nhận trách nhiệm.
- Execution Receipt và audit timeline.

## PWA

- `manifest.webmanifest`: metadata cài đặt.
- `sw.js`: cache shell để demo offline sau lần tải đầu.
- `assets/icon-192.png`, `assets/icon-512.png`: icon cài đặt.

## Giới hạn

- Dữ liệu và policy là synthetic.
- Các action chỉ mô phỏng frontend; chưa gọi API thật.
- Không phải ứng dụng production và không thực hiện quyết định tín dụng.
