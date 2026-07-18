# Legal/Compliance V2 — Capability Matrix

> Tất cả policy, khách hàng và kết quả trong module này là `SYNTHETIC_DEMO_DATA`. Không phải ý kiến pháp lý hoặc chính sách SHB thật.

## Component làm được gì

| Khả năng | Cơ chế | Output/Evidence |
|---|---|---|
| Chọn chính sách đúng sản phẩm | Policy registry lọc `product_ids`, active và effective date | `related_policies[]` theo từng product |
| Kiểm tra điều kiện | `EligibilityEngine` deterministic, fail-closed | `passed`, `failed`, `pending_information`, `pending_review` |
| Phát hiện hồ sơ/dữ liệu thiếu | Required-document và required-field rules | `missing_information`, `legal_summary.required_actions` |
| Giải thích kết luận | Product → Rule → Policy → Section lineage | Policy title, version, section, summary và exact quote |
| Kiểm chứng nguồn | Legal index + Evidence Validator | `claim_id`, `evidence_valid`, Evidence/Audit/AI Decision Log |
| Phân luồng rủi ro | Risk Guardrail Gate | Chuyển Compliance review khi nguồn thiếu/xung đột |
| Hỗ trợ RM | Web và Flutter projection | Kết quả pháp lý và chính sách liên quan theo sản phẩm |

## Component không được làm

- Không tự phê duyệt tín dụng, mở sản phẩm hoặc thực hiện hành động ngoài hệ thống.
- Không dùng LLM/RAG để thay đổi kết quả deterministic của eligibility rule.
- Không suy diễn khi policy/evidence thiếu, hết hiệu lực, sai product scope hoặc không đúng ACL.
- Không thay thế Legal/Compliance/SME và không dùng dữ liệu synthetic cho production.
- Không bỏ qua approval token, exact payload binding, RBAC hoặc idempotency gate.

## Phạm vi dữ liệu hiện tại

- Chính sách chung: KYC doanh nghiệp, đại diện pháp luật, UBO, AML/watchlist và hiệu lực hồ sơ.
- Chính sách riêng: Payroll, Cash Management, Bulk Payment/API và Working Capital.
- Nguồn sự thật demo: `data/synthetic/v2/b2b_policies.json`; logic quyết định: `data/synthetic/v2/eligibility_rules.json`.

## Điều kiện để lên pilot

Policy thật phải có data owner, Legal, Privacy và Security sign-off; corpus được version hóa; SSO/IAM thật; case de-identified do SME adjudicate; semantic retrieval, penetration, load và audit-retention test đạt yêu cầu.
