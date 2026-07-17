# 08 — Eligibility, Legal and Compliance

## 1. Objective

Kết hợp rule deterministic, legal RAG và live checks để trả rõ: đạt, không đạt, thiếu thông tin hoặc cần review; không để LLM tự phê duyệt.

## 2. Rule model

```json
{
  "rule_id": "RULE-UBO-001",
  "version": "2026.1",
  "scope": ["PROD-WORKING-CAPITAL"],
  "effective_from": "2026-01-01",
  "effective_to": null,
  "severity": "blocking",
  "required_inputs": ["customer.ubo_status"],
  "condition": "ubo_status == complete",
  "failure_code": "UBO_MISSING",
  "source_document_id": "LEGAL-KYC-001",
  "source_location": "Điều 8"
}
```

Rules lưu versioned registry; không nhúng business rule rải rác trong prompt.

## 3. Rule priority

1. Permission/sanction/watchlist hard block.
2. Legal/regulatory blocking.
3. Product eligibility blocking.
4. Missing required information.
5. Warning/advisory.
6. LLM-generated explanation only.

LLM không được downgrade severity.

## 4. Evaluation flow

```text
Product candidates + customer context + documents
→ validate required inputs/freshness
→ execute deterministic rules
→ retrieve current legal evidence
→ optional live KYC/UBO/watchlist tools
→ aggregate by product
→ detect Product/Legal conflict
→ emit eligibility result + evidence
```

## 5. Output contract semantics

Per product:

- `passed`: all blocking rules pass and required data fresh.
- `failed`: explicit disqualifying rule.
- `pending_information`: required input missing/stale.
- `pending_review`: policy conflict, PEP/AML or ambiguous legal case.

Output includes:

- rule results.
- severity.
- missing documents/information.
- evidence claim IDs.
- evaluated rule/version/time.
- data freshness.

## 6. Legal RAG

- Chunk by chapter/article/clause.
- Keep policy hierarchy.
- Filter active/effective version.
- ACL before retrieval.
- Exact article/number matching boosted.
- Quote and source version mandatory.

Legal RAG supports explanation/evidence; deterministic engine owns outcome for encoded rules.

## 7. Conflict handling

Examples:

- Product candidate matches, Legal blocks → keep product visible as blocked with reason.
- Two active policies conflict → `pending_review`.
- CRM says UBO complete but document missing → configurable data-owner precedence; default `pending_review`.
- Stale financial data → `pending_information`.

## 8. Proposed code artifacts

| File | Responsibility |
|---|---|
| `app/eligibility/models.py` | Rule and result models |
| `app/eligibility/registry.py` | Versioned rule loading |
| `app/eligibility/engine.py` | Deterministic execution |
| `app/eligibility/aggregator.py` | Per-product aggregate |
| `app/eligibility/conflicts.py` | Product/legal/data conflicts |
| `app/knowledge/chunking/legal.py` | Legal structure chunking |
| `app/knowledge/retrieval/legal.py` | Legal retrieval |
| `app/integrations/kyc.py` | KYC/UBO/watchlist adapter |

## 9. Failure/fallback

- Rule registry unavailable: fail closed for eligibility.
- Legal index unavailable: deterministic result may proceed only if source/version cached and valid; otherwise pending review.
- KYC tool timeout: pending review/information, never pass.
- Malformed rule: quarantine rule, alert, do not silently ignore blocking rule.

## 10. Tests

- ABC missing UBO blocks credit only.
- Missing recent BCTC pending information.
- Payroll can remain available when credit blocked.
- Invalid/expired business registration blocks.
- Rule version effective-date selection.
- Product/Legal conflict pending review.
- KYC timeout never returns passed.
- Unsupported legal claim rejected by Evidence Validator.

## 11. Acceptance

- Unsafe approval rate = 0.
- Missing-document recall ≥ 95% MVP, target 100% high-risk golden set.
- Every blocking result has rule ID/version/evidence.

