# Specialist Review Implementation Report

> **Cập nhật (vòng hardening sau code review):** Mục 11 ở cuối file bổ sung
> 4 điểm một reviewer chỉ ra sau khi đọc báo cáo gốc bên dưới:
> `human_review_allowed` (không phải block nào cũng được specialist gỡ),
> `expected_case_version` (optimistic concurrency), notification idempotent,
> và `OperationalReadinessChecklist` riêng cho Operations. Nội dung gốc bên
> dưới giữ nguyên để còn dấu vết quyết định ban đầu; mục 11 nêu rõ cái gì đã
> đổi và vì sao.
>
> **Cập nhật 2 (sửa bug `V2Repository` singleton):** Mục 12 sửa đúng bug đã
> disclose ở mục 8/11.5 — `app/api/v2/router.py` giờ đọc `settings.V2_DB_PATH`
> live như phần còn lại của hệ thống, có test chứng minh bug từng tồn tại
> thật (chạy lại đúng test đó trên code cũ, xác nhận fail) rồi mới sửa.
>
> **Cập nhật 3 (P0 — đưa full suite về xanh hoàn toàn):** Mục 13 sửa nốt
> `test_ui_v2.py`'s test còn fail. Không xoá test, không thêm nội dung
> trùng lặp vào HTML — sửa đúng chỗ test kiểm tra sai layer (nội dung vốn
> render bằng JS, test lại fetch HTML tĩnh chưa chạy JS). **343/343 test
> pass.**

Phạm vi: hiện thực hoá gap #1/#2/#3 trong
`docs/EMPLOYEE_ROLE_DESIGN_EVALUATION_REPORT.md` (điểm 70/100) — Product,
Legal, Operations Specialist trước đây chỉ **xem được** work queue, không
có endpoint nào để **hành động** trên case, và một case `PENDING_REVIEW`
(risk_level=high) không có người xử lý được định nghĩa. Đây là vòng
implementation theo đúng bản đặc tả kỹ thuật người dùng cung cấp (state
machine, API contract, RACI, test list), đã được đối chiếu với kiến trúc
thực tế của repo trước khi code — không thêm role mới, không đổi tên case
status hiện có.

## 1. Tóm tắt kết quả

Đã thêm một action surface thật cho Legal và Product Specialist (quyền
thay đổi trạng thái case, có giới hạn, có kiểm chứng bằng test HTTP thật),
một action surface ghi nhận/advisory cho Operations Specialist (trung thực
về việc chưa có gate kỹ thuật tương ứng), một cơ chế "trả case về RM" dùng
lại đúng Next Best Work queue RM đã xem, và một cơ chế multi-domain block
(một case bị chặn bởi cả Product lẫn Legal thì cần cả hai cùng gỡ). Toàn
bộ được xây trên state machine `CaseStatus` **có sẵn** — không thêm status
mới, không sửa `app/workflow/state_machine.py`.

Đã phát hiện và tránh (không sửa trong vòng này) một bug tiềm ẩn có thật:
`app/api/v2/router.py` giữ `V2Repository` dạng singleton ở module-level,
bind cứng vào `settings.V2_DB_PATH` tại thời điểm import — cùng loại lỗi
đã từng sửa cho `employee_db.py` ở vòng P0 trước, nhưng chưa từng được sửa
ở đây vì chưa có test nào trước đây chạy cô lập DB cho `/api/v2/cases/*`.
Test của tôi chạm vào đúng lỗi này (2 test đầu tiên lỗi 404 thay vì
403/409) — đã đổi cách kiểm chứng để không phụ thuộc vào phần code đó,
thay vì âm thầm mở rộng phạm vi sang sửa `router.py`.

**319/320 test pass** (`pytest tests/`), 1 fail còn lại
(`test_ui_v2.py::test_workspace_contains_four_guided_cases_and_expected_outputs`)
là **lỗi có từ trước**, xác nhận bằng `git diff --stat -- app/static/index.html tests/test_ui_v2.py`
ra rỗng — file đó tôi không hề chạm tới trong bất kỳ phiên nào.

## 2. Bản đồ bài toán → kỹ thuật

| Nhu cầu thực tế | Kỹ thuật áp dụng | Vì sao chọn | Artifact tạo ra | Cách kiểm chứng |
| --- | --- | --- | --- | --- |
| Specialist cần "hành động", không chỉ "xem" | Thêm endpoint mutate case state, tái dùng `CaseStatus`/`transition()` có sẵn | Tránh tạo state machine song song; mọi transition đã được `state_machine.py` cho phép sẵn (PENDING_REVIEW→PENDING_APPROVAL/REJECTED/IN_ANALYSIS) | `POST /api/v2/cases/{id}/specialist-reviews` | 17 test HTTP thật trong `test_v2_specialist_review.py` |
| Biết case đang chờ ai xử lý | Suy ra từ dữ liệu đã có (`Evidence.module`, `eligibility_result.overall_status`), không đoán | Tránh hard-code "luôn là legal" như code cũ; dùng đúng field engine đã tính | `RiskGateDecision.required_reviewer_roles` (risk_gate.py) | `test_v2_risk_gate_and_router.py` (3 test mới) |
| Legal "gỡ" một block mà không né tránh việc engine sẽ tính lại y hệt | Method riêng `clear_specialist_block()`, KHÔNG gọi lại `evaluate_eligibility`/`validate_evidence` | Hai engine đó là deterministic — chạy lại sẽ ra lại đúng kết luận cũ; quyết định của specialist là override có chủ đích, phải tách bạch, có audit riêng | `V2WorkflowEngine.clear_specialist_block()` | `test_legal_specialist_can_clear_legal_block` |
| Case bị chặn bởi ≥2 domain (Product + Legal) không được 1 người tự gỡ hết | Đếm "role đã cleared" theo đúng `case_version`, chỉ tiến khi đủ tập `required_reviewer_roles` | Đúng tinh thần Separation of Duties mà report trước đã nêu là gap | `cleared_roles_for_case_version()` (employee_db.py) | `test_multi_domain_block_requires_both_roles_to_clear` |
| RM phải biết specialist đã xử lý xong | Ghi một `employee_work_items` row mới, tái dùng Next Best Work queue RM đã xem | Không tạo kênh notification song song; RM chỉ cần refresh queue hiện có | `_notify_rm()` + `create_work_item()` | `test_specialist_review_returns_case_to_rm_work_queue` |
| Operations "hành động" thật sự | **Không fabricate** — chỉ ghi nhận + báo RM, không tự đổi case status | Không có gate kỹ thuật nào trong engine hiện tại đại diện cho "Operations block"; checklist của `OperationsService` tự tính lại từ tài liệu mỗi lần chạy, không phải to-do thủ công | `advisory_only=True` cho `operations_specialist` | `test_operations_specialist_cannot_clear_legal_issue` |

