# Evidence Validation Implementation

## What was wrong

The live path (`app/workflow/engine.py::_product_evidence()` /
`_legal_evidence()`) set `Evidence.is_valid = bool(source["quote"])` — i.e.
**any non-empty string counted as valid**. This never actually checked the
quote against anything. Separately, `app/safety/evidence_validator.py`
contained a more sophisticated-looking validator (exact-match +
Gemini-embedding cosine-similarity), but it was **dead code**: imported
only by `app/safety/__init__.py`, nowhere in the live pipeline, and it
referenced fields that do not exist on the current `Evidence`/
`SharedCaseState` model (`source_doc`, `page_or_section`, `state.audit_log`,
`state.legal_result`, `state.approval_status` — confirmed against
`app/schemas/v2/shared_case_state.py`; it would have raised `AttributeError`
if ever actually called), and it validated against
`data/mock_database/*.json`, a dataset the live pipeline never reads (the
live pipeline uses `data/synthetic/v2/{products,eligibility_rules}.json`).
`app/safety/guardrails.py`'s `GuardrailGate` had the identical problem
(same dead-import status, same nonexistent-field references) and has been
deleted; the real, live guardrail is `app/safety/input_guardrails_v2.py`.

## What exists now

`app/safety/evidence_validator.py` was rewritten from scratch as a real,
deterministic validator with **no dead code retained** — one implementation,
not two competing ones.

### `validate_claim()`

```python
validate_claim(
    claim_id="PROD-PROD-PAYROLL-1",
    source_document_id="SYN-PRODUCT-CATALOG",
    source_version="2026.1",
    quote="...",
    index=product_knowledge_index,   # a ChunkIndex: get_chunks_for_document()
) -> EvidenceValidationResult
```

Steps, in order:

1. Empty/whitespace-only quote → `INSUFFICIENT_EVIDENCE`.
2. `source_document_id in {"SYSTEM-TOOL-CONTRACT"}` → `VALID` immediately
   (synthetic, internally-authored system policy text — see
   `app/eligibility/engine.py::_live_failure` — not drawn from the RAG
   index, so there is nothing to look up).
3. Look up every indexed chunk for `(source_document_id, source_version)`
   via the new `PersistentHybridIndex.get_chunks_for_document()` (added in
   `app/knowledge/index.py`, a straightforward SQLite scan-and-filter, same
   pattern as the existing `search()` method).
   - No chunk for that `document_id` at all → `SOURCE_NOT_FOUND`.
   - Chunks exist for that `document_id` but not at that `document_version`
     → `VERSION_MISMATCH`.
4. Normalize both the quote and every candidate chunk's text (`NFC` Unicode
   normalization + whitespace/newline collapsing — `_normalize()`) and check
   substring containment. This is what makes "same content, different
   line-wrap" still match while an altered word does not.
   - Not found in any chunk → `INVALID` (`reason="quote_not_found_in_source"`).
   - An optional `semantic_check` callable can be supplied to *record* a
     supplementary similarity signal on a near-miss, but it can never flip
     `INVALID` to `VALID` — it is informational only, exactly per spec
     ("deterministic first, semantic is additive, never the sole basis").
5. If the matched chunk's `effective_to` has passed → `EXPIRED_SOURCE`.
6. Otherwise → `VALID`.

### `detect_conflicts()` / `EvidenceValidator.validate_all()`

Groups a batch of claims by `claim_id`; if the same `claim_id` was ever
asserted with two different (normalized) quotes, every evidence sharing that
`claim_id` is marked `CONFLICTING_EVIDENCE` rather than picking one
arbitrarily.

### Status enum

`VALID | INVALID | INSUFFICIENT_EVIDENCE | CONFLICTING_EVIDENCE |
SOURCE_NOT_FOUND | VERSION_MISMATCH | EXPIRED_SOURCE` — matches the spec
exactly. `EvidenceValidationResult.is_valid` is `True` iff `status ==
VALID`; everything else maps to `Evidence.is_valid = False` in the live
wiring below, so no separate mapping table is needed downstream.

## Live wiring

`app/workflow/engine.py::_product_evidence()` and `_legal_evidence()` (now
instance methods, not `@staticmethod` — they need `self.product.knowledge`
and the new `self.legal_knowledge` respectively) call `validate_claim()`
for every evidence record at construction time and set:

```python
is_valid=result.is_valid
validation_score=1.0 if result.exact_match else 0.0
```

`V2WorkflowEngine.__init__` gained a `legal_knowledge: LegalKnowledgeService`
constructor param (defaults to a fresh instance) — this is the same index
`LegalKnowledgeService.search()` serves from, so eligibility-rule evidence
is checked against the exact indexed text, not a separate copy.

Downstream, nothing had to change: `V2WorkflowEngine._analysis()` already
had `all_valid = all(item.is_valid and item.quote for item in
state.evidences)` and, on `not all_valid`, calls `self._apply_risk_gate()`
→ `RiskGuardrailGate.evaluate()`, which fails closed to
`outcome="need_review", risk_level="high"` on any invalid evidence
(`app/workflow/risk_gate.py:47-55`) — that logic was already correct, it
was just being fed a rubber-stamped `is_valid` before this change.
`ActionExecutorV2.execute()` independently re-checks
`all(item.is_valid for item in state.evidences)` before allowing execution
(`app/actions/executor.py:38`) — also pre-existing, also now fed a real
signal.

## Tests

`tests/unit/test_v2_evidence_validator.py` (14 tests):

| Requirement | Test |
| --- | --- |
| Quote correct → valid | `test_exact_quote_is_valid`, `test_quote_as_substring_of_a_longer_chunk_is_valid` |
| Quote altered by one word → invalid | `test_altered_quote_is_invalid` |
| Quote never existed → invalid | `test_fabricated_quote_not_present_anywhere_is_invalid` |
| Source document not found | `test_unknown_source_document_is_source_not_found` |
| Version mismatch | `test_known_document_wrong_version_is_version_mismatch` |
| Whitespace different, same content → valid | `test_whitespace_and_linebreak_differences_still_match` |
| Expired source | `test_expired_source_is_flagged_even_though_quote_matches` |
| Two sources conflict | `test_detect_conflicts_flags_same_claim_id_with_different_quotes`, `test_evidence_validator_marks_conflicting_claim_id_invalid` |
| System-authored source exempt | `test_system_tool_contract_source_is_exempt_from_index_lookup` |
| Empty quote | `test_empty_quote_is_insufficient_evidence` |
| **Invalid evidence blocks approval/action** (integration, live wiring) | `test_tampered_product_quote_is_caught_by_the_live_engine_wiring` — builds a real `ProductKnowledgeService`, retrieves a real evidence dict, deliberately corrupts its `quote`, calls `V2WorkflowEngine._product_evidence()` directly, asserts `is_valid is False` |
| **Invalid evidence blocks the action executor** | `test_action_executor_denies_execution_when_any_evidence_is_invalid` — constructs a `SharedCaseState` with one `is_valid=False` evidence, asserts `ActionExecutorV2.execute()` raises `ExecutionDenied("evidence validation failed")` before ever reaching token verification |

None of these tests call a live LLM or embedding API — `validate_claim()`
and `detect_conflicts()` are pure functions over an index/list, and the
integration test's `ProductKnowledgeService` uses whatever
`KNOWLEDGE_EMBEDDING_PROVIDER` is configured (openai by default), but no
assertion depends on embedding *values* — only on the deterministic
substring check.
