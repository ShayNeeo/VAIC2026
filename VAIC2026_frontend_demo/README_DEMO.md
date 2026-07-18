# SHB Opportunity OS — Frontend Demo

Demo giao diện tiếng Việt dành cho RM bán hàng doanh nghiệp. File chính là `app/static/index.html` và không cần cài thư viện frontend.

## Chạy độc lập

```bash
python -m http.server 8080 -d app/static
```

Mở `http://localhost:8080`.

## Gắn vào repository VAIC2026

1. Sao lưu `app/static/index.html` hiện tại.
2. Chép file demo vào đúng đường dẫn `app/static/index.html`.
3. Chạy backend:

```bash
uvicorn app.main:app --reload
```

4. Mở `http://localhost:8000`.

Giao diện tự kiểm tra endpoint `/health`. Nếu backend không có, toàn bộ luồng vẫn chạy bằng dữ liệu mock trong trình duyệt.

## Luồng demo đề xuất

1. Mở **Cơ hội hôm nay**.
2. Chọn **Công ty TNHH Sản xuất ABC**.
3. Giải thích Context Header, fact/source và bốn opportunity độc lập.
4. Mở **Agent trace** và **Bằng chứng**.
5. Chỉ ra Working Capital đang chờ UBO/BCTC trong khi ba nhánh giao dịch vẫn tiếp tục.
6. Bấm **Bổ sung UBO + BCTC** để mô phỏng impact-based resume.
7. Bấm **Duyệt phạm vi hành động**, kiểm tra payload diff và bốn checkbox trách nhiệm.
8. Xác nhận để xem Execution Receipt.
9. Mở **Hiệu suất & kiểm soát** để trình bày góc nhìn Sales Lead.

## Nguyên tắc UX

- RM duyệt một `Decision Brief`, không duyệt “suy nghĩ của AI”.
- Fact, signal, opportunity, action và outcome là các lớp dữ liệu riêng.
- Eligibility và Legal status được hiển thị theo từng opportunity.
- Agent trace và bằng chứng dùng progressive disclosure, không chiếm màn hình chính.
- Không có nút “Approve All” mơ hồ; modal hiển thị payload diff.
- Tất cả hành động trong demo là synthetic và không gửi ra ngoài.

---

## Phiên bản Mobile App / PWA

Gói này đã bổ sung phiên bản mobile-first tại:

```text
mobile/index.html
```

Chạy từ thư mục gốc:

```bash
python -m http.server 8080
```

Mở `http://localhost:8080/mobile/`.

Phiên bản mobile có Opportunity Queue, Decision Brief, Agent Trace, Evidence Bottom Sheet, Action Center, approval payload diff, partial resume và Execution Receipt. Xem hướng dẫn chi tiết tại `mobile/README_MOBILE.md`.