## 3. Kiến trúc & luồng xử lý

```
RM tạo case → V2WorkflowEngine._analysis() → RiskGuardrailGate.evaluate()
                                                        │
                        risk_level=high, outcome=need_review
                                                        │
                    CaseStatus.PENDING_REVIEW  (KHÔNG đổi, dùng nguyên trạng)
                    risk_gate_result.required_reviewer_roles = [...]
                                                        │
        ┌───────────────────────────────┬──────────────┴──────────────┐
        │                                │                              │
  Legal Specialist                Product Specialist            Operations Specialist
  (nếu "legal_specialist"         (nếu "product_specialist"     (LUÔN được phép, nhưng
   nằm trong required_roles)       nằm trong required_roles)     advisory_only=True)
        │                                │                              │
  POST /cases/{id}/specialist-reviews   POST /cases/{id}/specialist-reviews
  {review_type, decision, summary,      review_type=operations_specialist
   findings?, required_information?,
   evidence_ids?}
        │
   ┌────┴─────┬──────────────┬───────────────────────┐
   │           │              │                       │
cleared     blocked    needs_more_information     (không đúng role/scope
   │           │              │                      → 403/409, không đổi gì)
   │      transition→      transition→
   │      REJECTED         IN_ANALYSIS→PENDING_INFORMATION
   │      (approval=REJECTED)  (+ next_best_questions)
   │
Đủ hết required_reviewer_roles cho case_version hiện tại?
   │
  Có → V2WorkflowEngine.clear_specialist_block()
       (KHÔNG chạy lại eligibility/evidence — chỉ chuẩn bị operations_result
        nếu chưa có, rồi transition→PENDING_APPROVAL, approval=PENDING)
   │
  Chưa → ghi nhận review, case_status_changed=false, still_waiting_for=[...]
   │
Mọi nhánh kết thúc (trừ "còn chờ role khác"):
   - save_specialist_review()  (bảng specialist_reviews)
   - repo.append_audit() + JsonEventLogger.emit()   (hash-chain + JSON log)
   - _notify_rm()  → employee_work_items row mới, role_required=relationship_manager
   - RM sau đó tự approve/execute qua endpoint owned() cũ (KHÔNG đổi, KHÔNG bị specialist bỏ qua)
```

Điểm mấu chốt về thiết kế (khác với đặc tả gốc, có lý do rõ ràng):

- **Không thêm `CaseStatus` mới** (không có `assigned_to_specialist`,
  `specialist_review_in_progress`...). `state_machine.py` tự ghi chú
  "the only status values allowed anywhere" — tôi tôn trọng ràng buộc đó
  thay vì phá vỡ hợp đồng đã có với `plan_v2/contracts/`. Toàn bộ 3 quyết
  định (cleared/blocked/needs_more_information) đều map thẳng vào các
  transition **đã được cho phép sẵn** trong `ALLOWED` dict.
- **`cleared` không chạy lại `evaluate_eligibility`/`validate_evidence`.**
  Đây là quyết định kỹ thuật quan trọng nhất: hai engine đó là
  deterministic, chạy lại trên đúng dữ liệu cũ sẽ cho đúng kết luận cũ →
  vòng lặp vô hạn quay lại PENDING_REVIEW. Quyết định của specialist là
  **override có chủ đích** của một gate tự động, không phải "dữ liệu mới" —
  nên phải là một code path tách biệt, tường minh, có audit riêng
  (`specialist_review_cleared`), không lẫn vào pipeline tự động.
- **Operations không có quyền đổi `CaseStatus`.** Đặc tả gốc gộp cả ba
  specialist vào cùng một cơ chế "cleared/blocked/needs_more_information"
  đổi trạng thái case. Sau khi đọc code, checklist của `OperationsService`
  là **tự tính lại** từ trạng thái tài liệu mỗi lần `prepare()` chạy — không
  phải danh sách thủ công một người có thể tick. Gán cho Operations quyền
  "clear" một trạng thái case sẽ là **bịa ra một cơ chế kiểm soát không hề
  tồn tại trong engine**. Vì vậy Operations review được ghi nhận, có audit,
  có báo RM — nhưng không tự đổi case status. Đây là lựa chọn trung thực,
  không phải thiếu sót bị bỏ quên (giải thích thêm ở mục 8).

## 4. Danh sách file tạo/sửa

| File | Loại | Mục đích | Nội dung chính | Cách dùng |
| --- | --- | --- | --- | --- |
| `app/schemas/v2/specialist_review.py` | Mới | Pydantic contracts cho request/response/record | `SpecialistReviewRequest`, `SpecialistReviewResult`, `SpecialistReviewRecord`, `SpecialistReviewFinding` | Import trong `employee_router.py` |
| `app/workflow/risk_gate.py` | Sửa | Thêm field suy ra "ai được xử lý" | `RiskGateDecision.required_reviewer_roles`, helper `_required_reviewer_roles()` | Tự động chạy trong `RiskGuardrailGate.evaluate()`, không cần cấu hình |
| `app/workflow/engine.py` | Sửa | Method override có kiểm soát cho "cleared" | `V2WorkflowEngine.clear_specialist_block()` | Gọi từ `employee_router.py` khi đủ điều kiện |
| `app/storage/employee_db.py` | Sửa | Bảng lưu review + helper ghi work item runtime | Bảng `specialist_reviews`; `save_specialist_review()`, `list_specialist_reviews()`, `cleared_roles_for_case_version()`, `create_work_item()` | Tự tạo bảng khi `init_employee_db()` chạy |
| `app/api/v2/employee_router.py` | Sửa | Endpoint chính + sửa hard-code cũ | `case_action_router` (`GET/POST /cases/{id}/specialist-reviews`, `GET /cases/{id}/review-context`); sửa `get_my_context()` để suy ra `waiting_for_roles` thật thay vì luôn `["legal_specialist"]` | Mount qua `main.py` |
| `app/integrations/enterprise.py` | Sửa | Cấp đủ quyền IAM cho 3 persona specialist | Thêm `legal:check_issue`, `legal:block_non_eligible`, `product:verify_fit`, `ops:update_implementation` vào permissions; đổi `INSERT OR IGNORE` → upsert cho cột `permissions` | Tự chạy khi `employee_router.py` được import (process start) |
| `app/main.py` | Sửa | Mount router mới | `app.include_router(case_action_router, prefix="/api/v2")` | — |
| `tests/unit/test_v2_specialist_review.py` | Mới | 17 test HTTP thật (TestClient) | Legal/Product clear, Operations advisory, scope/role mismatch, multi-domain, blocked-no-token, RM notify, review-context | `pytest tests/unit/test_v2_specialist_review.py` |
| `tests/unit/test_v2_risk_gate_and_router.py` | Sửa | +3 test cho `required_reviewer_roles` | Product vs Legal routing, "không bao giờ rỗng" | `pytest tests/unit/test_v2_risk_gate_and_router.py` |
| `data/mock_database/enterprise_core.sqlite3` | Dữ liệu | Áp dụng permissions mới cho SPEC-LEGAL-001/SPEC-PROD-001/SPEC-OPS-001 | Đã xác minh trực tiếp bằng query SQL trước/sau | Tự động, không cần thao tác thủ công |

