# 00 — AI Build Protocol

## 1. Mục đích

Đảm bảo nhiều phiên AI có thể code cùng hệ thống mà không lệch contract, lặp việc hoặc báo hoàn thành khi chưa kiểm thử.

## 2. Protocol bắt buộc

### Trước khi code

1. Đọc `INDEX.md` và `PROGRESS.md`.
2. Chọn đúng một task ID hoặc một nhóm task có dependency đã Done.
3. Đọc contract machine-readable liên quan.
4. Đọc toàn bộ module plan liên quan.
5. Kiểm tra code hiện tại và tests; không giả định code chưa tồn tại.
6. Ghi task `In Progress` vào `PROGRESS.md`.

### Trong khi code

- Không sửa module ngoài scope nếu không cần cho dependency.
- Không xóa hoặc ghi đè thay đổi của người dùng.
- Không thêm secrets hoặc dữ liệu SHB thật vào repo.
- Mọi dữ liệu demo phải gắn `SYNTHETIC DEMO DATA`.
- Mọi state transition phải dùng enum contract.
- Mọi write action cần idempotency key.
- Mọi LLM output phải validate schema; không parse text tự do.
- Mọi source-derived fact phải có provenance.
- Mọi retry phải có max attempts và chỉ dùng khi an toàn.
- Không log raw prompt/document chứa PII.

### Trước khi báo Done

1. Chạy unit tests của module.
2. Chạy contract tests.
3. Chạy integration tests với dependency upstream/downstream.
4. Chạy security tests nếu liên quan tool/data/action.
5. Kiểm tra acceptance trong module 15.
6. Cập nhật `PROGRESS.md` với command và kết quả thật.
7. Ghi deviation nếu code khác plan.
8. Báo rõ phần chưa kiểm chứng.

## 3. Quy ước code

| Hạng mục | Quy ước |
|---|---|
| Python | 3.11+; type hints; Pydantic v2 |
| API | FastAPI; version prefix `/api/v2` |
| Models | `app/schemas/` hoặc `app/domain/`; không duplicate |
| Services | Pure business logic, không phụ thuộc HTTP |
| Adapters | CRM/SSO/vector/email nằm trong `app/integrations/` |
| Workflow nodes | Input/output là SharedCaseState hoặc typed command |
| Errors | Typed errors + stable error code |
| Logging | Structured JSON; sanitize trước log |
| Tests | Arrange–Act–Assert; deterministic; không cần network mặc định |

## 4. Module boundaries

- Context module chỉ thu thập/chuẩn hóa context; không đề xuất sản phẩm.
- Intent module chỉ hiểu mục tiêu/entity; không gọi CRM write.
- Product module không kết luận pháp lý.
- Eligibility module không tạo case/task.
- Operations chỉ chuẩn bị artifact draft.
- Approval chỉ xác thực ý chí/quyền của RM.
- Executor chỉ thực thi payload đã duyệt, không tự chỉnh payload.
- UI không chứa business rule quan trọng.

## 5. Contract change protocol

Khi cần đổi schema:

1. Tăng `schema_version` theo semantic versioning.
2. Cập nhật JSON schema.
3. Cập nhật migration/compatibility adapter.
4. Cập nhật contract tests.
5. Cập nhật module bị ảnh hưởng.
6. Cập nhật API examples.
7. Ghi decision/deviation trong `PROGRESS.md`.

Breaking change không được gộp âm thầm với feature khác.

## 6. Definition of evidence

Một task chỉ có evidence khi có ít nhất:

- File tạo/sửa.
- Test command đã chạy.
- Kết quả pass/fail thật.
- Sample input/output hoặc API response.
- Known limitations.

Không dùng “dự kiến pass”, “có vẻ chạy” hoặc “production-ready” nếu chưa có bằng chứng.

