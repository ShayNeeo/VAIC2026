# Specialist Review — Focused Audit (rút gọn)

Phạm vi do người dùng chọn tường minh: **tự thiết kế rubric rút gọn**,
tập trung đúng vào phần đã thay đổi qua 3 vòng gần nhất — specialist
review, `human_review_allowed`, multi-domain block, `expected_case_version`,
`OperationalReadinessChecklist`, notification idempotency, và fix
`V2Repository` singleton — **không** audit lại toàn bộ hệ thống từ đầu
(việc đó đã có ở `docs/ROLE_AWARE_REPO_VERIFICATION_REPORT.md` và
`docs/EMPLOYEE_ROLE_DESIGN_EVALUATION_REPORT.md`).

Nguyên tắc giữ nguyên từ các audit trước: read-only (không sửa code khi
đang audit — mọi phát hiện dưới đây được ghi lại, không tự ý vá), mọi
khẳng định có bằng chứng thật (HTTP response thật, không suy đoán), không
"tự chấm bài mình" bằng cách chạy lại đúng bộ test đã viết — phần xác
minh độc lập (mục 2) dùng kịch bản **mới**, engine thật, không dùng lại
helper `_seed_pending_review_case()` mà 29 test kia đều dựa vào.

## 1. Tổng điểm (thang rút gọn 50, không phải 100)

```text
FOCUSED AUDIT SCORE: 41 / 50
CLASSIFICATION: Vững về thiết kế và an toàn, có 1 bug thật (không phải do
                 3 vòng vừa rồi gây ra) làm giảm giá trị thực dụng của
                 tính năng "human_review_allowed" trong luồng RM thông
                 thường.
CONFIDENCE: HIGH — dựa trên kịch bản HTTP thật qua pipeline thật, không
             chỉ đọc code hay chạy lại test cũ.
```

| Hạng mục | Điểm | /10 |
| --- | --- | --- |
| Đóng gap role design (so với Top 5 gap của audit trước) | 8 | 10 |
| Đúng đắn end-to-end (pipeline thật → specialist review → approve → execute) | 6 | 10 |
| Bảo mật/authorization (probe độc lập) | 9 | 10 |
| An toàn hồi quy (regression) | 10 | 10 |
| Trung thực bằng chứng trong 3 báo cáo trước | 8 | 10 |

Không có hard cap nào bị kích hoạt (không tìm thấy: role tự khai từ
client, bỏ qua customer scope, propose+approve+execute rủi ro cao bởi một
role, dữ liệu cá nhân bị lộ qua Manager). Điểm bị trừ chủ yếu ở mục 2 (E2E)
vì một bug thật mới phát hiện, không phải vì thiết kế sai.

## 2. Xác minh độc lập qua pipeline thật (không dùng lại test có sẵn)

**Kịch bản:** `POST /api/v2/cases` với message tín dụng thật ("...vay vốn
lưu động...") qua `x-session-id: SESS-ABC` (customer COMP-ABC, dữ liệu
CRM thật trong `enterprise_core.sqlite3`) — chạy toàn bộ
`V2WorkflowEngine.run()` thật: intent extraction → `ComplexityRouter` →
product matching → `EligibilityEngine` → risk gate. Kết quả: case đúng
được route vào `PROD-WORKING-CAPITAL`, dừng ở `pending_information`
(thiếu `business_registration`) — **khớp chính xác** với dữ liệu CRM thật
của COMP-ABC (không có UBO hay tài liệu nào được set sẵn). Xác nhận pipeline
thật hoạt động đúng, không chỉ đúng trên fixture tự dựng.

**Bước tiếp theo dự định:** dùng `PATCH /cases/{id}/context` (endpoint RM
đã có sẵn từ trước, không phải do 3 vòng vừa rồi tạo) để sửa `ubo_status`
sang một giá trị "sai nhưng không phải thiếu" (nhằm tái tạo đúng
kịch bản `RULE-CREDIT-UBO-001` FAILED — rule DUY NHẤT được đánh dấu
`human_review_allowed=true`), rồi đưa case qua toàn bộ luồng specialist
review → RM approve → execute bằng pipeline thật.

### 2.1 Phát hiện: `PATCH /cases/{id}/context` từ chối 4/8 field nó tự khai là cho phép

**Bằng chứng (chạy thật, không suy đoán):**

