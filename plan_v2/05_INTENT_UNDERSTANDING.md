# 05 — Intent and Entity Understanding

## 1. Objective

Biến message + minimized context thành `IntentResult` đúng schema, hỗ trợ multi-intent, provenance, ambiguity và downstream execution requirements.

Source of truth output: `contracts/intent_result.schema.json`.

## 2. Intent representation

Không chỉ dùng một label. Mỗi intent gồm:

- Primary job-to-be-done.
- Sub-intents.
- Target entity/customer/case.
- Requested action.
- Constraints.
- Success criteria.
- Required outputs.
- Missing slots.
- Ambiguities.
- Field-level confidence.
- Evidence spans.

## 3. Initial intent taxonomy

| Intent ID | Meaning | Required slots | Risk |
|---|---|---|---|
| `find_product` | Tìm sản phẩm phù hợp | customer or profile, objective | low |
| `compare_products` | So sánh sản phẩm | product candidates | low |
| `check_eligibility` | Kiểm tra điều kiện | customer, product | medium/high |
| `check_missing_documents` | Kiểm tra hồ sơ thiếu | case/customer, product/workflow | medium |
| `resume_case` | Tiếp tục case sau cập nhật | case, changed artifact | medium |
| `prepare_customer_response` | Soạn phản hồi | case, purpose, recipient candidate | medium |
| `prepare_case_task` | Chuẩn bị case/task draft | case/customer, task type | medium |
| `approve_actions` | Phê duyệt hành động | case, action payload | high |
| `reject_actions` | Từ chối hành động | case, reason | high |
| `status_lookup` | Xem trạng thái | case/task | low |
| `out_of_scope` | Ngoài nghiệp vụ | — | varies |

Taxonomy phải lưu trong config/versioned registry; không hard-code rải rác.

## 4. Extraction pipeline

```text
Normalize text
→ detect language/abbreviations
→ build prompt from taxonomy + ContextSnapshot
→ LLM structured output
→ JSON schema validation
→ deterministic entity normalization
→ slot merge with context
→ ambiguity/conflict calculation
→ confidence policy
```

LLM không được gọi tool; chỉ semantic extraction.

## 5. Prompt contract

System instructions phải yêu cầu:

- Chỉ sử dụng message và context được cung cấp.
- Không tự tạo customer/product/amount.
- Tách nhiều intent nếu có.
- Giữ nguyên số tiền, ngày, tên thực thể.
- Field không biết phải để null/missing.
- Liệt kê các hypothesis khi mơ hồ.
- Evidence span phải trích đúng message ID/text.
- Phân biệt user goal và requested action.
- Trả duy nhất object đúng schema.

Không yêu cầu hoặc lưu chain-of-thought. Chỉ cần concise rationale/evidence spans.

## 6. Entity normalization

| Entity | Normalization |
|---|---|
| Customer | Resolve external/customer ID via context/search tool outside LLM |
| Product | Map alias to catalog product ID; unknown stays unresolved |
| Amount | Decimal + currency; preserve original text |
| Date/duration | ISO date/duration + original expression |
| Urgency | `normal/high/urgent` only with explicit signal/SLA |
| Document | Map to controlled document taxonomy |
| Task/action | Map to allowlisted action type |

## 7. Multi-intent and dependency

Example message: “Tìm gói chi lương và xem có vay thấu chi được không, rồi soạn email hồ sơ thiếu.”

Expected:

```text
find_product(payroll)
find_product(working_capital)
→ check_eligibility(working_capital)
→ check_missing_documents
→ prepare_customer_response
```

Intent Engine emits intents; Workflow module creates dependencies. Intent Engine không tự thực thi.

## 8. Model strategy

- Default: one capable structured-output model through internal gateway.
- Fallback: deterministic keyword/taxonomy router for top-level safe intents.
- Temperature low/configurable.
- Prompt version logged.
- Timeout ≤ 15s, max one schema-repair retry.
- Model output cannot override permission/context contracts.

## 9. Proposed code artifacts

| File | Responsibility |
|---|---|
| `app/intent/taxonomy.py` | Versioned intent definitions |
| `app/intent/models.py` | Pydantic generated from contract |
| `app/intent/prompt.py` | Prompt builder/version |
| `app/intent/extractor.py` | LLM structured extraction |
| `app/intent/normalizer.py` | Text/entity normalization |
| `app/intent/validator.py` | Contract/semantic validation |
| `app/intent/fallback.py` | Deterministic fallback router |

## 10. Tests

- Single clear intent.
- Multi-intent dependency-ready output.
- Vietnamese without accents.
- Abbreviations: BCTC, UBO, HMTD.
- Customer/case taken from workspace.
- User switches customer explicitly.
- Unknown product not hallucinated.
- Amount/date preserved exactly.
- Out-of-scope classification.
- Malformed JSON repaired once then typed failure.
- Evidence spans correspond to real message text.

## 11. Acceptance

- Contract validation pass 100% for accepted outputs.
- Primary intent accuracy ≥ 90% MVP, ≥ 95% pilot.
- Multi-intent recall ≥ 90% MVP.
- Unknown entities never converted into known IDs without resolver evidence.
- Every inferred field has source/confidence.

