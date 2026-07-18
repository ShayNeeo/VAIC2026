# QA Report — Frontend Demo

## Kiểm tra tự động bằng Chromium/Playwright

- HTML tải thành công bằng `page.set_content`.
- Không phát hiện JavaScript `pageerror` hoặc console error.
- Opportunity Queue render đủ 6 case.
- Điều hướng sang Decision Brief hoạt động.
- Decision Brief render đủ 4 opportunity card.
- Approval modal mở đúng và render payload diff.
- Responsive CSS có breakpoint 1180px, 880px và 560px.

## Acceptance flow cần kiểm tra thủ công

1. Lọc/search Opportunity Queue.
2. Chọn/bỏ chọn từng opportunity và quan sát Action Center cập nhật.
3. Mở bằng chứng và cấu phần điểm.
4. Mở Agent Trace.
5. Bổ sung UBO + BCTC; Working Capital đổi sang “Sẵn sàng chuyển thẩm định”.
6. Mở approval modal; nút xác nhận chỉ mở khi đủ bốn checkbox.
7. Thực thi và kiểm tra Execution Receipt.
8. Mở màn hình Hiệu suất & kiểm soát.

## Hạn chế

- Dữ liệu trong trình duyệt là mock; chưa ánh xạ toàn bộ response API V2.
- Chưa có persistence sau refresh.
- Không có SSO/RBAC thật, DMS/CRM thật hoặc email thật.
- Chưa kiểm thử WCAG bằng scanner tự động; đã thiết kế focus-visible, semantic button/table và contrast ở mức thực dụng.

## Mobile/PWA verification

- Chromium mobile viewport 390×844 rendered successfully.
- No JavaScript console errors or page errors detected.
- Queue contains four demo cases and filters/search render correctly.
- Workspace contains four selectable opportunities.
- Evidence bottom sheet opens with source and section metadata.
- Approval sheet opens; confirm button is disabled until all four responsibility checks are selected.
- Confirming approval navigates to Execution Receipt.
- Adding UBO + BCTC updates the Working Capital branch and missing-document status.
- Screenshots generated in `preview/mobile/`.