```text
customer.attributes.cash_flow_status  -> 200 OK
customer.attributes.operating_years   -> 409 CONTEXT_CORRECTION_REJECTED
customer.attributes.has_bad_debt_12m  -> 409 CONTEXT_CORRECTION_REJECTED
customer.attributes.name              -> 409 CONTEXT_CORRECTION_REJECTED
customer.attributes.ubo_status        -> 409 CONTEXT_CORRECTION_REJECTED
```//

`correct_context()` (`app/api/v2/router.py`) tự khai
`allowed_fields = {employees_count, annual_revenue, cash_flow_status,
account_or_unit_count, operating_years, has_bad_debt_12m, ubo_status, name}`
— 8 field. Nhưng `impacted_nodes()` (`app/workflow/impact.py`) chỉ có một
danh sách "4 field đặc biệt" đi thẳng vào `DOWNSTREAM_ELIGIBILITY`
(`employees_count`, `annual_revenue`, `cash_flow_status`,
`account_or_unit_count`); **4 field còn lại** (`operating_years`,
`has_bad_debt_12m`, `ubo_status`, `name`) rơi vào nhánh kiểm tra tiếp theo
`if any("customer" in item ...)`, và vì MỌI field đều có dạng
`customer.attributes.X` (luôn chứa chữ "customer") nên nhánh này luôn
đúng trước khi kịp phân biệt — trả về `FULL` (chạy lại từ
`collect_context`), rồi `V2WorkflowEngine.resume()` từ chối thẳng vì
`collect_context` nằm trong danh sách "phải tạo message mới, không được
resume". Đây là **lỗi có từ trước** (`impact.py`/`router.py` không nằm
trong bất kỳ file nào 3 vòng vừa rồi sửa) — không phải do specialist
review gây ra, nhưng **ảnh hưởng trực tiếp giá trị thực dụng của tính
năng `human_review_allowed`**: đường duy nhất một RM sửa `ubo_status`
theo quy trình chuẩn (PATCH context) để tái hiện đúng case UBO reviewable
hiện đang gãy.

**Vì sao không tự vá:** đây là audit, không phải vòng implementation —
sửa `impact.py`/`router.py` khi đang audit sẽ lặp lại đúng lỗi đã tránh ở
các vòng trước (không tự ý mở rộng phạm vi khi đang ở vai audit). Ghi lại
làm P0 mới, đề xuất ở mục 6.

**Do đó, phần còn lại của kịch bản E2E (specialist review → approve →
execute) chưa được xác minh qua pipeline thật trong audit này** — chỉ có
bằng chứng gián tiếp: (a) 29 test trong `test_v2_specialist_review.py` xác
minh đúng luồng này bằng state dựng trực tiếp qua `repo.save_case()`
(cùng dữ liệu `_analysis()` thật sự tạo ra, đọc trực tiếp từ code), và (b)
`RiskGuardrailGate.evaluate()` — nơi tính `human_review_allowed` — đã
được xác minh 24 test đơn vị thật. Đây là **giới hạn thật của audit này**,
không phải một khẳng định "đã kiểm chứng toàn bộ".

## 3. Xác minh bảo mật độc lập (kịch bản mới, không trùng 29 test cũ)

| Probe | Kết quả | Đánh giá |
| --- | --- | --- |
| Specialist gửi thẳng `"human_review_allowed": true` / `"case_status_changed": true` trong body để tự cấp quyền override | `422 extra_forbidden` (Pydantic `extra="forbid"` chặn ngay, chưa chạm logic nghiệp vụ) | **Đúng thiết kế** — không có đường nào client tự gán field server-authoritative |
| Product Specialist đọc `GET .../specialist-reviews` (lịch sử) của case chỉ có Legal Specialist thao tác, cùng customer scope | `200`, thấy đầy đủ `summary`/`findings` nội bộ của Legal | **Phát hiện nhỏ** — xem mục 4 |
| Toàn bộ 17+12 test cũ trong `test_v2_specialist_review.py` | 29 passed (chạy lại độc lập) | Không phát hiện regression |

## 4. Phát hiện nhỏ: lịch sử review hiển thị chéo giữa các subtype specialist

`GET /api/v2/cases/{id}/specialist-reviews` cho phép đọc nếu
`is_owner OR customer_id in identity.customer_scope` — tức **bất kỳ**
specialist nào (Legal/Product/Operations) chia sẻ customer scope đều đọc
được toàn bộ `summary`/`findings` nội bộ specialist khác viết cho case đó,
không giới hạn theo đúng subtype đang thao tác.

