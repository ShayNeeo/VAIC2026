# VAIC Repository Evaluation Report

**Repository:** `c:\Users\Admin\Desktop\hakathon` (git remote: `https://github.com/ShayNeeo/VAIC2026.git`)
**Evaluated at:** 2026-07-18 (local working tree, as found)
**Evaluator scope:** read-only audit. No code was modified during this evaluation. All commands executed are non-destructive (pytest, evaluation runners, `uvicorn` smoke test, `git status`/`log`/`diff --stat`, `grep`).

> A prior report existed at this path with near-perfect scores (97.8/100 raw) and "0 red flags." This audit re-verified every major claim directly against source code and live execution and found materially different results — see §22 for specifics (e.g. the prior report cited `app/safety/evidence_validator.py` as "Strong" evidence, but that file is dead code that would crash if invoked and is hardcoded to a currently-billing-exhausted Gemini key). This report replaces it.

---

## 1. Executive Scorecard

| Tiêu chí | Trọng số | Điểm hiện tại | Confidence |
| --- | ---: | ---: | --- |
| Problem Relevance | 20 | 19.0 | HIGH |
| AI-Native Architecture | 20 | 18.7 | HIGH |
| Technical Execution | 15 | 12.1 | HIGH |
| Deployment and Live URL | 15 | 3.6 | HIGH |
| Feasibility and Pilot | 15 | 12.2 | MEDIUM |
| Startup Potential | 15 | 11.9 | MEDIUM |
| **Tổng** | **100** | **77.5** | **HIGH** |

Confidence is HIGH overall because almost every claim below was checked against source code, live `pytest`/`uvicorn` execution, or `git` state rather than documentation. Feasibility/Startup are MEDIUM because those sections lean partly on prescriptive design docs (`plan_v2/*.md`) that cannot be "executed."

## 2. Final Classification

**77.5/100 → "Competitive but has visible gaps" (70–79.5 band).**

The backend architecture is genuinely sophisticated and mostly real (verified by execution), but three current, verifiable facts cap the score hard: (1) there is no live URL anywhere, (2) the exact flagship multi-product demo scenario fails end-to-end right now under the repository's own default `.env`, and (3) approximately the entire V2 implementation — everything this report gives credit for — is **not committed to git and has never been pushed to the tracked GitHub remote**. Anyone who clones `https://github.com/ShayNeeo/VAIC2026.git` today gets the old, deleted V1 skeleton, not the system audited here.

Not asserting a competition ranking — that depends on other teams and judge discretion.

## 3. Evaluation Scope and Limitations

- Read: `app/**`, `services/rag_mcp/**` (partially, via prior-session findings only, not re-read this pass), `tests/**`, `plan_v2/**`, `docs/**`, `data/**` (structure + selected JSON), `README.md`, `Dockerfile`, `docker-compose.yml`, `.env`, `.env.v2.example`, `pytest.ini`, `requirements.txt`.
- Executed: full `pytest` suite (`--basetemp=./tmp_test`), the same suite with an env override to isolate root causes, `app.evaluation.runner` (golden-case eval), a live `uvicorn` server with `curl` smoke tests against `/`, `/api/v2/health`, `/docs`, and multiple `git` inspection commands.
- Not executed: `docker build` (Docker CLI not present in this environment → **UNVERIFIED DUE TO ENVIRONMENT LIMITATION**), no browser/JS test harness run (JS logic was read, not executed in a browser), no CI (none exists to run).
- `services/rag_mcp/` internals (the standalone MCP server) were audited in a prior turn of this same session, not re-verified line-by-line in this pass; where cited, it is marked accordingly.
- This report reflects the working tree exactly as found, including uncommitted changes. Where "the repository" could mean either the working tree or the last git commit, both are stated explicitly (this distinction turned out to be critical — see §22, Red Flag R1).

## 4. Repository Evidence Inventory

| Category | Path | Status |
| --- | --- | --- |
| Backend app | `app/` (18 subpackages: actions, api, approval, context, data_catalog, eligibility, evaluation, intake, integrations, intent, knowledge, observability, operations, product, reliability, safety, schemas, storage, tools, workflow) | Present, mostly untracked in git (§22 R1) |
| Frontend | `app/static/{index.html,app.js,app.css}` | Present, untracked in git |
| Standalone RAG MCP server | `services/rag_mcp/` | Present |
| Tests | `tests/unit/*` (17 files), `tests/contract/*`, `tests/rag_mcp/*`, `tests/test_api_v2.py`, `tests/test_sales_cases_e2e.py`, `tests/test_ui_v2.py`, `tests/test_v2_evaluation.py`, `tests/test_v2_safety_reliability_evaluation.py` | 166 tests collected (verified) |
| Contracts | `plan_v2/contracts/*.schema.json`, `plan_v2/contracts/tool_contracts.json` | Present, cross-checked by `tests/contract/test_v2_contracts.py` |
| Eval datasets | `data/eval/v2/{golden_cases.json (40 cases), reliability_cases.json, security_cases.json}` | Present, executable |
| Docs | `docs/*.md` (14 files) + `docs/SHB_Corporate_Expert_Workspace_Multi_Agent_Proposal.docx` (source of the pain point/diagram) | Present |
| Deployment | `Dockerfile`, `docker-compose.yml` | Present, not built in this environment |
| CI | — | **NOT FOUND IN REPOSITORY** |
| Live URL | — | **NOT FOUND IN REPOSITORY** |
| Legacy/dead code | `app/agents/*`, `app/rag/*` (deleted from disk, still in last git commit), `app/database.py`, `app/safety/evidence_validator.py`, `app/safety/guardrails.py`, `app/tools/product_tools.py`/`legal_tools.py` (referenced but do not exist) | See §22 |

## 5. Commands Executed

