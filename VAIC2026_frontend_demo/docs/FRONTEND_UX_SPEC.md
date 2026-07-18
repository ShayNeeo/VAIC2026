# Frontend UX Spec — SHB Corporate Opportunity OS

## Người dùng chính

RM khách hàng doanh nghiệp cần chuyển một yêu cầu đa nhu cầu thành các opportunity có owner, trạng thái, bằng chứng và next-best-action.

## Đối tượng RM phê duyệt

`Decision Brief` gồm:

- Context doanh nghiệp/case/RM/quyền.
- Cách hệ thống hiểu nhu cầu và các fact có nguồn.
- Danh sách opportunity độc lập.
- Product fit, Legal status và evidence theo từng opportunity.
- Missing information và next-best-action.
- Payload diff của CRM/task/email draft.
- Xác nhận trách nhiệm của RM trước khi executor hoạt động.

## Màn hình

1. **Opportunity Queue** — ưu tiên theo SLA, readiness và next action.
2. **Case Decision Workspace** — giao diện chính ba cột.
3. **Approval Modal** — payload diff, scope và explicit confirmation.
4. **Execution Receipt** — kết quả idempotent và audit timeline.
5. **Management View** — funnel, productivity và control metrics.

## Màu và trạng thái

- Xanh lá: có thể tiếp tục.
- Vàng: thiếu thông tin.
- Đỏ: bị chặn hoặc phải review.
- Xanh dương: thông tin, context, AI suggestion.
- Cam: CTA chính và nhận diện sản phẩm demo.

## Font

Sử dụng font stack không phụ thuộc CDN:

`Inter, SF Pro Text, Segoe UI, Roboto, Helvetica, Arial, sans-serif`.

## Integration contract tối thiểu

UI hiện tại có thể ánh xạ từ `SharedCaseState`:

- `company_profile` → Context panel.
- `customer_request` → Need summary.
- `product_result.recommended_bundle.products` → Opportunity cards.
- `legal_result.per_product_eligibility` → Branch status.
- `operations_result` → Action Center.
- `evidences` → Evidence drawer.
- `execution_plan` + `audit_log` → Agent trace.
- `approval_status` + `final_status` → Approval/Receipt.

---

# Mobile UX Addendum

Phiên bản mobile không thu nhỏ dashboard desktop. Nó sử dụng mô hình **task-first**:

1. Bottom navigation gồm Trang chủ, Case, Hành động và Nhật ký.
2. Opportunity Queue dùng card và horizontal metric carousel.
3. Decision Brief giữ context, fact và opportunity trong một luồng cuộn dọc.
4. Evidence, score detail và agent trace mở bằng bottom sheet để không mất context.
5. Nút Duyệt được cố định phía trên bottom navigation khi ở Case Workspace.
6. Approval là bottom sheet gần toàn màn hình, có payload diff và bốn xác nhận trách nhiệm.
7. PWA shell cho phép cài đặt và cache giao diện demo qua HTTP/HTTPS.

Mục tiêu sử dụng: RM duyệt nhanh sau cuộc họp hoặc khi đang di chuyển; các tác vụ nhập liệu dài và quản trị sâu vẫn ưu tiên desktop.