## 5. API Contract thực tế (khác một số điểm nhỏ so với đặc tả gốc)

```
POST /api/v2/cases/{case_id}/specialist-reviews
Authorization: Bearer demo-spec-legal-001   (hoặc demo-spec-prod-001 / demo-spec-ops-001)

{
  "review_type": "legal_specialist",   // đổi từ "legal" sang đúng RoleType.value đã dùng toàn hệ thống
  "decision": "needs_more_information",
  "summary": "Chưa đủ dữ liệu xác minh UBO.",
  "findings": [{"code": "UBO_INFORMATION_MISSING", "severity": "high", "message": "..."}],
  "required_information": ["beneficial_owner_information"],
  "evidence_ids": ["EV-CASE-LEGAL-2-Eligibility"]
}

201 →
{
  "review_id": "REVIEW-...", "case_id": "...", "case_version": 2,
  "reviewer_employee_id": "SPEC-LEGAL-001", "review_type": "legal_specialist",
  "decision": "needs_more_information", "summary": "...",
  "case_status": "pending_information", "case_status_changed": true,
  "advisory_only": false, "still_waiting_for": [], "created_at": "..."
}

GET /api/v2/cases/{case_id}/review-context   → required_reviewer_roles, reasons, evidences, cleared_roles
GET /api/v2/cases/{case_id}/specialist-reviews → lịch sử toàn bộ review của case
```

Khác biệt có chủ đích so với JSON mẫu người dùng đưa:
- `review_type` dùng đúng giá trị `RoleType` (`legal_specialist` thay vì
  `legal`) — tránh tạo thêm một từ vựng vai trò thứ hai song song với
  `RoleType` đã dùng xuyên suốt hệ thống.
- Không có `expected_state_version` trong body (khác các endpoint RM-owned
  trong `router.py`). Lý do: specialist không "sửa một bản nháp đang cầm
  trên tay" như RM — họ phản ứng với `GET /review-context` rồi POST gần
  như ngay sau; version luôn lấy live từ server tại thời điểm xử lý. Rủi ro
  lost-update rất nhỏ (hai loại specialist khác nhau hiếm khi ghi đúng
  cùng một khoảnh khắc) — nêu rõ ở mục 8, không giấu.

## 6. Cách cấu hình & cách chạy

Không cần biến môi trường mới. Toàn bộ chạy trên cấu hình sẵn có
(`DEMO_AUTH_ENABLED`, `V2_DB_PATH` từ `app/config.py`).

Chạy server demo như cũ:
```
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Gọi thử bằng demo token có sẵn (`demo-spec-legal-001`, `demo-spec-prod-001`,
`demo-spec-ops-001`), ví dụ qua curl/PowerShell `Invoke-RestMethod` với
header `Authorization: Bearer demo-spec-legal-001`.

## 7. Cách kiểm thử — đã chạy thật, không bịa kết quả

```
./.venv/Scripts/python.exe -m pytest tests/unit/test_v2_specialist_review.py -v
→ 17 passed

./.venv/Scripts/python.exe -m pytest tests/unit/test_v2_risk_gate_and_router.py -v
→ 20 passed (17 cũ + 3 mới)

