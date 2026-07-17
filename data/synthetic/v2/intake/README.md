# Bộ hồ sơ intake synthetic

Bộ dữ liệu này chỉ dùng để demo luồng E2E. Không chứa dữ liệu khách hàng thật.

- `01_business_registration.txt`: đăng ký doanh nghiệp, MST, quy mô, thời gian hoạt động.
- `02_meeting_note.txt`: nhu cầu đa sản phẩm và pain point.
- `03_payment_process.txt`: quy trình thu/chi và ERP.
- `04_financial_statements.txt`: BCTC năm gần nhất để gỡ rule tín dụng.
- `05_ubo_information.txt`: xác minh UBO để gỡ rule KYC.

Case `missing_documents` chỉ nạp ba file đầu. Case `full_bundle` nạp cả năm file.