**Không xếp vào lỗi nghiêm trọng** vì: (a) `review-context` (endpoint chị
em) đã chủ động chia sẻ `required_reviewer_roles`/`reasons`/`evidences`
cho mọi specialist trong scope theo đúng thiết kế (để họ viết review có
căn cứ) — hành vi ở mục này nhất quán với thiết kế đó, không phải một lỗ
hổng mới; (b) trong demo hiện tại cả 4 persona specialist dùng chung đúng
3 customer_id, nên "customer scope" thực chất không phân biệt được gì.
Vẫn đáng ghi nhận vì nếu sau này customer_scope thật sự khác nhau giữa
các specialist, `findings`/`summary` (có thể chứa nội dung nhạy cảm nội
bộ) sẽ lộ chéo. Đề xuất P1 ở mục 6.

## 5. Đối chiếu lại Top 5 gap của `EMPLOYEE_ROLE_DESIGN_EVALUATION_REPORT.md` (70/100)

| Gap gốc | Trạng thái sau 3 vòng |
| --- | --- |
| 1. Không có endpoint hành động cho Product/Legal/Operations | **Phần lớn đã đóng** — Legal/Product có quyền clear thật (có giới hạn `human_review_allowed`); Operations có `OperationalReadinessChecklist` riêng (không phải case-mutation, nhưng là action surface thật, có audit) |
| 2. Case rủi ro cao không có người xử lý xác định | **Đóng về thiết kế, bị giảm giá trị thực dụng bởi bug mục 2.1** — `required_reviewer_roles` luôn có giá trị (test xác nhận không bao giờ rỗng), nhưng đường RM tạo ra đúng kịch bản UBO reviewable qua quy trình chuẩn (PATCH context) hiện đang gãy |
| 3. Không có đường quay lại RM | **Đóng** — `_notify_rm()` + idempotency, xác nhận bằng test kịch bản 2 specialist hoàn tất gần nhau chỉ tạo 1 work item |
| 4. Employee Context chung một shape cho mọi role | **Chưa đụng tới** — `review-context` (mới) đúng theo role, nhưng `EmployeeContextSnapshot`/`WorkContext` tổng quát vẫn y như audit trước, không nằm trong phạm vi 3 vòng vừa rồi |
| 5. Auditor/Admin chỉ có trên giấy | **Không đổi, đúng như đề xuất** — vẫn chưa cần xây, không phải thiếu sót |

## 6. Đề xuất tiếp theo, theo mức độ ưu tiên

```text
P0 — Sửa impact.py: đưa operating_years/has_bad_debt_12m/ubo_status/name
     vào cùng nhóm DOWNSTREAM_ELIGIBILITY như 4 field kia (hoặc đổi thứ
     tự kiểm tra để field-cụ-thể được xét trước field-chứa-"customer"
     chung chung). Không sửa trong audit này (đúng nguyên tắc read-only);
     đây là fix rất nhỏ (đổi 1 điều kiện trong impact.py) nhưng có giá trị
     lớn — hiện đang chặn đúng nửa số field mà app/api/v2/router.py tự
     công bố là "correctable".
P1 — Cân nhắc giới hạn GET .../specialist-reviews theo đúng subtype đang
     xem (hoặc chấp nhận hiện trạng có ghi chú rõ trong tài liệu thiết kế,
     nếu cross-specialist visibility là chủ đích).
P2 — Sau khi P0 được sửa, chạy lại đúng kịch bản E2E ở mục 2 để xác nhận
     specialist review → approve → execute hoạt động trên state do pipeline
     thật tạo ra (không phải state dựng tay) — đóng nốt giới hạn đã nêu ở
     mục 2.1.
P3 — Nối Flutter UI, như đã thống nhất từ trước.
```

## 7. Kết luận

3 vòng vừa rồi (specialist-review action surface, hardening
`human_review_allowed`/`expected_case_version`/`OperationalReadinessChecklist`/
idempotency, và fix `V2Repository` singleton) đều **đúng như báo cáo mô
tả** — không tìm thấy khẳng định sai sự thật nào khi đối chiếu độc lập.
Thiết kế an toàn (không có cách nào spoof quyền override qua request
body; multi-domain block, blocked-decision, scope, capability đều đúng
như test đã chứng minh). Phát hiện thật duy nhất đáng chú ý là một **bug
có từ trước** ở `impact.py`, không phải do 3 vòng vừa rồi gây ra, nhưng
lại là đúng mắt xích còn thiếu để tính năng `human_review_allowed` có ý
nghĩa thực dụng trọn vẹn trong một luồng RM thông thường.