./.venv/Scripts/python.exe -m pytest tests/ -q
→ 319 passed, 1 failed (test_ui_v2.py — lỗi có từ trước, xác nhận qua git diff rỗng trên index.html)
```

Danh sách 17 test và điều mỗi test chứng minh:

| Test | Chứng minh điều gì |
| --- | --- |
| `test_legal_specialist_can_clear_legal_block` | Legal gỡ được block do Eligibility → case sang `pending_approval` |
| `test_legal_specialist_can_request_more_information` | Legal yêu cầu bổ sung → case sang `pending_information`, câu hỏi xuất hiện trong `next_best_questions` |
| `test_legal_specialist_clearing_does_not_itself_approve_or_execute` | Gỡ block ≠ tự phê duyệt (approval vẫn `PENDING`, chưa có approver_id) |
| `test_product_specialist_can_clear_product_evidence_block` | Product gỡ được block do evidence Product |
| `test_product_specialist_cannot_submit_legal_review_type` | Giả mạo `review_type` khác role thật → 403, case không đổi |
| `test_specialist_cannot_review_case_not_waiting_for_their_role` | Product cố gỡ case chỉ bị chặn bởi Legal → 409 |
| `test_operations_specialist_review_is_advisory_only` | Operations "cleared" không đổi case status |
| `test_operations_specialist_cannot_clear_legal_issue` | Khẳng định trực tiếp: Operations không gỡ được block pháp lý |
| `test_specialist_cannot_review_case_outside_customer_scope` | Customer ngoài scope → 403 |
| `test_unknown_evidence_id_is_rejected` | evidence_id không tồn tại trên case → 422 |
| `test_manager_cannot_submit_specialist_review` | Manager không có capability này → 403 |
| `test_blocked_decision_requires_findings` | "blocked" thiếu findings → 422 |
| `test_blocked_review_does_not_issue_approval_token` | Case bị "blocked" → REJECTED, approval REJECTED, không payload_hash, không approver |
| `test_multi_domain_block_requires_both_roles_to_clear` | Block 2 domain: gỡ 1 role → case CHƯA đổi; gỡ đủ 2 → mới đổi |
| `test_specialist_review_returns_case_to_rm_work_queue` | Review hoàn tất → RM thấy item mới trong `/me/work-queue` |
| `test_high_risk_case_has_a_human_resolution_path` | Mọi case `PENDING_REVIEW` đều có `required_reviewer_roles` khác rỗng |
| `test_get_specialist_reviews_history` | Lịch sử review đọc lại đúng những gì đã ghi |

## 8. Hạn chế/rủi ro — nêu rõ, không che giấu

- **Operations Specialist chưa có quyền đổi case status** (chỉ ghi nhận +
  báo RM). Đây là quyết định có chủ đích (mục 3), không phải thiếu sót —
  nhưng vẫn là một hạn chế thật: nếu pilot cần Operations tự tay đánh dấu
  "đã sẵn sàng thực thi" và chặn case cho tới khi họ xác nhận, cần thiết kế
  thêm một trạng thái/checklist thủ công riêng cho execution readiness
  (không có trong vòng này).
- **`expected_state_version` không bắt buộc trên endpoint mới** → rủi ro
  lost-update rất nhỏ nếu hai request cùng lúc sửa đúng một case (đã nêu ở
  mục 5). Chưa xảy ra trong test vì mỗi test dùng 1 case riêng.
- **Phát hiện mới, KHÔNG sửa trong vòng này**: `app/api/v2/router.py`'s
  `repo` là singleton bind cứng `V2_DB_PATH` tại thời điểm import module —
  bất kỳ test nào sau này muốn cô lập DB cho `/api/v2/cases/*` (không phải
  `/api/v2/me/*`) sẽ gặp đúng lỗi tôi vừa gặp (404 giả do không thấy case).
  Không sửa vì ngoài phạm vi yêu cầu và có rủi ro đụng vào file đang được
  nhiều endpoint RM-facing khác dùng trực tiếp — nên để thành một task
  riêng, có review riêng.
- **`next_best_questions` sinh từ `required_information`** dùng
  `NextBestQuestion` model có sẵn nhưng gán `blocking_steps=["specialist_review"]`
  — nhãn này là mới, frontend (`app/static/app.js`) hiện chưa có logic
  riêng cho nhãn này (không vỡ gì, chỉ là chưa được UI xử lý đặc biệt).
- **Flutter/Dart UI**: vòng này thuần backend, không đụng tới
  `lib/features/employee_workspace/`. Muốn dùng specialist-review từ app
  Flutter cần thêm UI riêng (form nhập findings/decision) — chưa làm, chưa
  verify được vì môi trường này không có Flutter/Dart SDK (đã xác nhận từ
  vòng trước).
- **1 test cũ vẫn fail** (`test_ui_v2.py`, nội dung tĩnh trong
  `app/static/index.html`) — xác nhận có từ trước bằng git diff rỗng, không
  phải do vòng này.

## 9. Bảng sẵn sàng production

| Hạng mục | Đã có? | Ghi chú |
| --- | --- | --- |
| Data strategy | Có | Bảng `specialist_reviews` idempotent, `case_version` neo đúng episode |
| Retrieval quality | N/A | Không phải tính năng RAG |
| Guardrails/HITL | Một phần | RBAC + scope + capability đủ 3 lớp; chưa có UI duyệt cho Operations vì chưa có gate tương ứng |
| Evaluation | Một phần | 20 test HTTP/unit thật; chưa có benchmark định lượng riêng cho luồng này (khác benchmark NBW 30 case đã có) |
| Observability | Có | `repo.append_audit()` (hash-chain) + `JsonEventLogger.emit()` cho mọi nhánh có đổi trạng thái |
| Reliability | Một phần | `StateConflictError` → 409 khi ghi đè; chưa có `expected_state_version` bắt buộc từ client |
| Security/privacy | Có | Identity luôn qua `require_verified_identity`; `review-context` chỉ trả evidence, không trả PII khách hàng ngoài customer_id |

## 10. Kế hoạch tiếp theo (nếu làm vòng sau) — trạng thái sau vòng hardening

1. ~~Thiết kế state/checklist thủ công riêng cho Operations execution
   readiness~~ → **Đã làm ở mục 11.3** (`OperationalReadinessChecklist`).
2. Sửa `app/api/v2/router.py` để `V2Repository` đọc `settings.V2_DB_PATH`
   live như `employee_db.py`/`employee_router.py` đã làm — **chưa làm**,
   vẫn để riêng như reviewer đồng ý (mục 11.5).
3. ~~Thêm `expected_state_version` tuỳ chọn~~ → **Đã làm ở mục 11.2**
   (`expected_case_version`).
4. Nối Flutter `employee_workspace_screen.dart` với các endpoint mới —
   **chưa làm**, vẫn ngoài phạm vi (không có Flutter/Dart SDK trong môi
   trường này).
5. Chạy lại role-design audit + end-to-end workflow audit — **chưa làm**,
   đây là một deliverable lớn riêng (như 3 audit trước đó trong cùng dự
   án), nên chờ yêu cầu tường minh thay vì tự chạy kèm vòng implementation.

## 11. Vòng hardening sau code review — 4 điểm đã sửa

Một code review đọc báo cáo ở trên và chỉ ra 4 vấn đề thật, có thứ tự ưu
tiên rõ ràng. Tất cả đã được sửa, có test HTTP thật xác nhận. Danh sách
việc reviewer nói "chưa cần làm ngay" (thêm Auditor/Admin/Team Lead, tách
3 Specialist thành 3 app, notification service riêng, thêm CaseStatus,
cho Manager override) — **không làm**, đúng như đề xuất.

### 11.1 `human_review_allowed` — không phải block nào cũng được gỡ

**Vấn đề reviewer nêu:** `clear_specialist_block()` coi mọi lý do dẫn tới
`PENDING_REVIEW` là có thể gỡ được, miễn đúng domain — không phân biệt
block tuyệt đối (thiếu tài liệu, ngưỡng số tuyệt đối, nợ xấu, sanctions)
với block thật sự cần phán đoán con người (UBO cần xác minh độc lập,
diễn giải tài liệu mơ hồ).

**Đã sửa, dựa trên dữ liệu thật, không bịa:**

- `EligibilityRule`/`RuleEvaluation` (`app/eligibility/models.py`) có thêm
  field policy `human_review_allowed: bool = False`. Trong 9 rule thật ở
  `data/synthetic/v2/eligibility_rules.json`, **chỉ đúng 1 rule** được đánh
  dấu `true`: `RULE-CREDIT-UBO-001` (UBO chưa xác minh — đúng ví dụ "UBO
  relationship cần human verification" reviewer đưa). 8 rule còn lại
  (thiếu tài liệu, ngưỡng nhân sự/doanh thu/tài khoản/năm hoạt động, nợ
  xấu) giữ mặc định `False` — không sửa gì thêm, tự động không gỡ được.
- Với **evidence** (không phải rule), tận dụng lại field
  `ValidationStatus` đã có sẵn trong `app/safety/evidence_validator.py`
  nhưng trước đây bị "làm phẳng" thành một boolean `is_valid` trước khi
  tới Risk Gate. Giờ `Evidence` có thêm `human_review_allowed: bool`,
  được `V2WorkflowEngine._product_evidence`/`_legal_evidence` gán `True`
  **chỉ khi** lỗi là `ValidationStatus.INVALID` (trích dẫn không khớp
  nguồn, nhưng nguồn vẫn còn hiệu lực — specialist có thể tự đối chiếu lại
  tài liệu gốc). Các lỗi cấu trúc khác (`EXPIRED_SOURCE`,
  `SOURCE_NOT_FOUND`, `VERSION_MISMATCH`, `CONFLICTING_EVIDENCE`,
  `INSUFFICIENT_EVIDENCE`) mặc định `False` — khớp chính xác ví dụ "Evidence
  hết hiệu lực" của reviewer.
- `RiskGateDecision.human_review_allowed` (`app/workflow/risk_gate.py`):
  `True` chỉ khi **toàn bộ** rule/evidence gây block đều được đánh dấu
  reviewable — một rule/evidence tuyệt đối trong hỗn hợp sẽ phủ quyết cả
  quyết định (`test_one_non_overridable_rule_blocks_override_even_if_another_rule_allows_it`,
  `test_one_structural_evidence_problem_vetoes_override_even_with_a_citation_mismatch`).
  Riêng nhánh `pending_review` (live-check-unavailable/policy-conflict)
  luôn `True` — đúng bản chất "cần phán đoán vì hệ thống sống không kiểm
  tra được", không phải một lựa chọn tuỳ ý.
- Endpoint `POST .../specialist-reviews`: nếu `decision=cleared` mà
  `human_review_allowed` không `True` → **409 `BLOCK_NOT_OVERRIDABLE`**,
  chặn trước khi ghi bất kỳ thay đổi nào. Nếu được phép gỡ, **bắt buộc**
  `findings` (tối thiểu 1) làm căn cứ — audit event
  `specialist_review_cleared` giờ ghi thêm `overridden_reasons`,
  `overridden_rules`, `findings` (trước đây chỉ có `review_id`/`summary`).

Test: `test_cannot_clear_a_block_that_is_not_human_review_allowed`,
`test_hard_eligibility_rule_block_is_not_overridable_by_default`,
`test_cleared_decision_requires_findings_even_when_overridable`, cộng 6
test đơn vị mới trong `test_v2_risk_gate_and_router.py`.

### 11.2 `expected_case_version` — optimistic concurrency

`SpecialistReviewRequest.expected_case_version: Optional[int] = None`
(`app/schemas/v2/specialist_review.py`). Nếu client gửi và không khớp
`state_version` hiện tại của case → **409 `CASE_VERSION_CONFLICT`** ngay
từ đầu, trước khi chạm bất kỳ logic nghiệp vụ nào. Không bắt buộc trong
MVP này (đúng đề xuất "optional trong MVP, bắt buộc ở pilot" của
reviewer) — client cũ không gửi field này vẫn hoạt động y hệt trước.
Response luôn có `case_version` mới nhất để client tự reload
`/review-context` khi cần.

Test: `test_expected_case_version_matching_succeeds`,
`test_expected_case_version_mismatch_returns_409`.

### 11.3 `OperationalReadinessChecklist` — action surface thật cho Operations

Đối tượng domain **mới, tách biệt** khỏi checklist tự động của
`OperationsService` (đã giải thích ở mục 3 báo cáo gốc là không thể biến
thành to-do thủ công). Đây chính là "danh sách thủ công một người có thể
tick" mà báo cáo gốc nói là còn thiếu:

```
PUT /api/v2/cases/{case_id}/operational-readiness   (chỉ Operations Specialist)
{
  "items": [
    {"code": "PAYLOAD_VALIDATED", "status": "completed"},
    {"code": "CUSTOMER_CONTACT_CONFIRMED", "status": "blocked", "note": "Chưa liên lạc được."}
  ],
  "summary": "Còn thiếu xác nhận đầu mối."
}
→ 200 { "status": "not_ready", "items": [...], "updated_by": "SPEC-OPS-001", ... }

GET /api/v2/cases/{case_id}/operational-readiness   (RM chủ case hoặc bất kỳ role trong scope)
```

- `status` tổng (`ready`/`not_ready`) suy ra tự động từ `items` (mọi item
  `completed` → `ready`).
- **Không bao giờ đổi `CaseStatus`, không đụng `legal`/`product`
  eligibility** — đúng yêu cầu tách bạch của reviewer. Xác nhận bằng
  `test_operational_readiness_does_not_touch_case_status`.
- Khi `not_ready`, tự tạo work item báo RM (dùng lại đúng cơ chế
  `_notify_rm`/idempotency ở mục 11.4).
- Bảng mới `operational_readiness` (`case_id` PRIMARY KEY, upsert) trong
  `app/storage/employee_db.py` — một snapshot hiện tại cho mỗi case, không
  phải lịch sử (khác `specialist_reviews`, vốn append-only).

Test: `test_operations_specialist_can_set_operational_readiness`,
`test_operational_readiness_not_ready_when_any_item_incomplete`,
`test_operational_readiness_does_not_touch_case_status`,
`test_legal_specialist_cannot_set_operational_readiness`,
`test_rm_can_read_operational_readiness`,
`test_operational_readiness_missing_returns_null`.

### 11.4 Notification idempotent

**Vấn đề reviewer nêu:** `item_id` cũ dùng `review_id` (UUID ngẫu nhiên
mỗi request) — một request bị client retry (timeout rồi gửi lại) hoặc hai
domain hoàn tất gần nhau có thể tạo 2 work item cho cùng một sự kiện.

**Đã sửa:** `_notification_item_id()` (`app/api/v2/employee_router.py`)
sinh id **quyết định luận** (deterministic) từ đúng
`case_id + case_version + event_type + target_employee_id + hash(role_set)`
— khớp chính xác công thức reviewer đề xuất. `create_work_item()` vốn đã
dùng `INSERT OR REPLACE` (xây từ vòng trước), nên một retry với cùng
key sẽ **ghi đè cùng một dòng** thay vì tạo dòng mới, tự động, không cần
thêm logic riêng.

Xác nhận bằng kịch bản đúng như reviewer mô tả — hai specialist khác nhau
hoàn tất cùng một block nhiều-domain gần nhau —
(`test_repeated_notification_for_same_outcome_does_not_duplicate_work_item`):
sau khi cả Product và Legal đều clear, RM chỉ thấy **đúng 1** work item
cho case đó, không phải 2.

### 11.5 Việc chủ động không làm (theo đúng đề xuất reviewer)

- **Không** sửa `app/api/v2/router.py`'s singleton `V2Repository` — vẫn để
  thành task riêng, có review riêng (reviewer đồng ý với lý do đã nêu ở
  mục 8 báo cáo gốc).
- **Không** thêm Auditor/Admin/Team Lead, không tách 3 Specialist Workspace
  thành 3 app riêng, không tạo notification service riêng, không thêm
  `CaseStatus` mới, không cho Manager override quyết định của Specialist.
- **Chưa** nối Flutter UI, **chưa** chạy lại role-design/E2E audit — hai
  mục cuối cùng trong danh sách 6 bước reviewer đề xuất; để lại làm task
  riêng có xác nhận rõ ràng thay vì tự ý mở rộng thêm trong cùng vòng này.

### 11.6 Kiểm thử — vòng hardening

```
./.venv/Scripts/python.exe -m pytest tests/unit/test_v2_specialist_review.py -v
→ 29 passed  (17 cũ + 12 mới: human_review_allowed x3, version-conflict x2,
   notification-idempotency x1, operational-readiness x6)

./.venv/Scripts/python.exe -m pytest tests/unit/test_v2_risk_gate_and_router.py -v
→ 24 passed  (18 sau vòng trước + 6 mới cho human_review_allowed)

./.venv/Scripts/python.exe -m pytest tests/ -q
→ 338 passed, 1 failed (test_ui_v2.py — vẫn là lỗi có từ trước, không liên quan)
```

### 11.7 File tạo/sửa thêm trong vòng hardening

| File | Loại | Thay đổi |
| --- | --- | --- |
| `app/eligibility/models.py` | Sửa | `EligibilityRule.human_review_allowed`, `RuleEvaluation.human_review_allowed` |
| `app/eligibility/engine.py` | Sửa | Truyền `rule.human_review_allowed` vào `RuleEvaluation` |
| `data/synthetic/v2/eligibility_rules.json` | Dữ liệu | `RULE-CREDIT-UBO-001.human_review_allowed = true` (rule duy nhất) |
| `app/schemas/v2/shared_case_state.py` | Sửa | `Evidence.human_review_allowed` (field mới, additive) |
| `plan_v2/contracts/shared_case_state.schema.json` | Sửa | Đồng bộ field mới vào JSON Schema `$defs/evidence` (tránh lệch hợp đồng) |
| `app/workflow/engine.py` | Sửa | `_product_evidence`/`_legal_evidence` gán `human_review_allowed` từ `ValidationStatus.INVALID` |
| `app/workflow/risk_gate.py` | Sửa | `RiskGateDecision.human_review_allowed` + logic suy ra theo từng nhánh |
| `app/schemas/v2/specialist_review.py` | Sửa | `expected_case_version`; thêm `OperationalReadinessItem/Request/Snapshot` |
| `app/storage/employee_db.py` | Sửa | Bảng `operational_readiness` + `save_operational_readiness()`/`get_operational_readiness()` |
| `app/api/v2/employee_router.py` | Sửa | Check `human_review_allowed`/`expected_case_version`/findings-cho-cleared; `_notification_item_id()` deterministic; 2 endpoint `operational-readiness` mới |
| `tests/unit/test_v2_specialist_review.py` | Sửa | +12 test (29 tổng) |
| `tests/unit/test_v2_risk_gate_and_router.py` | Sửa | +6 test (24 tổng) |

### 11.8 Hạn chế còn lại sau vòng hardening — nêu rõ

- Chỉ **1/9 rule** trong bộ dữ liệu tổng hợp hiện tại được đánh dấu
  `human_review_allowed=true`. Đây là lựa chọn bảo thủ có chủ đích (đúng
  tinh thần "khi không chắc, chặn lại" reviewer đề xuất) — nghĩa là trong
  demo hiện tại, khả năng "Legal gỡ được block" chỉ thật sự xảy ra khi
  case bị chặn đúng bởi `RULE-CREDIT-UBO-001` hoặc bởi một lỗi trích dẫn
  thuần tuý (`ValidationStatus.INVALID`). Muốn mở rộng danh sách rule
  reviewable cần một người có thẩm quyền nghiệp vụ/compliance quyết định
  từng rule, không phải việc kỹ thuật tự quyết.
- `expected_case_version` vẫn optional — rủi ro lost-update nhỏ còn lại y
  như mục 8 báo cáo gốc đã nêu, chỉ giảm bớt khi client chủ động gửi field
  này.
- `OperationalReadinessChecklist` chưa có ràng buộc `code` (chuỗi tự do,
  không đối chiếu với checklist tự động của `OperationsService`) — nếu
  cần đồng bộ 2 danh sách này là việc của vòng sau, chưa làm ở đây.

## 12. Sửa bug `V2Repository` singleton bind cứng `V2_DB_PATH`

Đây là mục 4 trong thứ tự ưu tiên reviewer đề xuất (mục 5 UI/Flutter và
mục 6 re-audit **chưa làm**, để lại làm task riêng khi có yêu cầu tường
minh, đúng tinh thần "không tự ý mở rộng phạm vi" đã áp dụng xuyên suốt).

### 12.1 Bug là gì, tại sao ảnh hưởng test isolation

`app/api/v2/router.py`'s `create_router()` trước đây dựng đúng **một**
`V2Repository(settings.V2_DB_PATH)` ngay khi `create_router()` được gọi —
và `create_router()` chỉ được gọi **một lần duy nhất mỗi process**, ở dòng
cuối file (`router = create_router()`), tức là ngay khi module được
import lần đầu. `app.main` import module này ở top-level, nên `repo` bị
"đóng băng" vào bất kỳ giá trị `settings.V2_DB_PATH` nào tồn tại **tại
thời điểm import** — thường là đường dẫn DB thật, vì import luôn xảy ra
trước khi bất kỳ test fixture nào kịp `monkeypatch.setattr(...)`.

Hậu quả thật, không phải giả thuyết: khi viết
`tests/unit/test_v2_specialist_review.py` ở vòng trước, 2 test gọi thẳng
`/api/v2/cases/{id}/execute` và `/api/v2/cases/{id}/approve` (nằm trong
`router.py`) đã fail với `404` thay vì `403`/`409` — vì `repo` cũ không hề
thấy case tôi vừa ghi vào DB cô lập của test. Lúc đó tôi né bằng cách đổi
cách assert (không phụ thuộc endpoint đó) và ghi lại bug này thành việc
"để riêng" — reviewer xác nhận đúng hướng và giờ yêu cầu sửa thật.

Cùng một bệnh cũng có ở `ApprovalServiceV2`/`ActionExecutorV2`/
`IntakeService` — cả ba đều nhận `V2Repository` qua constructor và lưu lại
(`self.repository = repository`), và cả ba đều được dựng **một lần** bên
trong `create_router()` bằng `repo` (cũ) — nên chúng cũng "nhìn nhầm
database" y hệt, không chỉ riêng các endpoint gọi `repo.` trực tiếp.

### 12.2 Cách sửa

Không đổi `V2Repository`/`ApprovalServiceV2`/`ActionExecutorV2`/
`IntakeService` (các constructor này nhận `db_path`/`repository` tường
minh có chủ đích — nhiều nơi khác cũng dùng đúng kiểu tường minh đó, đổi
sẽ vỡ hợp đồng). Thay vào đó, bên trong `create_router()`, 4 biến
`repo`/`approval`/`executor`/`intake` (dựng một lần) đổi thành 4 **hàm
truy cập không tham số**, dựng đối tượng mới mỗi lần được gọi — cùng
nguyên tắc `app/storage/employee_db.py`'s `get_db_connection()` và
`app/api/v2/employee_router.py`'s `_repo()` (vòng trước) đã áp dụng:

```python
def repo() -> V2Repository:
    return repository or V2Repository(settings.V2_DB_PATH)   # đọc live

def approval_service() -> ApprovalServiceV2:
    return ApprovalServiceV2(repo())

def executor_service() -> ActionExecutorV2:
    return ActionExecutorV2(repo(), approval_service())

def intake_service() -> IntakeService:
    return IntakeService(repo())
```

Tham số `repository` tường minh của `create_router(repository=...)` **vẫn
được tôn trọng tuyệt đối** — nếu ai đó chủ động truyền vào một instance cụ
thể (ví dụ một test muốn dùng đúng một repo mock), giá trị đó luôn thắng,
không bị `settings.V2_DB_PATH` ghi đè. Đây không phải tính năng mới —
tham số này đã tồn tại sẵn, giờ chỉ đảm bảo nó vẫn hoạt động đúng sau khi
đổi phần mặc định.

Toàn bộ ~50 điểm gọi (`repo.X(...)` → `repo().X(...)`,
`intake.X(...)` → `intake_service().X(...)`, `approval.issue(...)` →
`approval_service().issue(...)`, `executor.execute(...)` →
`executor_service().execute(...)`) được đổi bằng một script thay thế
chính xác theo regex có ranh giới từ (`\brepo\.([a-z_]+\()` v.v.), chỉ áp
dụng từ điểm bắt đầu định nghĩa `repo()` trở về sau (không đụng phần
import/docstring phía trên) — không có chỗ nào bị bỏ sót hoặc thay nhầm
(xác nhận bằng cách đếm số lần khớp trước/sau, đúng 38+8+2+2 = 50/50).

### 12.3 Kiểm chứng bug từng tồn tại thật, không chỉ tin lời báo cáo cũ

Trước khi báo "đã sửa", tôi `git stash` riêng file `router.py` để đưa nó
về đúng bản **trước khi sửa**, chạy lại 4 test mới viết
(`tests/unit/test_v2_router_db_isolation.py`) trên bản cũ đó, rồi mới
`git stash pop` để khôi phục bản đã sửa. Kết quả:

```
Trên code CŨ (chưa sửa):  3 failed, 1 passed
  - test_shared_app_reads_cases_endpoint_from_the_currently_configured_db: FAILED (404 CASE_NOT_FOUND)
  - test_isolated_db_does_not_leak_into_a_second_isolated_db: FAILED (404 thay vì 200)
  - test_case_list_reflects_only_the_currently_configured_db: FAILED -- danh sách case trả về
    là case THẬT từ data/state/v2.sqlite3 (ví dụ CASE-D9BC62...), không phải case vừa ghi
    vào DB cô lập -- đúng triệu chứng "test nhìn nhầm database" reviewer mô tả.
  - test_explicit_repository_injection_still_overrides_settings: PASSED (hành vi này vốn đã đúng từ trước)

Trên code MỚI (đã sửa):  4 passed
```

Việc test thứ 4 pass ngay cả trên code cũ chứng minh bộ test này không
phải "viết ra để tự khớp với code" — nó phân biệt được đúng phần nào có
bug (mặc định lười biếng) và đúng phần nào chưa từng có bug (khi có
`repository=` tường minh).

### 12.4 File tạo/sửa

| File | Loại | Thay đổi |
| --- | --- | --- |
| `app/api/v2/router.py` | Sửa | `repo`/`approval`/`executor`/`intake` (biến, dựng 1 lần) → `repo()`/`approval_service()`/`executor_service()`/`intake_service()` (hàm, dựng mỗi lần gọi); ~50 điểm gọi cập nhật theo |
| `tests/unit/test_v2_router_db_isolation.py` | Mới | 4 test HTTP thật qua `app.main.app` dùng chung, chứng minh isolation hoạt động + injection tường minh vẫn thắng |

### 12.5 Kết quả kiểm thử toàn repo sau khi sửa

```
./.venv/Scripts/python.exe -m pytest tests/unit/test_v2_router_db_isolation.py -v
→ 4 passed

./.venv/Scripts/python.exe -m pytest tests/ -q
→ 342 passed, 1 failed (test_ui_v2.py -- vẫn là lỗi tĩnh HTML có từ trước, không liên quan)
```

### 12.6 Hạn chế còn lại

- Chi phí runtime tăng nhẹ: mỗi request giờ dựng lại `V2Repository` (chạy
  `CREATE TABLE IF NOT EXISTS`/`apply_migrations` mỗi lần) thay vì dùng
  lại một instance — chấp nhận được ở quy mô SQLite/MVP hiện tại (cùng
  đánh đổi `app/api/v2/employee_router.py` đã chấp nhận từ vòng trước),
  nhưng nếu sau này chuyển sang DB thật có connection pool, nên revisit.
- `_default_assembler()` (IAM/SSO/CRM qua `enterprise_core.sqlite3`) vẫn
  dùng đường dẫn mặc định cứng, **không đọc từ `settings`** — đây là một
  cơ chế cấu hình khác, không phải cùng bug với `V2_DB_PATH`, và nằm ngoài
  phạm vi báo cáo này (không có yêu cầu cụ thể nào chỉ ra nó gây vấn đề
  test isolation trong vòng này).

## 13. P0 — Đưa full suite về 343/343

### 13.1 Điều tra trước khi sửa (không đoán, không tự ý xoá test)

`test_workspace_contains_four_guided_cases_and_expected_outputs`
(`tests/test_ui_v2.py`) kiểm tra 7 label trong `TestClient(app).get("/").text`
— tức HTML thô server trả về, **chưa chạy JavaScript**. Trước khi sửa, đã
xác minh 3 việc:

1. `git log --oneline -- app/static/index.html app/static/app.js` → commit
   gần nhất chạm vào 2 file này là **`545525b fix(frontend): connect all
   backend endpoints to UI`**, chính là commit mới nhất toàn repo. `git
   status --short app/static/` → sạch, không có sửa đổi dang dở, không có
   dấu hiệu phiên nào khác đang chỉnh. Kết luận: đây là UI tĩnh **đang được
   bảo trì chủ động, không phải code chết bị Flutter thay thế** — đúng
   nhánh "UI tĩnh vẫn là fallback chính thức" trong 2 hướng đề xuất.
2. Grep 7 label trong `index.html`: **5/7 label có thật** — nằm trong
   `<option>` của dropdown `#scenario` và một thẻ `<h3>` (nội dung tĩnh,
   server render sẵn).
3. Grep 2 label còn lại ("Bổ sung hồ sơ UBO và BCTC", "RM phê duyệt tạo
   case/task") → **không có trong `index.html`, nhưng có thật trong
   `app.js`** (object `SCENARIOS` và hàm `renderActionButtons()`) — đây là
   nội dung được `app.js` bơm vào hai `<div>` rỗng (`#scenarioGuide`,
   `#expectedOutput`) **sau khi** người dùng chọn một case trong dropdown
   (sự kiện `change`). Không có lựa chọn mặc định, nên trang chưa từng
   được ai thao tác sẽ hợp lý khi hiện box trống — đây là hành vi UX đúng,
   không phải bug.

Kết luận: đây không phải "thiếu nội dung", mà là **test kiểm tra sai
layer** — nội dung có thật và được phục vụ thật (`/static/app.js` được
`index.html` tham chiếu qua `<script src="/static/app.js">`, trình duyệt
thật chắc chắn tải và chạy nó), chỉ là `TestClient` không thực thi JS nên
không thấy được.

### 13.2 Cách sửa — không xoá, không thêm nội dung trùng lặp

Theo đúng ràng buộc "không chỉ xoá test để lấy màu xanh": sửa
`tests/test_ui_v2.py` để mỗi label được kiểm tra đúng resource nó thực sự
nằm trong — 5 label tĩnh vẫn kiểm tra qua `GET /`; 2 label JS-render đổi
sang kiểm tra qua `GET /static/app.js` (chính là file `<script src>` trỏ
tới, một trình duyệt thật cũng tải đúng file này). Thêm một assert mới
xác nhận `index.html` thực sự có tham chiếu `<script src="/static/app.js">`
— để nếu sau này ai gỡ script đó ra, test vẫn bắt được lỗi thay vì
false-negative. **Không xoá bất kỳ assertion nội dung nào** — vẫn kiểm
tra đúng 7 chuỗi y hệt, chỉ đổi nơi tìm.

**Không sửa `app/static/index.html`/`app.js`** — không cần, vì nội dung
đã đúng và đã được phục vụ đúng; nhân đôi nó vào HTML tĩnh sẽ tạo hai
nguồn sự thật (SCENARIOS trong JS + text cứng trong HTML) dễ lệch nhau
theo thời gian, mà không giải quyết được gì thêm.

### 13.3 Kết quả

```
./.venv/Scripts/python.exe -m pytest tests/test_ui_v2.py -v
→ 2 passed

./.venv/Scripts/python.exe -m pytest tests/ -q
→ 343 passed, 0 failed
```

### 13.4 File sửa

| File | Loại | Thay đổi |
| --- | --- | --- |
| `tests/test_ui_v2.py` | Sửa | Tách assertion theo đúng resource (`/` vs `/static/app.js`); thêm docstring giải thích lý do kiến trúc; thêm assert script-tag để tránh false-negative trong tương lai |

### 13.5 Hạn chế

- Vẫn không có kiểm thử "chạy JS thật" (Selenium/Playwright) cho phần
  tương tác dropdown → guide box; test hiện tại xác nhận nội dung được
  phục vụ đúng, không xác nhận hành vi DOM sau khi JS chạy (ví dụ: chọn
  "Case 2" có thực sự làm `#scenarioGuide` hiện đúng text hay không). Nếu
  cần mức đảm bảo đó, cần thêm một lớp test hoàn toàn khác (browser
  automation), ngoài phạm vi P0 này.
