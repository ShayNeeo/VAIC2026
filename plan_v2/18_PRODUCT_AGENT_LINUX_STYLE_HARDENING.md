# Plan V2-Addendum: Product Agent Hardening (Linux-Kernel Maintainability)

**Owner**: Full MCP deploy dev (Product Agent only — 1 of 3 specialist agents)
**Branch**: `feat/product-agent-hardening` (off `origin/main`)
**Source of truth**: `SHB_Corporate_Sales_MVP_Data_Blueprint_V3_Proposal.docx` + `mcp_common/schemas.py`

## 0. Scope (what I own)
Product Agent MCP server only:
- `servers/product_agent/server.py` (MCP entrypoint, 3 tools)
- `servers/v3_product_agent/{product,rag,safety}/*.py`
- `tests/product_agent/*`
- `docs/MCP_PRODUCT_AGENT_VIETNAMESE.md`

Legal / Operations / Approval agents are siblings — I only align interfaces, not implement them.

## 1. Review Findings (current code)

| # | Location | Issue | Blueprint ref | Severity |
|---|----------|-------|---------------|----------|
| P-1 | `server.py` | Pipeline monolith: orchestration, schema-build, guardrail wiring in one fn; `legal_result={}` hardcoded; no trace/observability hook | §14.2, §16.2 | mid |
| P-2 | `server.py` | `EvidenceItem(**e)` re-wraps already-built `EvidenceItem` (double model construction) | §3.4 | low |
| P-3 | `server.py` | Output lacks F-04 required fields: `score_components`, `prerequisites`, `evidence_ids`, `provenance` | F-04 | high |
| P-4 | `matcher.py` | Business rules as inline `_has()` magic strings; no `ProductNeed` enum; not data-driven | B3/PR1 | high |
| P-5 | `matcher.py` | `missing_parameters` is a placeholder string; no real gap detection | F-04 | mid |
| P-6 | `matcher.py` | Gemma-off → reason falls back to raw f-string; not deterministic/structured | §7 | mid |
| P-7 | `catalog.py` | Dict literals store pydantic objects; no `ProductCatalogEntry`; no compatibility graph | §9.3 | mid |
| P-8 | `verify.py` | `NUMERIC_EXACT` enum never used; fee/limit not extracted from catalog for exact compare | §11.1 | mid |
| P-9 | `retriever.py` | Sparse gate `0.40` hardcoded; `./data` cache path not configurable; no effective-date/ACL filter hook | §10.2 | low |
| P-10 | tests | No test for `NUMERIC_EXACT`, deterministic reason, provenance, missing-param detection | §17 | mid |

## 2. Design Principles (Linux-kernel style)
1. **Single responsibility per module.** `server.py` = wiring only. `pipeline.py` = orchestration. `matcher.py` = decision logic. `catalog.py` = data. `verify.py` = evidence truth.
2. **Explicit over implicit.** No magic strings for needs; a typed `ProductNeed` enum drives matching.
3. **Fail closed.** Missing data → `pending_information`, never `eligible=True`. (§11.1)
4. **Deterministic by default.** Gemma is an *optional* reasoner; pipeline yields valid output with zero LLM calls. (§10.3)
5. **One source of truth.** Catalog is the only place product facts live; matcher/verify read it, never duplicate.
6. **Documented invariants.** Every public fn has a docstring stating pre/post/why.
7. **No silent loss.** `EvidenceItem` constructed once; passed by reference.

## 3. Concrete Changes

### 3.1 `product/catalog.py`
- Add `ProductNeed` enum (`payroll`, `cash_management`, `collection`, `working_capital`).
- Keep `V3_PRODUCT_CATALOG` as `Mapping[str, ProductCatalogEntry]` (typed, not loose dict).
- Add `NEED_KEYWORDS: Dict[ProductNeed, Tuple[str,...]]` (signal → keywords).
- Add `COMPATIBILITY_GRAPH` (compatible/exclusion per product) for bundle logic.

### 3.2 `product/matcher.py`
- `ProductMatcher.select_needs(request, profile) -> List[ProductNeed]` — pure, deterministic.
- `ProductMatcher.score(pid, request, profile) -> ProductMatchScore` — keeps V3 components.
- `ProductMatcher.reason(pid, request, profile) -> str` — deterministic template when Gemma off; LLM only polishes.
- `ProductMatcher.detect_missing_parameters(request, profile, selected) -> List[str]` — real gap detection (e.g. unknown funding amount).
- Build `ProductRecommendation` with `evidence` linked to `EvidenceItem` (built once in verify, passed in).

### 3.3 `safety/verify.py`
- Add `NUMERIC_EXACT` path: extract fee/limit value+unit from `V3_PRODUCT_CATALOG[pid].fees_limits`; exact compare claim vs catalog.
- Reuse catalog as canonical source text (no duplicate `_build_sources`).
- Return `(List[EvidenceItem], summary)`; items constructed once.

### 3.4 `rag/retriever.py`
- Move `SPARSE_GATE` to `settings` (configurable, default 0.40).
- Cache path via `settings.EMBEDDING_CACHE_PATH`.
- Add `effective_date`/`acl` filter hook (no-op for synthetic, ready for real).

### 3.5 `server.py` → add `product/pipeline.py`
- Extract `run_pipeline(request) -> PipelineResult` (pure orchestration, returns typed result).
- `server.py` only registers tools + maps `PipelineResult` → MCP response.
- Wire `trace_id` into observability stub (log JSON with event code, no PII).
- Pass `legal_result` through (not hardcoded `{}`); default safe `pending_review` if absent.
- Build `ProductResult` with F-04 fields: `score_components`, `prerequisites`, `evidence_ids`, `provenance` (catalog version/owner).

### 3.6 Tests
- Add `tests/product_agent/test_catalog.py`: enum/keywords/compat graph.
- Add `tests/product_agent/test_pipeline.py`: full pipeline deterministic (Gemma off), provenance, missing-param.
- Extend `test_verify.py`: `NUMERIC_EXACT` fee exact-match.
- Extend `test_matcher.py`: reason deterministic, score bounds.

## 4. Acceptance (from blueprint §17 + §18.1)
- `Contract-valid outputs 100%` — `ProductResult` validates against `mcp_common/schemas.py`.
- `Unnecessary clarification < 5%` — auto-fill from profile.
- `Unsafe external action = 0` — Product Agent exposes no write tool (MCP-07 holds).
- `Citation correctness 100%` — every claim tied to catalog version/section.
- `Eligibility unsafe pass = 0` — Product Agent never sets `eligible` (Legal owns it).
- Full suite green (currently 139; target ≥ 150 with new tests).

## 5. Out of scope (siblings)
- Legal Agent rule registry (friend #1 owns).
- Operations Agent dedup/executor (friend #2 owns).
- Orchestrator DAG (separate owner).
- Real embedding model, CRM/DMS adapters.

## 6. Definition of Done
- [ ] `plan_v2/PROGRESS.md` updated with Product Agent row (was "Deterministic MVP" → "V3 hardened").
- [ ] All P-1..P-10 addressed.
- [ ] New tests pass; total suite ≥ 150.
- [ ] `docs/MCP_PRODUCT_AGENT_VIETNAMESE.md` updated (F-04 fields, enum-driven matching, fail-closed).
- [ ] PR created from `feat/product-agent-hardening` → `main`.