| Command | Purpose | Result | Exit code | Impact on score |
| --- | --- | --- | --- | --- |
| `git status`, `git log --oneline`, `git diff --stat HEAD`, `git status --porcelain app/` | Establish true committed vs working-tree state | 6 total commits; 60 untracked files + 39 modified/deleted tracked files; nearly all of `app/` untracked | 0 | Deployment §9E, Red Flag R1 (critical) |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=./tmp_test` (full suite) | Ground-truth test result at evaluation time | `3 failed, 163 passed` (166 collected) | 1 | Technical Execution §8A/E |
| Same 2 failing e2e tests with `KNOWLEDGE_EMBEDDING_PROVIDER=openai RAG_MCP_EMBEDDING_PROVIDER=openai RAG_MCP_ENABLED=false` | Root-cause isolation | `2 passed` | 0 | Confirms root cause is `.env` config, not broken logic |
| `pytest tests/rag_mcp/test_transport.py::test_official_mcp_streamable_http_transport_with_service_auth` standalone | Check if 3rd failure is a real bug or test-order flake | `1 passed` | 0 | Flaky/order-dependent, not a logic bug |
| `python -m app.evaluation.runner` | Golden-case business eval | 40/40, all metrics 1.0, `unsafe_approval_rate: 0.0` | 0 | Technical Execution §8E (with caveat, see §18) |
| `uvicorn app.main:app` + `curl` on `/`, `/api/v2/health`, `/docs` | Local runnability smoke test | All `200`; health reports `"status":"ok"`, `product_chunks:6`, `legal_chunks:9` | 0 | Deployment §9C (local only) |
| `docker --version` | Check Docker availability | `command not found` | 127 | Docker build → UNVERIFIED DUE TO ENVIRONMENT LIMITATION |
| `pytest --collect-only` | Exact test count | `166 tests collected` | 0 | Cross-checks README's stale "172 passed" claim |
| `git ls-files \| grep env`, `git status --porcelain \| grep env` | Verify which `.env*` files are actually tracked | `.env.example` tracked but deleted in working tree; `.env.v2.example` untracked | 0 | Deployment §9D/E |
| `grep` for hardcoded secret patterns, dead-code imports, hardcoded company logic | Red-flag sweep | No live secrets found; confirmed 3 dead-code modules; confirmed no company-name-keyed business logic | — | §22 |

---

## 6. Problem Relevance — 20

| Sub-criterion | Max | Raw Score | Evidence Level | Multiplier | Awarded Score | Evidence | Findings |
| --- | --: | --: | --- | --: | --: | --- | --- |
| A. Fit với đề bài | 5 | 5.0 | Strong | 1.0 | 5.0 | `app/api/v2/router.py` requires `X-Employee-ID`/`X-Session-ID` on every route; `require_permission()` gates by IAM role; UI copy and README are entirely RM-facing ("RM Workspace", "Kính gửi Quý khách hàng... RM kiểm tra, phê duyệt" in `app/tools/operations_tools.py:33-44`). No public/anonymous chat endpoint exists. | VERIFIED BY EXECUTION (routes/health tested) |
| B. Pain point rõ và thực tế | 4 | 4.0 | Strong | 1.0 | 4.0 | `docs/SHB_Corporate_Expert_Workspace_Multi_Agent_Proposal.docx` §1.3 (read via python-docx earlier this session): RM must manually cross-reference Product/Legal/Operations knowledge with no shared case state. `plan_v2/01_SCOPE_AND_PRODUCT.md` journeys A–D (verified by sub-agent) restate this concretely with a context-reuse hero use case. | DOCUMENTED, consistent with implementation |
| C. User journey hoàn chỉnh | 4 | 3.5 | Strong | 1.0 | 3.5 | Full chain exists and is exercised by `tests/test_sales_cases_e2e.py`: create → upload → process-documents → confirm-profile → run-analysis → approval-preview → approve → execute-actions. `test_payroll_journey_reaches_approval_executes_mock_and_exposes_ai_log` **passed** in this session's live run. However, 2 of 5 tests in the same file (`test_missing_documents_pause...`, `test_multi_product_request...`) **fail under the repo's own default `.env`** (§8.0). | VERIFIED BY EXECUTION, partially failing right now |
| D. Giá trị đầu ra | 4 | 3.5 | Strong | 1.0 | 3.5 | All 6 output types from the proposal's §8.3 exist in code and were produced in a full live run earlier this session (solution bundle+reason, per-product eligibility+evidence, missing-document checklist, draft customer email, CRM case/task draft, full AI/audit trace). Confirmed structurally in `app/operations/service.py:87-119` and `app/workflow/engine.py`. Docked because the multi-product path that produces this bundle is currently broken by default (§8.0). | VERIFIED (mechanism), currently unreliable in default config |
| E. Scope hợp lý | 3 | 3.0 | Strong | 1.0 | 3.0 | No auto credit-approval anywhere (`EligibilityEngine` is rule-only, "no_llm" tagged in every AI-log entry, `app/eligibility/engine.py`). No real external send: `operations_result["external_side_effects"] == []` always, asserted by `tests/test_sales_cases_e2e.py:123`. Disclaimers on every draft: "không phải cam kết cấp sản phẩm, hạn mức hoặc tín dụng" (`app/operations/service.py:175,185,221`). | VERIFIED BY EXECUTION |

**Section total: 19.0 / 20**

### Strengths
Genuine RM-only scope, a specific and well-documented pain point, and a real (not narrated) end-to-end journey for at least one scenario.

### Weaknesses
The exact flagship scenario from the proposal is not reliably reproducible right now with the repo as checked out (§8.0).

### Missing Evidence
No user research or RM interview artifacts beyond the proposal document itself (expected for a hackathon; not penalized further).

### Recommended Fixes
Fix the default embedding-provider config (§25 P0-2) so journeys C/D are consistently reproducible.

### Score Cap Applied
None.

---

## 7. AI-Native Architecture — 20

| Sub-criterion | Max | Raw Score | Evidence Level | Multiplier | Awarded Score | Evidence | Findings |
| --- | --: | --: | --- | --: | --: | --- | --- |
| A. Planner và orchestration | 4 | 4.0 | Strong | 1.0 | 4.0 | `app/workflow/planner.py`: `PlannerService.plan()`/`replan()` builds a real dependency graph (`PlanStep.dependencies`, `status: ready/blocked/completed`) and re-plans based on `eligibility_result.overall_status` (3 distinct branches, `planner.py:33-63`). `app/workflow/engine.py::resume()` supports partial resume via `impacted_nodes()` (only re-runs downstream nodes), with a hard loop cap (`loop_count >= 3 → FAILED`, `engine.py:171-174`). Not a fixed prompt chain — plan structure changes based on runtime data. | VERIFIED BY EXECUTION (mechanism proven with env override; see §8.0 for current default-env caveat) |
| B. Specialist Agents | 4 | 4.0 | Strong | 1.0 | 4.0 | 3 distinctly-scoped services: `app/product/service.py` (`ProductService`, own knowledge index), `app/eligibility/engine.py` (`EligibilityEngine`, own `RuleRegistry`, fail-closed, `no_llm` by design), `app/operations/service.py` (`OperationsService`, own SOP file `data/synthetic/v2/operations_sop.json`, own source-card gate `require_serving_approval()`). Each has its own Pydantic-typed input/output on `SharedCaseState` (`product_result`, `eligibility_result`, `operations_result`) and its own unit test file (`test_v2_product_knowledge.py`, `test_v2_eligibility.py`, `test_v2_operations.py`). | VERIFIED BY EXECUTION |
| C. Agent collaboration | 3 | 2.8 | Strong | 1.0 | 2.8 | Concrete cross-agent effect proven by `test_missing_documents_pause_then_uploaded_evidence_resumes_only_downstream`: Product's `product_ids` feed Eligibility → Eligibility's `pending_information` blocks Planner's `approval`/`compliance` steps → Operations' checklist reasons include `"eligibility_rule"` sourced from the blocked rule IDs → after new documents arrive, only `evaluate_eligibility` onward re-runs (Product is *not* re-run). This is real dependency propagation, not independent text generation glued together. Docked slightly because this exact test currently **fails** under default `.env` (passes with the openai override — mechanism is sound, default config is not). | VERIFIED BY EXECUTION (with override); FAILING in current default config |
| D. Tool use và action execution | 3 | 2.8 | Strong | 1.0 | 2.8 | Real observable side effects: `app/actions/executor.py::ActionExecutorV2.execute()` re-validates eligibility==passed, all evidence valid, payload matches the frozen draft, then consumes a one-time approval token and persists an idempotent result (`SHB-CRM-*`/`SHB-OPP-*`/`SHB-TASK-*` IDs, content-hashed). `test_payroll_journey_...` asserts `result["opportunity_id"].startswith("SHB-OPP-")` and **passed live**. Persisted via `V2Repository` (SQLite), not in-memory only. | VERIFIED BY EXECUTION |
| E. RAG, evidence và grounding | 3 | 2.0 | Medium | 1.0 (post-discount) | 2.0 | Retrieval is real (`app/knowledge/index.py::PersistentHybridIndex.search()`, dense+sparse hybrid, branch ACL, `effective_from/effective_to` date filters, citations with `source_document_id/version/location/quote`). **But** the live "evidence validation" that gates auto-approval is shallow: `app/workflow/engine.py:429,443` sets `is_valid=bool(source["quote"])` — i.e. any non-empty quote string from the curated catalog/rule data is automatically "valid." The more rigorous validator that actually checks a quote against real source text (`app/safety/evidence_validator.py`, exact-match + embedding cosine-similarity) is **dead code**: it is only imported by `app/safety/__init__.py` and nowhere else in the live pipeline, references fields that don't exist on the current `Evidence`/`SharedCaseState` model (`source_doc`, `page_or_section`, `state.audit_log`, `state.legal_result`, `state.approval_status` — none of these exist; confirmed against `app/schemas/v2/shared_case_state.py`), and is hardcoded to the currently-broken Gemini provider (`evidence_validator.py:22`). It would raise `AttributeError` if ever actually called. | Retrieval: VERIFIED BY EXECUTION. Hallucination-check: DOCUMENTED BUT NOT IMPLEMENTED in the live path (a more sophisticated version exists but is orphaned/broken) |
| F. Guardrails và human-in-the-loop | 2 | 2.0 | Strong | 1.0 | 2.0 | `app/safety/input_guardrails_v2.py::screen_input()` (regex prompt-injection + PII redaction) is wired into every case-create/message endpoint and **verified**: `test_sales_case_scope_and_unsafe_input_fail_closed` passed live. `app/workflow/risk_gate.py::RiskGuardrailGate` fail-closes to `need_review`/`high` risk on invalid evidence, `failed`, `pending_review`, or any unrecognized eligibility status — the "unrecognized status" branch is an explicit fail-closed default (`risk_gate.py:76-78`). `ActionExecutorV2.execute()` independently re-checks eligibility+evidence even after a token is issued (defense in depth, `executor.py:36-39`). No code path sends a real email or calls a real external system — every artifact is `"status": "draft"`/`"draft_not_sent"`. | VERIFIED BY EXECUTION |
| G. Adaptive routing | 1 | 1.0 | Strong | 1.0 | 1.0 | `app/workflow/router.py::ComplexityRouter` — deliberate allowlist (`SIMPLE_PRIMARY_INTENTS = {status_lookup, compare_products, check_missing_documents}`), fails closed to "complex" for anything else, with explicit reasoning in the module docstring. 10 dedicated unit tests in `tests/unit/test_v2_risk_gate_and_router.py`. | VERIFIED BY EXECUTION |

**Section total: 18.7 / 20**

### Strengths
Real dependency-aware planning and re-planning, 3 genuinely distinct specialist services with their own data sources, real persisted actions, and a fail-closed risk gate that distinguishes "missing info" from "hard block" from "policy conflict" — a materially more sophisticated design than a single generic `else: pending_review` branch.

### Weaknesses
The "evidence validator" that is supposed to catch unsupported/hallucinated claims is effectively a no-op (`bool(quote)`) in the live path, while a real one exists but is disconnected and broken. LLM tool-calling in the classic sense (a model dynamically choosing which tool to invoke) is not used anywhere — orchestration is deterministic Python, which is a defensible safety choice for a banking use case but should be described accurately, not as "agents deciding."

### Missing Evidence
No trace of any LLM being given tool-choice autonomy; all "agent" boundaries are Python service boundaries, not autonomous LLM decision points.

### Recommended Fixes
Either delete `app/safety/evidence_validator.py`/`guardrails.py` (dead, broken, misleading) or actually wire a real quote-vs-source check into `V2WorkflowEngine._product_evidence()`/`_legal_evidence()`.

### Score Cap Applied
None (no hard-cap trigger conditions were met — see §23).

---

## 8. Technical Execution — 15

### 8.0 Live test result (ground truth, this evaluation run)

```
166 tests collected
3 failed, 163 passed in 46.29s

