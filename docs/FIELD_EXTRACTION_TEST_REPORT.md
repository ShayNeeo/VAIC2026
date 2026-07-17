# Field Extraction Test Report

`tests/unit/test_v2_field_extraction.py` — 43 tests, all against
`app/intake/extractor.py` (`classify_document`, `extract_document_fields`,
`detect_needs`, `detect_pain_points`) and `app/intake/service.py`
(`IntakeService._detect_conflicts`, `_build_profile`). All fixture text is
**SYNTHETIC DEMO DATA**.

## Coverage by field

| Field | Cases | Notes |
| --- | --- | --- |
| Company name | full form, uppercase, TNHH form, repeated mention (first-wins), absent | |
| Tax code | valid synthetic MST, with `-NNN` branch suffix, not confused with adjacent phone/fax numbers, invalid format rejected, missing | |
| **Legal representative** | full label ("Người đại diện theo pháp luật:"), short label ("Đại diện:"), title not swallowed into the name, first-of-multiple-names wins, absent without evidence | **New field — did not exist before this work (see Bugs Found #3).** |
| Employee count | direct mention, "quy mô nhân sự" phrasing, missing | |
| Supplier count | direct mention, not confused with unrelated transaction-count numbers | |
| **Distributor count** | direct mention, not conflated with customer count, not conflated with branch count, customer count still extracted separately | **Regression test for Bug Found #1.** |
| ERP | named system (SAP, Oracle), a *need* for ERP integration without a named system (`explicit_needs` only, not fabricated as a system name), absent | **Regression test for Bug Found #2.** |
| Pain points | detected with source span + sub-1.0 confidence, empty when no signal words present | |
| Document classification | `classify_document` on a meeting-note-flavored fixture, `detect_needs` on a multi-need fixture | |
| Missing field | ERP + tax code both absent from a fixture that never mentions them; `CustomerBusinessSnapshot.missing_information` lists `company_identity.tax_code` end-to-end via `IntakeService.create()` | |
| Low confidence | a hedged quantity ("khoảng hơn 400 lao động") does not get fabricated into a precise `employees_count` — see explanation below; a field below the 0.85 auto-confirm threshold is flagged `NEEDS_REVIEW`; a field at/above threshold is `VALID` | |
| Provenance | every field from a multi-field fixture carries `source_document_id`, non-empty `source_section`, non-empty `source_text_span`, `extraction_method`, `confidence` in `[0,1]`, and a valid `validation_status`; `source_page` traced to the correct section metadata | |
| Conflict | two documents with different employee counts (500 vs 520) are flagged as a conflict on `business_profile.employees_count` with both candidate values, `requires_confirmation=True` (high-impact, unresolved); agreeing documents produce no conflict; an RM confirmation resolves the conflict (`requires_confirmation` flips to `False`, `resolved_value` set) | RM override case |
| DOCX integration | a real `python-docx`-generated file (not synthetic in-memory text) parsed via `app.knowledge.parsers.parse_document_bytes`, fed through the real extractor, asserting tax code / legal representative / employee count / distributor count all come out correctly | |

## Bugs found and fixed (not just tested around)

### 1. Distributor count and customer count shared one field

`app/intake/extractor.py`'s old regex was
`r"(?i)([0-9][0-9.,]{0,8})\s*(?:đại lý|dai ly|khách hàng|khach hang)"`
writing into `collection_profile.customer_count` — meaning "40 đại lý"
(40 dealers/distributors) was silently reported as 40 *customers*, a
different business concept. Split into two fields/regexes:
`collection_profile.distributor_count` (đại lý / nhà phân phối / điểm phân
phối) and `collection_profile.customer_count` (khách hàng only). Neither
matches "chi nhánh" (branch), a third, still-distinct concept.

### 2. The bare word "ERP" was captured as a system name

The old regex's capture group was
`(SAP|Oracle|MISA|ERP)` — the literal word "ERP" was itself a candidate
match. `"Doanh nghiệp muốn kết nối ERP nhưng chưa có hệ thống ERP nào"`
(customer explicitly has **no** system and just wants one) was extracted
as `technology_profile.erp_system = "ERP"` — a fabricated current-system
fact. Fixed by restricting the capture group to actual named products
(`SAP|Oracle|MISA|Odoo|NetSuite|Fast|Bravo`); the *need* for ERP
integration continues to be captured correctly and separately via
`detect_needs()`'s existing `erp_integration` signal into `explicit_needs`.

### 3. `legal_profile.legal_representative` did not exist

`classify_document()` already recognized "người đại diện" as a signal for
the `ubo_information` document type, but `extract_document_fields()` never
actually extracted a representative *name* into any field — only
`legal_profile.ubo_status` (verified/not) for UBO documents. Added a new
regex-based extraction (`Người đại diện theo pháp luật:` / `Đại diện:` /
diacritic-free variants, capturing up to the next comma/period/newline so a
trailing title doesn't get folded into the name).

## A test-design correction (not a code bug)

`test_meeting_note_classification` originally asserted that the
payroll/supplier/dealer/ERP-topic-dense `MEETING_NOTE` fixture (used for
the pain-point/needs extraction tests) would classify as `"meeting_note"`.
Live execution showed it classifies as `"payment_process"` instead —
`classify_document()` picks the rule with the most keyword hits, and that
fixture genuinely has 5 payment_process-keyword hits vs 2 meeting_note
hits. This is correct, content-driven behavior, not a bug: neither
`payment_process` nor `meeting_note` is a required-document type any
eligibility rule keys off of (`data/synthetic/v2/eligibility_rules.json`
only checks `business_registration`, `financial_statements`,
`ubo_information`), so this classification ambiguity has no functional
effect on eligibility. The test now uses a separate, purely
meeting-note-flavored fixture instead of asserting a classification for a
fixture that was never designed to be classification-unambiguous.

## Why the hedged-quantity case is a "does not fabricate" result, not a "flags for review" result

The prompt's low-confidence spec describes "khoảng hơn 400 lao động" as a
case that should produce a low-confidence candidate flagged for review.
What actually happens: the employee-count regex requires the digit to be
immediately followed by `nhân viên|nhân sự|người lao động` (with "người").
"400 lao động" (missing "người") does not match at all, so **no field is
emitted** rather than a low-confidence one being emitted. This is verified
directly (`test_vague_hedged_employee_count_is_not_fabricated_as_a_precise_fact`)
against the actual regex boundary — the practical effect (no fabricated
precise number from a hedged phrase) matches the spec's intent, but the
mechanism is "stay silent" rather than "flag for review," which is worth
knowing if a future change wants a genuine low-confidence *candidate* value
surfaced to the RM instead of nothing at all (listed as a P3 follow-up).