FAILED tests/rag_mcp/test_transport.py::test_official_mcp_streamable_http_transport_with_service_auth
FAILED tests/test_sales_cases_e2e.py::test_missing_documents_pause_then_uploaded_evidence_resumes_only_downstream
FAILED tests/test_sales_cases_e2e.py::test_multi_product_request_returns_a_bundle_not_a_single_product
```

Root cause, confirmed by direct comparison: `.env:15-16` currently sets `RAG_MCP_EMBEDDING_PROVIDER=gemini` and `KNOWLEDGE_EMBEDDING_PROVIDER=gemini`. The configured Gemini key's project has exhausted prepayment credits (`429 RESOURCE_EXHAUSTED`, established earlier this session via a direct live API call). Re-running the same 2 tests with `KNOWLEDGE_EMBEDDING_PROVIDER=openai RAG_MCP_EMBEDDING_PROVIDER=openai RAG_MCP_ENABLED=false` → **2 passed**. The 3rd failure (`test_official_mcp_streamable_http_transport...`) passes in isolation (`1 passed`) but fails inside the full suite — a test-order/async-cleanup flake in the `mcp` client's `streamable_http_client`, not a logic bug.

| Sub-criterion | Max | Raw Score | Evidence Level | Multiplier | Awarded Score | Evidence | Findings |
| --- | --: | --: | --- | --: | --: | --- | --- |
| A. End-to-end workflow chạy được | 4 | 3.0 | Strong | 1.0 | 3.0 | One full journey (payroll, single-product) verified passing live end-to-end including real action execution. The multi-product / resume journeys currently fail under default config (above). | VERIFIED BY EXECUTION (partial) |
| B. Document Intelligence | 3 | 2.7 | Strong | 1.0 | 2.7 | Real parsers: `pypdf` (PDF), `python-docx` (headings/tables), `openpyxl` (XLSX), plain text for txt/md/csv/json (`app/knowledge/parsers.py`). Structured, provenance-tracked extraction: each `ExtractedField` carries `field_name/value/confidence/source_document_id/source_page/source_section/source_text_span` (`app/intake/extractor.py`). RM review/confirm gate is real and tested (`PATCH .../extracted-profile`, `POST .../confirm-profile`, with `attestation` required). `tests/unit/test_v2_document_parsers.py` passed 4/4 using **real generated PDF/DOCX/XLSX files**, not stubs. OCR is a status label only (`DocumentJobStatus.NEEDS_OCR`) with no OCR engine implemented or in `requirements.txt`. | VERIFIED BY EXECUTION (parsing, RM-review gate); OCR itself is DOCUMENTED BUT NOT IMPLEMENTED |
| C. Code quality và kiến trúc | 2 | 1.3 | Medium | 1.0 | 1.3 | Good: consistent Pydantic `extra="forbid"` schemas, `Protocol`-based adapter interfaces (`app/integrations/enterprise.py`), config centralized in `app/config.py`, no secrets in tracked files. Bad, confirmed by direct reads: **3 orphaned/dead modules** — `app/database.py` (an unused fake in-memory DB, zero imports anywhere), `app/safety/evidence_validator.py` + `guardrails.py` (schema-mismatched, would crash if called, see §7E), and `scripts/export_catalogs.py:6-13` which imports `app.tools.product_tools`/`app.tools.legal_tools` — **files that do not exist** (silently swallowed by `try/except ImportError`, so it degrades to `{}` rather than crashing, but it is dead/broken tooling left in the repo). A naming collision exists between the dead `GuardrailGate` and the live `RiskGuardrailGate`. | VERIFIED BY EXECUTION (grep-confirmed dead imports and unused files) |
| D. Error handling và state management | 2 | 1.6 | Strong | 1.0 | 1.6 | Real optimistic concurrency (`expected_version` mismatch → 409 `STATE_VERSION_CONFLICT` throughout `app/api/v2/router.py`), idempotency keys on case creation and action execution, `ResilientCRMAdapter` circuit-breaker/retry wrapper (`app/integrations/resilient.py`), resume loop cap. Gap: when the embedding provider itself fails (as it does right now), the failure is not surfaced as a clear, distinct error — it silently degrades to an empty product list, which is exactly what produced the 2 live test failures above rather than a loud, diagnosable error. | VERIFIED BY EXECUTION |
| E. Tests và evaluation | 3 | 2.4 | Strong | 1.0 | 2.4 | 166 tests across unit/contract/e2e/rag_mcp layers; a real golden-case evaluation harness (`app/evaluation/runner.py`, 40 cases: intent/retrieval/eligibility) that ran live this session at **40/40, all metrics 1.0, unsafe_approval_rate 0.0** — but see §18 caveat: this run likely benefited from a warm embedding cache from before Gemini's credits ran out, so it does not by itself prove the *current* Gemini path works for novel input (the e2e failures above prove it currently does not). `data/eval/v2/security_cases.json` + `reliability_cases.json` + `app/evaluation/safety_reliability_runner.py` exist for guardrail/reliability evaluation. No single-agent-vs-multi-agent benchmark (§18). | VERIFIED BY EXECUTION, with a caching caveat noted |
| F. Observability | 1 | 1.0 | Strong | 1.0 | 1.0 | Rich per-case AI decision log (`component/mode/model/prompt_version/latency_ms/token_usage/estimated_cost/output_summary/sources/safety` — `app/workflow/engine.py::_ai_log`), hash-chained audit events, `/api/v2/metrics`, `/api/v2/health` (verified live: `{"status":"ok","storage":{"healthy":true,"case_count":15},"indexes":{"product_chunks":6,"legal_chunks":9}}`). | VERIFIED BY EXECUTION |

**Section total: 12.1 / 15**

### Strengths
Real parsers on real files, real optimistic-concurrency and idempotency, a genuinely useful AI decision log, and a working golden-case evaluation harness.

### Weaknesses
3 dead/broken modules sitting in the tree; the currently-failing tests show the default config (`.env`) does not match whatever configuration the developers were actually testing against before this snapshot.

### Missing Evidence
No coverage percentage available — `.coverage` in the repo root is stale and references deleted `app/agents/*` files, so it could not be used.

### Recommended Fixes
See §25 P0-2, P1-5.

### Score Cap Applied
None (tests exist, document processing exists, RM does not type JSON — none of the "Technical Execution" hard caps trigger).

---

## 9. Deployment and Live URL — 15

| Sub-criterion | Max | Raw Score | Evidence Level | Multiplier | Awarded Score | Evidence | Findings |
| --- | --: | --: | --- | --: | --: | --- | --- |
| A. Có live URL | 5 | 0.0 | None | 1.0 | 0.0 | No `render.yaml`, `fly.toml`, `vercel.json`, `Procfile`, or any URL other than `127.0.0.1`/`localhost` anywhere in the repo. | **NOT FOUND IN REPOSITORY** |
| B. Demo ổn định | 4 | 1.0 | Strong (for what was tested) | 1.0 | 1.0 | Local server starts and responds `200` on `/`, `/api/v2/health`, `/docs` (verified live this session). But the exact hero/flagship scenario (multi-product) currently fails end-to-end under the repo's own default `.env` (§8.0) — this is as close to "requires manual data-fixing to demo" as it gets without literally touching the database. | VERIFIED BY EXECUTION — currently unstable for the hero case |
| C. Deployment architecture | 2 | 1.0 | Medium | 0.7 | 1.0 | `Dockerfile` (8 lines: `python:3.11-slim`, installs `requirements.txt`, `EXPOSE 8000`, `CMD uvicorn`) and `docker-compose.yml` (2 services: `workspace` + `rag-mcp`, with `depends_on`) exist and read as syntactically reasonable, but neither has a `HEALTHCHECK`/`healthcheck:` and neither was actually built in this environment (no Docker CLI available). | IMPLEMENTED BUT NOT VERIFIED |
| D. Security và secret management | 2 | 1.3 | Strong (secrets), Medium (env docs) | 1.0/0.7 | 1.3 | No live secrets found anywhere in tracked files (grepped for OpenAI/Google/AQ-style key patterns — zero matches). `.gitignore:69-72` correctly excludes `.env`/`.env.*`. **But**: the tracked `.env.example` is deleted in the working tree with no committed replacement, and the untracked `.env.v2.example` that exists on disk is missing several variables the code actually reads (`GOOGLE_API_KEY`, `DEFAULT_LLM`, `GOOGLE_MODEL`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `RAG_MCP_ENABLED`, `RAG_MCP_PRODUCT_URL`/`TOKEN`, `RAG_MCP_LEGAL_URL`/`TOKEN` — cross-checked against `app/config.py`). File upload is size/type-limited (`settings.MAX_UPLOAD_BYTES`, allowlist extensions). | VERIFIED BY EXECUTION (no secrets) + VERIFIED gap in env template |
| E. Reproducibility | 2 | 0.3 | Weak | 1.0 | 0.3 | README has real run/test commands, but no `pip install` line anywhere in `README.md`. Far more importantly: **`git log` shows only 6 commits, the latest a merge dated 2026-07-17 17:47, and `git status`/`git diff --stat` show 60 untracked files plus 39 modified/deleted tracked files** — essentially the entirety of `app/product`, `app/eligibility`, `app/workflow`, `app/knowledge`, `app/intake`, `app/context`, `app/approval`, `app/actions`, `app/api`, `app/schemas/v2`, `app/storage`, `app/static/app.js` are **untracked**. `origin/main` (the tracked GitHub remote) still contains the deleted V1 code (`app/agents/*`, `app/rag/*`, old test files) and none of the V2 system this report evaluates. A fresh `git clone` reproduces almost nothing described in this report. | VERIFIED BY EXECUTION (`git log`, `git status`, `git diff --stat`) |

**Section total (pre-cap): 3.6 / 15**

### Score Cap Applied
**Hard cap: "Không có live URL → Deployment tối đa 5/15."** The computed raw total (3.6/15) is already below this cap, so the cap is stated for completeness but does not further reduce the score.

### Strengths
Local runnability is real and was verified live; container definitions exist and look reasonable on inspection.

### Weaknesses
No live URL, no CI, no healthcheck, an incomplete env template, and — most severely — the work is not actually in the git history that a judge would see on GitHub.

### Missing Evidence
Actual `docker build`/`docker compose up` success (Docker not available in this evaluation environment).

---

## 10. Feasibility and Three-Month Pilot — 15

| Sub-criterion | Max | Raw Score | Evidence Level | Multiplier | Awarded Score | Evidence | Findings |
| --- | --: | --: | --- | --: | --: | --- | --- |
| A. Use case có thể pilot | 4 | 3.5 | Strong | 1.0 | 3.5 | Scope is small and RM-specific; `Protocol`-based adapters (`CRMPort`/`IAMPort`/`SSOPort`) mean the system does not hard-depend on a real core-banking connection to run — it depends on adapters that currently point at a local SQLite mock, which is exactly the right shape for a pilot to later swap. | VERIFIED BY EXECUTION (adapters real, backend is local SQLite) |
| B. Data readiness | 3 | 2.6 | Strong (design), Medium (real-data presence) | 1.0/0.7 | 2.6 | `plan_v2/17_ASSUMPTIONS_OPEN_QUESTIONS.md`/`18_DATA_STRATEGY_MARKET_SOURCES.md` contain a real Tier A–E data-ownership table and an explicit "no real customer data used in hackathon" statement. `app/data_catalog/registry.py::require_serving_approval()` is **code-enforced**, not just documented — `OperationsService.__init__` calls it and will refuse to serve an unapproved source card. 7 source-card instances exist in `data/catalog/source_cards/`, all explicitly labeled synthetic. | VERIFIED BY EXECUTION (governance gate is real code); no real SHB data present anywhere (**SYNTHETIC DEMO DATA**, as the repo itself declares) |
| C. Integration readiness | 3 | 2.7 | Strong | 1.0 | 2.7 | Real `typing.Protocol` port interfaces separate from concrete SQLite adapters; `ResilientCRMAdapter` proves swappability by wrapping any `CRMPort`. `tests/contract/test_v2_contracts.py::test_tool_registry_allowed_caller_check` (passed live) proves the tool registry's caller-allowlist is enforced, not just declared. Actions are not hardcoded into agent code — they flow through `ActionExecutorV2` with a formal `ActionInput`/`ActionOutput` contract. | VERIFIED BY EXECUTION |
| D. Security và governance | 2 | 1.8 | Strong | 1.0 | 1.8 | Real approval-token gate, RBAC via IAM permission checks (403 on cross-employee case access, tested), hash-chained audit, branch-scoped ACL on knowledge retrieval, prompt-injection + PII guardrails. | VERIFIED BY EXECUTION |
| E. Pilot roadmap | 3 | 1.6 | Medium | 1.0 | 1.6 | `plan_v2/PROGRESS.md` has an explicit MVP-vs-pilot-vs-production gating statement and a blocker line ("Thiếu data/API/SSO-IAM/policy owner/security sign-off thật"). README's "Ranh giới production" section is an honest, specific gap list (SSO/IAM/CRM real systems, sign-offs, OCR, Postgres/Redis, load/pentest/DR testing). But there are no owner names, target dates, or numeric acceptance criteria attached to roadmap items — it reads as an engineering status log with roadmap language, not a pilot plan a business sponsor could sign off on. | DOCUMENTED DESIGN (partial) |

**Section total: 12.2 / 15**

### Strengths
Governance and data-tiering are not just talked about — `require_serving_approval()` is a real, enforced runtime gate. Adapter interfaces genuinely decouple mock from future-real integrations.

### Weaknesses
No named owners/dates/acceptance criteria for a pilot; no real SHB data has touched the system.

### Score Cap Applied
None triggered (human approval exists, so the "no human approval → max 10/15" cap does not apply).

---

## 11. Startup and Business Potential — 15

| Sub-criterion | Max | Raw Score | Evidence Level | Multiplier | Awarded Score | Evidence | Findings |
| --- | --: | --: | --- | --: | --: | --- | --- |
| A. Business value | 4 | 3.0 | Medium | 1.0 | 3.0 | Plausible, mechanism-backed value story (context reuse avoids re-asking, Next Best Question/Action, cross-product bundling) — but zero measured numbers anywhere (correctly not fabricated, per rubric instruction not to reward invented ROI). | DOCUMENTED, mechanism-level VERIFIED |
| B. Khác biệt so với chatbot/RAG thường | 3 | 2.8 | Strong | 1.0 | 2.8 | Document intelligence pipeline + shared `SharedCaseState`/Customer Business Snapshot + real multi-step orchestration + real approval-gated action execution + audit — this is a materially different shape from a single-turn RAG chatbot, and every piece was found in real code, not just described. | VERIFIED BY EXECUTION |
| C. Khả năng mở rộng | 3 | 2.2 | Medium | 1.0 | 2.2 | Product catalog, eligibility rules, and operations SOP are all external JSON/data-driven rather than hardcoded in Python, and integration is behind `Protocol` interfaces — both support extension to other product lines/banks in principle, but no second product line or second bank config was actually built to prove it. | IMPLEMENTED (design supports it), NOT VERIFIED by a second instantiation |
| D. Adoption và vận hành | 3 | 2.3 | Strong | 1.0 | 2.3 | RM-appropriate form UI (no JSON typing in the primary flow — JSON only in a read-only debug tab per the sub-agent's citation of `index.html:158`), evidence/citations surfaced, edit/approve/reject flows real and tested, AI-log/audit tabs in UI. No mechanism found for RM feedback to flow back into model/prompt improvement (profile correction only affects the current case, not future behavior). | VERIFIED BY EXECUTION (UI+API), no continuous-improvement loop found |
| E. Productization | 2 | 1.6 | Strong | 1.0 | 1.6 | Clearly modular service boundaries, config-driven data files, a large and consistent REST surface (`/api/v2/*`, dozens of routes read directly in `app/api/v2/router.py`). | VERIFIED BY EXECUTION |

**Section total: 11.9 / 15**

### Strengths
The differentiation from a plain RAG chatbot is real and demonstrable, not just a marketing claim.

### Weaknesses
No evidence of a second tenant/bank/product-line configuration to prove the "configurable for other banks" claim beyond architectural plausibility.

---

## 12. SHB Challenge Compliance

| Yêu cầu SHB | Điểm 0–5 | Evidence |
| --- | --: | --- |
| Có ít nhất 2–3 specialist agents | 5 | ProductService, EligibilityEngine, OperationsService — distinctly scoped, own data sources (§7B) |
| Planner phân rã và giao task | 5 | `PlannerService.plan()`/`replan()`, dependency-graph `PlanStep`s (§7A) |
| Agents phối hợp trong một yêu cầu phức tạp | 4 | Proven mechanism (§7C), but the exact test for this currently fails under default `.env` |
| Có domain-specific RAG | 4 | Real hybrid retrieval + citations; hallucination-check layer is dead code (§7E) |
| Có tool/function calling | 3 | Real, validated tool *contracts* and a caller-allowlist registry (`tests/contract/test_v2_contracts.py`), but orchestration is deterministic Python, not an LLM dynamically choosing tools |
| Có hành động thực tế, không chỉ sinh text | 5 | Persisted, idempotent, hash-verified CRM/task/opportunity records (§7D) |
| Có shared state hoặc memory | 5 | `SharedCaseState`, persisted with optimistic locking, JSON-Schema + Pydantic dual-validated |
| Có agent trace và task status | 5 | `ai_decision_log`, `audit_events`, `Task.status/dependencies` |
| Có dashboard hiển thị collaboration flow | 2 | UI has AI-log/audit/trace tabs (sequential list), but no dedicated agent-collaboration graph/flow visualization |
| Có human control | 5 | Approval token, reject endpoint, RM profile-correction, attestation checkbox |
| Có so sánh single-agent và multi-agent | 0 | **NOT FOUND IN REPOSITORY** — only a routing *label* (`mode="single_agent_rag"`) exists, zero comparative metrics |
| Có use case thực tế cho SHB | 5 | Grounded directly in the SHB hackathon proposal; RM-only, corporate-banking specific |

**Conclusion: MOSTLY COMPLIANT**

Per the rubric's own rule, the missing single-agent-vs-multi-agent benchmark means this cannot be rated **FULLY COMPLIANT**, regardless of how strong the rest of the table is. It is not **PARTIALLY COMPLIANT** because that downgrade is specifically tied to "no action after agent reasoning," which is false here (actions are real).

---

## 13. Hero Demo Readiness

Scenario: 500-employee manufacturer, 80 suppliers, 40 dealers, manual payroll/AP, dealer reconciliation trouble, dispersed cash flow, short-term capital need, wants ERP integration.

| Step | Status | Evidence |
| --- | --- | --- |
| 1. RM tạo sales case bằng form | PASS | `POST /api/v2/sales-cases`, form fields not JSON, verified by e2e test + UI read |
| 2. RM tải nhiều tài liệu | PASS | Multi-file upload widget + `POST .../documents`, verified live |
| 3. Hệ thống tự parse/OCR/extract | PARTIAL | Parse/extract: PASS (real parsers, tested on real files). OCR: NOT IMPLEMENTED (status label only) |
| 4. RM kiểm tra Customer Business Snapshot | PASS | `GET/PATCH .../extracted-profile`, `confirm-profile` with attestation, tested |
| 5. Product Agent tạo solution bundle | PARTIAL | Mechanism real and previously verified end-to-end this session; **currently fails** under default `.env` for multi-product queries (§8.0) |
| 6. Legal Agent phát hiện dữ liệu còn thiếu | PASS (mechanism) | `EligibilityEngine` → `pending_information` with `missing_information` list, tested |
| 7. Planner re-plan | PASS | `PlannerService.replan()` blocks/unblocks steps based on eligibility outcome, tested |
| 8. Operations Agent tạo Next Best Questions/Actions | PASS | `NextBestService`, `OperationsService.prepare()`, tested |
| 9. RM phê duyệt | PASS | Approval-preview → approve → execute-actions, tested live |
| 10. Opportunity/task được tạo | PASS | Real `SHB-OPP-*`/`SHB-TASK-*` IDs persisted, asserted in a passing test |
| 11. Audit trace được hiển thị | PASS | `GET .../ai-log`, `GET .../audit`, `chain_valid: true`, tested |

**Overall: PARTIAL.** 8 of 11 steps are solidly PASS; step 3 is capped by missing OCR; step 5 (the actual bundle-generation step, arguably the single most important step of the demo) is currently broken by the repository's own default configuration, not by a missing feature.

---

## 14. Document Intelligence Assessment

Already detailed in §8B. Summary: real multi-format parsing (PDF/DOCX/XLSX/TXT/MD/CSV/JSON) with field-level provenance and a mandatory RM confirmation gate before any agent runs — this is a genuine document-intelligence pipeline, not a "paste text" shortcut. OCR is explicitly out of scope and only exists as a status label (`NEEDS_OCR`) — **DOCUMENTED BUT NOT IMPLEMENTED**.

## 15. Multi-Agent Authenticity Assessment

Not "three prompts glued together": each service has its own data source, its own tests, and — critically — changing one agent's output demonstrably changes what a downstream agent produces and what the Planner marks as blocked/ready (§7C, live-tested mechanism). The main authenticity caveat is that no LLM ever dynamically selects a tool or an agent; routing and orchestration are deterministic Python. This is a legitimate, safety-motivated design choice for a banking context, but it means "multi-agent" here is closer to "multi-stage governed pipeline with LLM-assisted steps" than "autonomous LLM agents choosing their own actions" — worth stating precisely rather than glossing over.

## 16. Tool and Action Execution Assessment

Real, per §7D and §10C: formal `ActionInput`/`ActionOutput` contracts (`app/schemas/v2/tool_contracts.py`), a caller-allowlist registry enforced and tested, idempotency-keyed execution, and persisted results distinguishable from a fresh call vs a replay (`idempotent_replay` flag). No action bypasses approval — verified by `ActionExecutorV2.execute()` re-checking eligibility/evidence independent of the approval token.

## 17. Evidence and Guardrail Assessment

Retrieval/citation: real (§7E). Hallucination/unsupported-claim checking: weak in the live path (`bool(quote)` only), with a more rigorous but disconnected and broken implementation sitting unused. Guardrails (prompt injection, PII redaction, approval-gating, fail-closed risk classification): real and tested (§7F). Net: grounding *exists* but is *citation-only*, not *verified-against-source* in production right now.

## 18. Single-Agent vs Multi-Agent Benchmark

**BENCHMARK NOT IMPLEMENTED.** No dataset, script, or numeric result comparing single-agent vs multi-agent performance exists anywhere in the repository (confirmed by targeted search for `single_agent`, `benchmark`, `comparison`). The only related artifact is a routing *label* (`mode: "single_agent_rag"` in `app/workflow/engine.py:104`) attached when `ComplexityRouter` picks the simple path — this records which path was taken, not how the two paths compare.

Additionally: the golden-case evaluation (`app/evaluation/runner.py`, 40/40 passing) was run live this session under the *default* `.env` (Gemini provider) and still passed 100%. Given that the same default config demonstrably fails on **novel** multi-product query text (§8.0), the most likely explanation is that the golden-case queries' embeddings were already warm in `data/vector_db/gemini_vector_cache.json` from before the Gemini account's credits were exhausted. This is flagged explicitly so the 40/40 result is not over-read as proof the current live Gemini path works generally — it does not, for new text.

**To close this gap, concretely:**
- Dataset: extend `data/eval/v2/golden_cases.json` (or a new `data/eval/v2/routing_cases.json`) with ~20 multi-intent cases that force `ComplexityRouter.is_complex() == True`, paired with the same cases forced through the simple/single-agent path (a `--force-simple` flag on `app/evaluation/runner.py` would work).
- Script: extend `app/evaluation/runner.py` to run each case both ways and record: correct-product recall, missing-information recall, citation coverage, and latency for each path.
- Module to change: `app/evaluation/runner.py`, `app/workflow/router.py` (add a bypass hook for the benchmark).
- Acceptance threshold: needs the team to confirm (e.g., "multi-agent path must recover ≥90% of missing-information cases that the single-agent path misses").

## 19. Security Review

- No live secrets found in tracked source (`sk-`, `AQ.`, `AIza` patterns all grepped, zero matches).
- `.gitignore` correctly excludes `.env`/`.env.*`.
- `.env.example` is git-tracked at HEAD but deleted from the working tree with no committed replacement; `.env.v2.example` exists but is untracked and incomplete (§9D).
- RBAC is real: `require_permission()`, case-ownership checks returning 403 on cross-employee access (tested).
- Input safety: prompt-injection regex + PII redaction, tested, wired into every write endpoint.
- File upload: size-limited (`MAX_UPLOAD_BYTES`), type-allowlisted, content-hashed, quarantines on injection detection (`quality["publishable"]` gate in `app/api/v2/router.py:1163-1179`).
- No authentication beyond `X-Employee-ID`/`X-Session-ID` headers checked against a local IAM table — acceptable for an MVP, explicitly flagged by the README itself as needing a real SSO/session gateway in production.

## 20. Test Coverage

166 tests collected; 163 passed / 3 failed at the moment of this audit (root-caused in §8.0). No usable coverage percentage — the committed `.coverage` file is stale (references deleted `app/agents/*` paths) and could not be used to compute a current number; `pytest-cov` is present in `requirements.txt` but no fresh coverage run's summary was captured as part of this audit's command budget.

## 21. Deployment Readiness

Not ready. No live URL, no CI, incomplete env template, and — the dominant fact — the code a judge would actually receive via `git clone` of the tracked remote is the old V1 system, not what this report evaluated. Local `Dockerfile`/`docker-compose.yml` look reasonable on inspection but were not build-verified in this environment.

## 22. Red Flags

| ID | Severity | Finding | File Evidence | Impact | Fix |
| --- | --- | --- | --- | --- | --- |
| R1 | **Critical** | Nearly the entire V2 implementation (everything scored positively in §6–§11) is **not committed to git** and has never reached the tracked GitHub remote. `git log` shows 6 commits, latest 2026-07-17 17:47 ("Merge branch 'mvp/multi-agent-backend'"); `git status` shows 60 untracked files and 39 modified/deleted tracked files, covering essentially all of `app/product`, `app/eligibility`, `app/workflow`, `app/knowledge`, `app/intake`, `app/context`, `app/approval`, `app/actions`, `app/api`, `app/schemas/v2`, `app/storage`, `app/static/app.js`. `origin/main` still has the old V1 code. | `git log --oneline`, `git status --porcelain`, `git diff --stat HEAD` (all executed live) | Submission readiness / Deployment / Reproducibility | Commit and push before any submission deadline — see §25 P0-1 |
| R2 | High | The default, repository-shipped `.env` breaks the flagship demo scenario right now: `KNOWLEDGE_EMBEDDING_PROVIDER=gemini`/`RAG_MCP_EMBEDDING_PROVIDER=gemini` point at a Gemini key with exhausted billing credits. Confirmed by a live 2-test pass/fail flip when switching to `openai`. | `.env:15-16`; live `pytest` before/after comparison | Problem Relevance §6C/D, AI-Native §7C, Deployment §9B | Change `.env` defaults to `openai` (already the code-level fallback in `app/knowledge/index.py::create_embedding_provider()`), or restore Gemini billing |
| R3 | High | `app/safety/evidence_validator.py` and `app/safety/guardrails.py` are dead code that references non-existent fields on the current data model (`source_doc`, `page_or_section`, `state.audit_log`, `state.legal_result`, `state.approval_status`) and would raise `AttributeError` if ever actually invoked. They are imported only by `app/safety/__init__.py`, nowhere in the live pipeline. The real evidence gate in the live path is a much weaker `bool(quote)` check. A prior evaluation pass on this same repo (the report this one replaces) cited this exact dead file as "Strong" evidence for RAG grounding — a clear example of scoring from a filename/docstring instead of verifying the code runs. | `app/safety/evidence_validator.py:22,28,35,39`; `app/safety/guardrails.py:35,38`; confirmed against `app/schemas/v2/shared_case_state.py` field names via grep | AI-Native §7E, Code Quality §8C | Delete the dead module or wire a real check into `V2WorkflowEngine._product_evidence()`/`_legal_evidence()` |
| R4 | Medium | `app/database.py` (a fake in-memory `SimpleDatabase`, explicitly commented "giả lập cơ sở dữ liệu thật") is never imported anywhere in the codebase — confirmed by a repo-wide grep with zero matches. | `app/database.py`; grep result: no matches | Code Quality §8C | Delete |
| R5 | Medium | `scripts/export_catalogs.py:6-13` imports `app.tools.product_tools`/`app.tools.legal_tools`, which do not exist (only `app/tools/operations_tools.py` and `__init__.py` exist under `app/tools/`). Wrapped in `try/except ImportError` so it silently degrades to `{}` rather than crashing — but the script is effectively dead/broken. | `scripts/export_catalogs.py:6-13`; `app/tools/` directory listing | Code Quality §8C | Fix imports or delete the script |
| R6 | Medium | README's stated test snapshot ("`172 passed`", dated 2026-07-17) does not match the live, current test count (166 collected total, 163 passed as of this audit). README also claims "dense fallback hiện là deterministic hash," but no hash-based embedding fallback class exists anywhere in the current codebase (`create_embedding_provider()` supports only `openai`/`gemini` and raises `ValueError` otherwise). | `README.md:116,140`; live `pytest --collect-only` → 166; grep for `DeterministicHashEmbedding`/`HashEmbedding` → no code matches | Code Quality / README accuracy | Update README to match current code and current live test results |
| R7 | Medium | `tests/rag_mcp/test_transport.py::test_official_mcp_streamable_http_transport_with_service_auth` fails when run as part of the full suite (`anyio` "Attempted to exit cancel scope in a different task than it was entered in") but passes standalone — a test-isolation/async-cleanup flake, not a logic defect, but it reduces the reliability of "all green" as a signal. | Full-suite vs standalone `pytest` runs (both executed live) | Test reliability | Isolate the MCP client's async lifecycle per test (e.g. dedicated event loop / explicit teardown) |
| R8 | Low | Golden-case evaluation (40/40) may be partly riding on a warm embedding cache rather than proving the live Gemini path works for novel input (§18). Not fabricated, just potentially misleading if quoted without this caveat. | `data/vector_db/gemini_vector_cache.json` (cache keyed by SHA-256 of text, persists across runs); cross-referenced against the live e2e failures for novel text | Evaluation credibility | Add a "cold cache" evaluation mode (fresh cache dir) as part of CI |

No evidence was found of: hard-coded per-company recommendations, fabricated agent traces, fake "loading" states with no real work behind them, opportunities reported as created without a database write, or an agent holding unrestricted tool permissions (the tool registry explicitly enforces `allowed_callers`, tested).

## 23. Score Caps Applied

Only one cap was triggered and it is already naturally satisfied by the raw computed score:

- **"Không có live URL" → Deployment tối đa 5/15.** Raw Deployment total computed to 3.6/15, already under the cap.

All other listed hard caps were checked and **not** triggered: specialist agents are real (not capped to 8/20 or 10/20), tool/action execution is real (not capped to 12/20), shared state exists (not capped to 11/20), evidence/citation exists — even though the hallucination-*check* is weak, citations themselves are present (not capped to 13/20), human approval exists (Feasibility not capped to 10/15), RM does not type JSON (Technical Execution not capped to 11/15), document processing exists (not capped to 10/15), tests exist (not capped to 9/15). The repository is far beyond "README only" (not capped to 35/100 overall) and the backend is real, not a UI mock (not capped to 45/100 overall).

## 24. Current vs Potential Score

```
Current verified score: 77.5 / 100
```

```
ESTIMATED POTENTIAL — NOT VERIFIED
Potential score after critical (P0) fixes: ~87 / 100
Potential score after all recommended (P0+P1+P2+P3) fixes: ~91 / 100
```

These are forward-looking estimates only, based on which specific sub-criteria would most plausibly move and by how much (mainly Deployment, once a live URL + stable default config exist, and Technical Execution/AI-Native once the dead evidence-validator and env-config issues are resolved). They are not a promise and were not computed by re-running the rubric against a hypothetical future state.

## 25. Prioritized Improvement Backlog

| Priority | Fix | Affected criterion | Estimated score impact | Effort | Repository path |
| --- | --- | --- | --- | --- | --- |
| P0 | Commit and push the entire V2 implementation to `origin/main` | Deployment §9E, Reproducibility, overall submission validity | Very high (this is what makes every other fix visible to a judge at all) | S | whole repo (`git add`, `git commit`, `git push`) |
| P0 | Change `.env` `KNOWLEDGE_EMBEDDING_PROVIDER`/`RAG_MCP_EMBEDDING_PROVIDER` from `gemini` to `openai` (or restore Gemini billing) so the flagship multi-product scenario works by default | Problem Relevance §6C/D, AI-Native §7C, Technical Execution §8A | +2–3 across those sections | S | `.env` |
| P0 | Stand up an actual reachable live URL (any free-tier host is enough to remove the hard cap) | Deployment §9A | Up to +10 to Deployment alone | M | new: deployment config |
| P0 | Fix the order-dependent failure in `tests/rag_mcp/test_transport.py::test_official_mcp_streamable_http_transport_with_service_auth` | Technical Execution §8E | +0.3 | S–M | `tests/rag_mcp/test_transport.py`, `services/rag_mcp` client lifecycle |
| P1 | Delete or properly wire `app/safety/evidence_validator.py`/`guardrails.py` into the live evidence-check path | AI-Native §7E, Code Quality §8C | +1–1.5 | M | `app/safety/evidence_validator.py`, `app/safety/guardrails.py`, `app/workflow/engine.py` |
| P1 | Commit a complete `.env.example`/`.env.v2.example` covering every variable read in `app/config.py` | Deployment §9D/E | +0.5–1 | S | `.env.v2.example`, `app/config.py` |
| P1 | Build a real single-agent-vs-multi-agent benchmark (dataset + script + metrics) | SHB Challenge Compliance, AI-Native §7 | Unlocks "FULLY COMPLIANT" | M | `app/evaluation/runner.py`, new `data/eval/v2/routing_cases.json` |
| P1 | Correct README's stale claims (test count "172 passed" vs live 166/163, "deterministic hash" fallback claim that no longer exists in code) | Code Quality §8C | +0.3 | S | `README.md` |
| P2 | Add CI (GitHub Actions) running `pytest` + both evaluation runners on every push | Deployment §9C, Technical Execution §8E | +0.5–1 | S–M | new: `.github/workflows/ci.yml` |
| P2 | Implement at least one real OCR engine for scanned PDFs (currently only a `NEEDS_OCR` status label) | Technical Execution §8B, Hero Demo §13 step 3 | +0.5 | M | `app/knowledge/parsers.py`, `requirements.txt` |
| P3 | Delete `app/database.py` (unused) and fix or delete `scripts/export_catalogs.py`'s broken imports | Code Quality §8C | +0.2 | S | `app/database.py`, `scripts/export_catalogs.py` |
| P3 | Add a "cold cache" mode to the golden-case evaluation to avoid the warm-cache credibility caveat (§18) | Evaluation credibility | +0.2 | S | `app/evaluation/runner.py` |

## 26. Top 10 Required Fixes

1. **Commit and push the uncommitted V2 system.** *Problem:* `git status` shows 60 untracked + 39 modified/deleted files covering essentially all of `app/` beyond the old V1 skeleton that remains on `origin/main`. *Why it costs points:* a judge evaluating the GitHub repo, not this local folder, would see almost none of what this report scored. *File/component:* the whole working tree. *Expected result:* `git status` clean, `origin/main` matches the working tree. *How to verify:* `git log origin/main` shows the new commit; a fresh `git clone` builds and runs. *Score impact:* enables every other point in this report to actually count. *Size:* S.

2. **Fix the default embedding provider in `.env`.** *Problem:* `.env:15-16` sets `KNOWLEDGE_EMBEDDING_PROVIDER=gemini`/`RAG_MCP_EMBEDDING_PROVIDER=gemini` against a Gemini key with exhausted billing, breaking the flagship multi-product demo. *Why it costs points:* Problem Relevance §6C/D, AI-Native §7C, Technical Execution §8A. *File:* `.env`. *Expected result:* `tests/test_sales_cases_e2e.py` passes all 5 cases under the checked-in default config, not only with a manual env override. *How to verify:* `pytest tests/test_sales_cases_e2e.py` with no env overrides → 5 passed. *Score impact:* +2–3 across 3 sections. *Size:* S.

3. **Get a live URL.** *Problem:* none exists. *Why it costs points:* hard-caps Deployment at 5/15 regardless of everything else. *File/component:* new deployment config (Dockerfile/compose already exist and can likely be reused as-is). *Expected result:* a reachable HTTPS URL serving `/` and `/api/v2/health`. *How to verify:* `curl` from outside the dev machine. *Score impact:* up to +10 in Deployment. *Size:* M.

4. **Wire a real evidence/hallucination check into the live path, or delete the dead one.** *Problem:* `app/workflow/engine.py:429,443` only checks `bool(quote)`; the more rigorous `app/safety/evidence_validator.py` is dead, broken (wrong field names), and hardcoded to a broken Gemini call. *Why it costs points:* AI-Native §7E, Code Quality §8C. *File:* `app/workflow/engine.py`, `app/safety/evidence_validator.py`. *Expected result:* either the dead file is removed, or `_product_evidence()`/`_legal_evidence()` call a real quote-vs-source check. *How to verify:* a new unit test asserting a fabricated/altered quote is flagged `is_valid=False`. *Score impact:* +1–1.5. *Size:* M.

5. **Build a single-agent vs multi-agent benchmark.** *Problem:* completely absent — only a routing label exists. *Why it costs points:* blocks "FULLY COMPLIANT" in the SHB Challenge Compliance table outright, and is explicitly requested by the rubric. *File:* extend `app/evaluation/runner.py` + a new `data/eval/v2/routing_cases.json`. *Expected result:* a report showing product-recall/missing-info-recall/citation-coverage/latency for the same cases run both ways. *How to verify:* run the extended evaluator, inspect the JSON output. *Score impact:* unlocks FULLY COMPLIANT status; some AI-Native credit. *Size:* M.

6. **Complete the `.env.v2.example` template.** *Problem:* missing `GOOGLE_API_KEY`, `DEFAULT_LLM`, `GOOGLE_MODEL`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `RAG_MCP_ENABLED`, `RAG_MCP_PRODUCT_URL`/`TOKEN`, `RAG_MCP_LEGAL_URL`/`TOKEN` relative to what `app/config.py` actually reads. *Why it costs points:* Deployment §9D/E reproducibility. *File:* `.env.v2.example`, cross-check against `app/config.py`. *Expected result:* every `os.getenv(...)` call in `app/config.py` has a matching line in the example file. *How to verify:* a small script diffing the two. *Score impact:* +0.5–1. *Size:* S.

7. **Fix the order-dependent RAG-MCP transport test failure.** *Problem:* `tests/rag_mcp/test_transport.py::test_official_mcp_streamable_http_transport_with_service_auth` fails in the full suite, passes standalone (`anyio` cancel-scope error). *Why it costs points:* Technical Execution §8E — reduces trust in "all green." *File:* `tests/rag_mcp/test_transport.py`, the `mcp` client lifecycle in `services/rag_mcp`. *Expected result:* full-suite run is 166/166 with no order dependency. *How to verify:* `pytest -q` (full suite) passes cleanly. *Score impact:* +0.3. *Size:* S–M.

8. **Correct README's stale claims.** *Problem:* README states "172 passed" (2026-07-17 snapshot) and "dense fallback hiện là deterministic hash," neither of which matches the current, live-verified state (166 collected/163 passed; no hash-fallback class exists in code). *Why it costs points:* Code Quality §8C ("README không khớp code" is an explicit red-flag category). *File:* `README.md:116,140`. *Expected result:* README numbers match a fresh `pytest` run. *How to verify:* re-run `pytest -q` and diff against the README claim. *Score impact:* +0.3. *Size:* S.

9. **Add CI.** *Problem:* no `.github/workflows` or any CI config exists. *Why it costs points:* Deployment §9C, general engineering maturity signal. *File:* new `.github/workflows/ci.yml`. *Expected result:* pytest + evaluation runners execute automatically on push/PR. *How to verify:* a green check on the next push. *Score impact:* +0.5–1. *Size:* S–M.

10. **Remove dead code.** *Problem:* `app/database.py` (unused fake DB) and `scripts/export_catalogs.py`'s imports of nonexistent `app.tools.product_tools`/`legal_tools` sit in the tree unused/broken. *Why it costs points:* Code Quality §8C. *File:* `app/database.py`, `scripts/export_catalogs.py`. *Expected result:* both either deleted or fixed to actually work. *How to verify:* grep confirms zero remaining references to deleted files; `scripts/export_catalogs.py` runs without silently falling back to `{}`. *Score impact:* +0.2. *Size:* S.

## 27. Submission Readiness Checklist

| Hạng mục | Status | Evidence |
| --- | --- | --- |
| Slide | MISSING | No `.pptx`/`.key`/slide file found in repo |
| Demo dưới 5 phút | UNVERIFIED | No video found; manual walkthrough would currently hit the R2 failure on the flagship scenario unless env is fixed first |
| GitHub repository | PARTIAL | Remote exists (`ShayNeeo/VAIC2026`), but `origin/main` does not contain the V2 system (§22 R1) |
| README | PARTIAL | Detailed and mostly accurate, but contains stale claims (§22 R6) |
| Live URL | MISSING | Confirmed absent |
| AI collaboration log | READY | `ai_decision_log` + `/api/v2/{case}/ai-log`, verified live |
| Synthetic demo data | READY | Explicitly labeled **SYNTHETIC_DEMO_DATA** throughout `README.md` and `data/catalog/source_cards/*` |
| Test script | READY | `pytest`, `app.evaluation.runner`, `app.evaluation.safety_reliability_runner`, all executed successfully in this audit |
| Single-agent comparison | MISSING | Confirmed absent (§18) |
| Architecture diagram | READY | `docs/SHB_MULTI_AGENT_WORKFLOW_DIAGRAM_MAPPING.md` + the proposal docx diagram (not re-verified pixel-by-pixel this pass, but present) |
| Security statement | PARTIAL | README's "Ranh giới production" section covers this informally; no dedicated security doc |
| Pilot roadmap | PARTIAL | `plan_v2/PROGRESS.md` + README's production-boundary section, but no owners/dates (§10E) |
| Demo fallback video | MISSING | No video file found anywhere in repo |

## 28. Evidence Appendix

Key file:line citations used throughout this report (non-exhaustive, see inline citations above for full list):

- `app/workflow/engine.py:85-107` (complexity routing branch), `:187-374` (`_analysis`, the core orchestration loop), `:376-393` (`_apply_risk_gate`), `:429,443` (shallow evidence-validity check)
- `app/workflow/planner.py:24-70` (`replan`, 3-branch dependency mutation)
- `app/workflow/risk_gate.py:47-78` (`RiskGuardrailGate.evaluate`, fail-closed default)
- `app/workflow/router.py:25,39-56` (`ComplexityRouter`, allowlist design)
- `app/eligibility/engine.py:115-125` (`_aggregate`, blocking-severity priority order)
- `app/operations/service.py:56-120` (`prepare`, draft-only artifacts, disclaimers)
- `app/actions/executor.py:22-63` (idempotent, re-validated action execution)
- `app/integrations/enterprise.py:21-37` (`Protocol`-based ports), `:55-113` (SQLite adapters)
- `app/safety/evidence_validator.py:22,28,35,39` (dead code, broken field references, hardcoded Gemini)
- `app/safety/__init__.py:1-2` (the only importer of the dead evidence validator)
- `app/knowledge/index.py:163-175` (`create_embedding_provider`, code-level default is `openai`)
- `.env:15-16` (working default overrides this to `gemini`)
- `app/database.py` (confirmed zero importers)
- `scripts/export_catalogs.py:6-13` (broken imports, silently swallowed)
- `tests/test_sales_cases_e2e.py` (all 5 e2e scenarios, incl. the 2 currently failing)
- `tests/contract/test_v2_contracts.py:249-272` (tool registry enforcement, passed live)
- `README.md:116,140` (stale claims)

## 29. No-Hallucination Verification

Self-check against §19 of the instructions:

- No score was awarded for a README-only claim without corresponding code (every "Strong" evidence rating above cites a specific file:line or a specific test that was executed live in this session).
- Real code was read directly for every scored sub-criterion; no scoring was based on a summary of a summary.
- `pytest`, the evaluation runner, and a live `uvicorn` server were actually executed in this session, with raw output captured and quoted above (§5, §8.0).
- Failing commands (3 test failures, `docker --version` not found) are reported explicitly rather than omitted.
- Evidence multipliers were applied and shown in each scoring table; no score was rounded until the section totals.
- Multi-agent authenticity was explicitly distinguished from prompt-chaining (§15) — the collaboration claim rests on a live-tested mechanism (blocked/ready step propagation), not narrative description.
- Every action-execution claim was checked against an actual assertion in a test that ran and passed (`opportunity_id.startswith("SHB-OPP-")`), not just code that looks like it should work.
- The "RM must type JSON" question was explicitly checked (no — form-based, JSON only in a read-only debug tab).
- Document intake was checked file-by-file, not assumed from the README description.
- Human approval was checked as an enforced code path (`ActionExecutorV2` re-validates independent of the token), not just a UI button.
- The live URL question was checked by searching for actual hosting config files, not asserted from absence of mention.
- No numeric business-value/ROI figures were invented; §11A explicitly declines to score fabricated ROI.
- Every file path referenced in this report was confirmed to exist via direct `Read`/`Grep`/`Glob` calls or by a sub-agent whose citations were spot-checked against the same tools.
- Where this report replaces a prior, more lenient self-assessment at the same path, the specific contradicting evidence is cited (§22 R3) rather than the prior report simply being silently discarded.

No violations found requiring correction before saving this report.
