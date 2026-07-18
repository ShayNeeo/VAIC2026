# Role-Aware Repository Verification Report

**Audit type:** Read-only. No code was modified, no tests were changed, no
commits/pushes were made. All findings below were produced by reading source
files and by *executing* code (pytest, `fastapi.testclient.TestClient`
against the real `app.main.app`) — not by inspection alone, except where a
finding is explicitly marked as static/code-reading only.

**Source-of-truth note (must read first):** The prompt that requested this
audit referenced a `<PLAN_V3_PATH>` document and said to fall back to
"content provided alongside this prompt" if that document was not in the
repository. Neither the file path nor the fallback content was actually
supplied. A repository-wide search (filenames, file contents, git log,
branch names) found **no standalone "Role-Aware Employee Copilot v3" plan
document** anywhere in this repo. The closest artifact is
`plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md`, which the *existing*
`app/context/employee_service.py` cites by name for its fail-closed IAM
design — that pre-existing service is more aligned with typical "v3-style"
requirements than the new code this audit targets (see §6/§7). Per the
prompt's own fallback instruction, this audit uses the requirements spelled
out directly in the prompt itself (§2, §6–§19 of the prompt) as the
checkable source of truth, and flags this missing document as a limitation
rather than inventing plan content.

---

## 1. Executive Summary

A real, executable "Role-Aware Employee Copilot & Work Optimization Layer"
exists in this repository, on branch `feat/v2-employee-copilot-layer`
(commit `694df1b`, already pushed to `origin`, **not yet on `main`**). It is
not vaporware: 281 tests collect and run, the 12 named security tests exist
verbatim and pass, a real 30-case Next Best Work benchmark executes and
prints real KPIs, and the API responds correctly to valid/invalid/expired/
IAM-down identity headers when probed live with `TestClient`.

However, execution testing surfaced concrete, severe gaps that static
reading alone would have missed or that the test suite does not catch:

1. **Three of the endpoints the frontend actually calls are broken** —
   confirmed with real HTTP calls, not inference (§14, §17).
2. **Two parallel, disconnected "IAM" implementations exist side by side.**
   The new layer does not use the pre-existing, more correct
   `IAMPort`/`SSOPort` (`app/integrations/enterprise.py`) or
   `EmployeeContextService` (`app/context/employee_service.py`); it
   reimplements identity/role/permission lookup from scratch with a weaker
   design (§6, §7).
3. **Identity is an unauthenticated, client-supplied HTTP header**
   (`X-Employee-ID`) with no token/session/signature verification. Anyone
   can become any employee, including `MGR-HN-01`, by setting a header
   (§7).
4. **Running the test suite permanently destroys the persistent demo
   database** the live app and hero-demo depend on, because the new tests
   write to the same on-disk SQLite file as the running app with no test
   isolation (§16, §13).
5. **No tool/action-execution permission revalidation** exists in this
   layer at all.

None of these five are hypothetical; each has direct file:line or HTTP
request/response evidence below.

## 2. Final Score

```text
FINAL SCORE: 59 / 100
CLASSIFICATION: 50-69  Prototype only
```

See §19 for the full rubric breakdown and §23 for the hard-cap check.

## 3. Confidence Level

**HIGH.** Nearly every claim below is backed by an actually-executed
command or HTTP call in this session (pytest runs, `TestClient` probes
against the live `FastAPI` app object), not just static code reading. The
few exceptions (frontend browser rendering, real external SSO) are
explicitly marked `UNVERIFIED DUE TO ENVIRONMENT LIMITATION` or
`EXTERNAL DEPENDENCY`.

## 4. Repository and Git State

```text
Repository root: c:\Users\Admin\Desktop\hakathon
Current branch:  feat/v2-employee-copilot-layer  (pushed to origin)
HEAD:            694df1b feat(v2): add Role-Aware Employee Copilot layer with fail-closed IAM
Parent (main):   6d22f62 (main does NOT yet contain this feature)
Working tree:    clean of tracked changes (git diff --stat: empty)
Untracked only:  scratch/, tmp_test/ (pre-existing/pytest artifacts, not part of this audit)
```

Frontend: this repository also contains a Flutter app under `lib/`, which is
a **separate** frontend from the one this audit exercised. The Role-Aware
Employee Copilot's actual UI wiring (`routeWorkspace`, personalization
panel, SSO switcher mentioned in the commit message) lives in
`app/static/app.js` + `app/static/index.html`, served by the same FastAPI
app (`app/main.py`). This is treated as **in-repo, in-scope** frontend, not
`EXTERNAL DEPENDENCY` (see §20 for what was and wasn't checked there).

## 5. Commands Executed

```text
git status --short / git log --oneline -10 / git diff --stat / git fetch --all
python -m pytest --collect-only -q                              -> 281 tests collected
python -m pytest -q --basetemp=./tmp_test                        -> 1 failed, 280 passed, 96 warnings, 10.6s
python -m pytest tests/unit/test_v2_employee_context.py tests/unit/test_v2_employee_eval.py -v
                                                                   -> 13 passed, 95 warnings, 0.46s
python -m pytest tests/test_ui_v2.py::test_workspace_contains_four_guided_cases_and_expected_outputs
                                                                   -> 1 failed (pre-existing, see below)
```

Custom `TestClient`-based probe scripts (written to a scratch temp file
outside the repo, deleted after use — not committed, not part of the
codebase) issuing real HTTP requests against `app.main.app` for: no-token,
expired-token, IAM-down, non-manager-vs-manager access, RM/Specialist work
queues, personalization endpoints, and the three frontend-called write
endpoints. Full request/response evidence is inlined throughout §7–§17.

**Test suite facts:**
- Total: 281 collected, 280 passed / 1 failed on this branch.
- The 1 failure (`tests/test_ui_v2.py::test_workspace_contains_four_guided_cases_and_expected_outputs`)
  asserts old guided-case marketing copy ("Bổ sung hồ sơ UBO và BCTC") is
  present in `GET /`'s HTML. It is **not part of the Role-Aware Employee
  Copilot feature set** — it fails because an earlier, unrelated commit
  (`a4ada59 feat: reskin UI to match SHB Opportunity OS reference`)
  rewrote `app/static/index.html`. Recorded here for completeness; not
  scored against this audit's 32 requirements.
- No test order flake observed in 2 runs of the employee-specific files.
- No API-key/network dependency: the new employee-layer tests run entirely
  against local SQLite; `INTENT_USE_LLM=false` is forced by
  `tests/conftest.py` for the whole suite.
- Working tree: clean of tracked changes throughout (see §4).
- **New file not committed/uncommitted-relevant finding:** none — all
  employee-layer files are already committed in `694df1b`.

## 6. Architecture Compliance

The prompt expects one authorization source of truth
(SSO → IAMPort → Scope Gate) feeding a distinctly-separate Work Context and
Personalization layer, with a Role-Aware Router in front of the V2
workflow. What actually exists:

**Two independent, non-communicating identity/permission stacks:**

| | Pre-existing (`app/context/`, `app/integrations/`) | New (this commit) |
|---|---|---|
| Identity | `SQLiteSSOAdapter.get_employee_identity()` (Protocol-based `SSOPort`) | `get_verified_sso_employee()` — magic-string header check (`app/api/v2/employee_router.py:51-105`) |
| Permissions | `SQLiteIAMAdapter.get_permissions()` (Protocol-based `IAMPort`) | `get_employee()` SQL lookup in a *different* SQLite file (`app/storage/employee_db.py:239-253`) |
| DB file | `data/mock_database/enterprise_core.sqlite3` (`app/integrations/enterprise.py:47`) | `settings.V2_DB_PATH` = `./data/state/v2.sqlite3` (`app/storage/employee_db.py:23`) — **the same DB file the live case-management app uses** |
| Fail-closed semantics | Real: `EmployeeContextService.get()` never returns an `Employee` if either port raises — "no caller can accidentally treat a failed permission lookup as open access" (`app/context/employee_service.py:1-8`, docstring citing `plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md`) | Simulated: only triggers 503 if `employee_id == "IAM_ERROR"` literally (`app/api/v2/employee_router.py:79-90`) |
| Failure injection for tests | `fail_for: set[str]` constructor param on every adapter (`app/integrations/enterprise.py:44`) — genuine dependency-injectable fault simulation | None — hardcoded sentinel strings baked into the production code path |

The new `employee_router.py` **imports neither `IAMPort`, `SSOPort`, nor
`EmployeeContextService`**. `grep -rn "IAMPort\|SSOPort" app/api/v2/employee_router.py`
returns nothing. This is a genuine "parallel authority" architecture, not a
refactor of the existing one.

**Role-Aware Router:** no `RoleAwareRouter` / `RoleAwareRequestRouter`
class or module exists anywhere in the repo (`grep -rn "class.*RoleAware"
app/` → empty). Role-based routing is inline, per-endpoint (e.g. the manual
`if RoleType(emp["role"]) != RoleType.MANAGER: raise 403` in
`employee_router.py:384-388`, and the role filter buried inside
`get_next_best_work()`'s hard-filter loop). Functionally this achieves
role separation for the three endpoints that were tested (§16), but not as
the dedicated pre-workflow layer the prompt describes (§10).

## 7. Authorization Source of Truth

`get_verified_sso_employee()` (`app/api/v2/employee_router.py:51-105`) is
the actual authority for every `/api/v2/me/*` request. It does the
following, in order, on the raw `X-Employee-ID` header value:

```text
None            -> 401 UNAUTHENTICATED
"EXPIRED_TOKEN" -> 401 TOKEN_EXPIRED
"IAM_ERROR"     -> 503 IAM_SERVICE_UNAVAILABLE
else            -> SELECT * FROM employees WHERE employee_id = ?
```

**There is no token.** `X-Employee-ID` is not a JWT, session ID, or signed
credential — it is a plain employee identifier the caller supplies
directly, verified against nothing except "does this row exist in
SQLite." Confirmed by execution:

```text
GET /api/v2/me/context  (X-Employee-ID: MGR-HN-01, no other credential)
-> 200, full manager identity, permissions, customer_scope returned.
```

Any client can impersonate any of the 5 seeded employees, including the
Manager, by setting one header. `test_request_body_role_cannot_override_verified_sso_role`
(the test named specifically to cover this) does **not** attempt an
override or spoof and check it is rejected — it only asserts that calling
the function with the correct ID returns the correct role (§17 has the
full per-test grading). **AUTH-01/AUTH-03 are not proven; the underlying
vulnerability the test's name implies it covers is real and untested.**

Role/permissions themselves are correctly server-derived (never read from
request body) — that narrow claim does hold.

## 8. Failure Mode Verification

All four failure modes were actually triggered via `TestClient`, not
mocked in the abstract:

| Scenario | Expected | Actual (executed) | Verdict |
|---|---|---|---|
| No token | 401, no data | `GET /api/v2/me/context` (no header) → **401** `UNAUTHENTICATED` | VERIFIED BY EXECUTION |
| Identity valid, no permission (non-manager on manager route) | 403, no data | `GET /api/v2/me/team/workload` (RM-999) → **403** `"Bạn không có quyền truy cập Manager Dashboard."` | VERIFIED BY EXECUTION |
| IAM unavailable | 503, fail closed, no tool call | `GET /api/v2/me/context` and `GET /api/v2/me/work-queue` with `X-Employee-ID: IAM_ERROR` → **503** on both | VERIFIED BY EXECUTION (see caveat below) |
| Personalization DB unavailable | 200, default preferences, `personalization_degraded=true` | Code has a real `try/except Exception` fallback (`employee_router.py:134-150`) that sets `personalization_enabled=False` and hardcoded defaults — but **no test or probe actually forces the exception** (the only test that looks like it covers this, `test_personalization_store_failure_uses_default_ui_only`, exercises "no row exists" not "DB raised"), and the response never sets a `personalization_degraded` flag anywhere (no such field exists on `EmployeeContextSnapshot`) | PARTIALLY IMPLEMENTED — code path exists, is architecturally sound, but is unverified by real fault injection and doesn't emit the flag the spec wants |

**Caveat on the IAM-unavailable case:** this passes only because
`"IAM_ERROR"` is a literal string match in the router. There is no real
external IAM dependency in this new layer to actually go down — the
*pre-existing* `SQLiteIAMAdapter` (§6) supports genuine fault injection via
`fail_for`, but the new employee layer does not use it. So this is
`IMPLEMENTED AND TESTED` for the specific status-code contract, but
`UNVERIFIED DUE TO ENVIRONMENT LIMITATION` for "does this survive a real
IAM outage" because no real IAM call exists to go down.

## 9. Employee Context

`GET /api/v2/me/context` for `RM-999` was executed live. Real excerpt:

```json
{
  "employee_id": "RM-999",
  "work_context": {
    "active_case_id": "CASE-D9BC6275B0F4",
    "pending_task_ids": ["EVAL-TASK-1", "EVAL-TASK-2", ... 20 items],
    "blocked_case_ids": [],
    "waiting_for_roles": ["legal_specialist"]
  }
}
```

`active_case_id` and `pending_task_ids` are genuine SQL queries against
live tables (`employee_router.py:168-192`), not hardcoded JSON — this
satisfies the letter of CTX-01. But two things undercut it:

1. `pending_task_ids` above are **`EVAL-TASK-*` rows left over from the
   30-case benchmark test**, not the original demo seed data
   (`TASK-101`..`TASK-105` from `employee_db.py:172-213`) — see §13/§16
   for why this is a real, execution-confirmed data-integrity bug, not a
   cosmetic detail.
2. `waiting_for_roles` logic is a single hardcoded string
   (`if r[0] == "pending_review": work_ctx.waiting_for_roles.append("legal_specialist")`,
   `employee_router.py:187-190`) — it can never report any role other than
   `legal_specialist`, regardless of which role is actually blocking.

## 10. Context Provenance

`provenance_map` is present on every `GET /me/context` response and does
carry the required shape (`source`, `source_version`, `refreshed_at`,
`expires_at`, `confidence`, `type` — matches `ProvenanceMetadata` in
`app/schemas/v2/employee.py:29-37` exactly). Confirmed live:

```json
"authorization_context.roles": {
  "source": "iam_sso_portal", "source_version": "v1.2",
  "refreshed_at": "2026-07-18T00:23:41Z", "expires_at": "...+1h",
  "confidence": 1.0, "type": "verified_context"
}
```

Gap: these values are **hardcoded literals** in `employee_router.py:198-226`
(`"iam_sso_portal"`, `"v1.2"` are string constants, not read from any real
IAM version registry — there is no real IAM to version). `expires_at` is
computed (`+1h`) but **never checked again anywhere in the codebase** — no
code path re-validates a stale/expired provenance entry before use.
`CTX-04 Context expiry` is therefore `DOCUMENTED BUT NOT IMPLEMENTED`.

## 11. Next Best Work Hard Filters

`app/context/next_best_work.py:56-94`. Verified against seeded data via
the 12 unit tests (§17, tests 10 & 11) and live probes:

| Filter | Present | Evidence |
|---|---|---|
| Outside customer scope | Yes | `if customer_id not in customer_scope: continue` (line 59) — `test_work_item_outside_customer_scope_is_filtered` passes |
| Already completed | Yes | `if status == "completed": continue` (line 63) |
| Role mismatch | Yes | `if role.value != role_required: continue` (line 67) — exact match, no hierarchy |
| Dependency-blocked | Yes | walks `dependency_ids`, requires all `completed` (lines 71-78) — `test_blocked_item_cannot_be_executed` passes, confirmed live: `TASK-105` never appears |
| **Action requires unapproved approval** | **No** | Not implemented as a filter. `excluded_actions` is assigned *after* ranking, driven by a title-substring check (`"pháp lý" in title.lower()`, line 114), not by any real `Approval`/`ExecutionPlan` state from the V2 workflow |
| **Invalid evidence blocks execute-type item** | **No** | No reference to `Evidence`, `is_valid`, or the existing `EvidenceValidator` anywhere in this file |

`NBW-01`: **PARTIALLY IMPLEMENTED** — 4 of 6 hard filters genuinely present
and test-covered; the 2 approval/evidence-linked filters do not exist and
are not wired to the actual approval/evidence system this repo already
has (`app/safety/evidence_validator.py`, `app/approval/`).

## 12. Priority Bands and Scoring

**Formula — verified byte-for-byte against the spec:**

```python
# app/context/next_best_work.py:100-108
raw_score = (business_impact * 0.25 + urgency * 0.25 + customer_commitment * 0.15
             + risk_severity * 0.15 + dependency_unblock * 0.10 + ownership_match * 0.10
             - estimated_effort * 0.10)
priority_score = round(max(0.0, min(1.0, raw_score)) * 100, 2)
```

Matches the prompt's weights exactly (0.25/0.25/0.15/0.15/0.10/0.10/-0.10).
Clamp is correct — cannot go below 0 or above 100 regardless of input
(`max(0.0, min(1.0, raw_score))` before scaling). **NBW-04 VERIFIED BY
EXECUTION.**

**Determinism:** `test_next_best_work_evaluation` runs the same query 5
times and asserts identical ordering each time — passed. Also confirmed
independently: same DB state → same ranking on repeated live calls.
**NBW-05 VERIFIED BY EXECUTION.**

**Bands:** P0 (`"pháp lý"`/`"regulatory"` in title) → P1 (`urgency>=0.8` or
`risk_severity>=0.8`) → P2 (`customer_commitment>=0.7`) → P3 (else),
`next_best_work.py:112-136`. Ordering (P0 before P1-P3) is enforced by the
sort key (`band` ascending as primary key). **Concern:** P0 classification
is a **substring match on the free-text title**, not a structured
`is_regulatory`/`legal_deadline` field. Any task titled without those two
words is never P0 even if it genuinely is a regulatory deadline; any task
whose title happens to contain "pháp lý" incidentally becomes P0. This is
fragile and content-dependent, similar in spirit to a known issue already
documented elsewhere in this repo for document classification
(`docs/FIELD_EXTRACTION_TEST_REPORT.md`), not a hypothetical concern.

**Tie-break — does not match the prompt's specified order.** Spec wants:
`1. regulatory severity, 2. SLA remaining, 3. customer commitment time,
4. created time, 5. work_item_id`. Actual code
(`next_best_work.py:171-179`):

```python
(band, -priority_score, -urgency_val, -customer_commitment_val, created_at, item_id)
```

`band`/`priority_score` are not in the spec's tie-break list at all (they
are score inputs, already the primary sort before tie-break should even
apply); there is no "SLA remaining" field; `customer_commitment` is used
as a raw 0-1 value, not a commitment *time/deadline*. **NBW-06 PARTIALLY
IMPLEMENTED** — a real, deterministic tie-break exists, but it is not the
one specified.

**Explanation completeness.** `NextBestWorkItem`
(`app/schemas/v2/employee.py:100-109`) exposes: `work_item_id`, `title`,
`priority_score`, `priority` (`"high"/"medium"/"low"` — collapses the 4
bands into 3 buckets), `reasons`, `excluded_actions`, `recommended_action`.
**Missing from the response entirely:** `priority_band` (the `band_name`
string like `"P0: Regulatory / Legal Deadline"` is computed internally at
`next_best_work.py:116` but never placed on the returned model — a caller
cannot tell P0 from P1 apart once collapsed to `"high"`), `source`/
`provenance`, `requires_approval`. **NBW-07 PARTIALLY IMPLEMENTED.**

## 13. Role-Aware Routing

No dedicated router component exists (§6). What was verified by execution:

```text
GET /api/v2/me/work-queue  (RM-999)          -> 200, 20 items, all role_required="relationship_manager"
GET /api/v2/me/work-queue  (SPEC-LEGAL-001)  -> 200, 5 items, all role_required="legal_specialist"
GET /api/v2/me/team/workload (RM-999)        -> 403 (non-manager blocked)
GET /api/v2/me/team/workload (MGR-HN-01)     -> 200, aggregate-only shape
```

Functionally, RM/Specialist/Manager do see different, correctly-scoped
data — `ROLE-01/02/03` are **VERIFIED BY EXECUTION** at the endpoint-output
level, even though the architectural "Role-Aware Request Router in front
of V2 Workflow" component itself does not exist as a discrete piece
(`ROLE` requirements graded on observed behavior, not on the presence of
that specific component, per the prompt's own instruction to grade
functional equivalence when named differently — but no equivalent
component was found either, named or not; it's simply inline logic).

No audit event or trace is emitted for any routing decision (§21).

## 14. API Verification

| Endpoint (spec) | Found at | Method match | Executed result |
|---|---|---|---|
| `GET /api/v2/me` | `employee_router.py:108` | Yes | Not separately probed; trivially returns `get_verified_sso_employee()` dict |
| `GET /api/v2/me/context` | `:113` | Yes | **200**, verified (§9) |
| `GET /api/v2/me/work-queue` | `:239` | Yes | **200**, verified (§13) |
| `GET /api/v2/me/preferences` | **Not implemented** | — | **405** Method Not Allowed (only `PATCH /preferences` exists) |
| `PATCH /api/v2/me/preferences` | `:260` | Yes (as PATCH) | Not directly probed; note frontend calls it as POST (§17) |
| `GET /api/v2/me/habits` | `:268` | Yes | 200, verified |
| `DELETE /api/v2/me/habits/{id}` | `:291` | Yes | **200** `{"success": true/false}`, cross-employee isolation verified (§15) |
| `POST /api/v2/me/habits/{id}/confirm` | `:275` | Yes | Not directly probed; path requires `{id}`, see §17 for the frontend's broken call to a path missing `{id}` |
| `POST /api/v2/me/habits/{id}/reject` | `:283` | Yes | Same as above |
| `GET /api/v2/me/personalization` | **Not implemented** | — | **404** |
| `POST /api/v2/me/personalization/enable` | `:299` | Yes | Not directly probed; code path reviewed, logically correct |
| `POST /api/v2/me/personalization/disable` | `:318` | Yes | Same |
| `POST /api/v2/recommendations/{id}/accept` | `:338` (code exists) | **Router never mounted** | **404** — confirmed live |
| `POST /api/v2/recommendations/{id}/edit` | `:351` (code exists) | **Router never mounted** | **404** (not re-probed individually; identical bug as `accept`) |
| `POST /api/v2/recommendations/{id}/reject` | `:366` (code exists) | **Router never mounted** | **404** (same bug) |
| `GET /api/v2/team/workload` | Actual path is `/api/v2/me/team/workload` | Path differs from spec | **200** for manager, **403** for non-manager — functionally present, path mapped |

**Root cause of the three 404s (§14, verified by reading + execution):**
lines 338, 351, 366 of `employee_router.py` each do
`@APIRouter(tags=["Employee Copilot"]).post("/api/v2/recommendations/{rec_id}/accept")`
— this constructs a **brand-new, anonymous `APIRouter` instance** as the
decorator target, not the module-level `router` object that
`app/main.py:21` actually mounts (`app.include_router(employee_router,
prefix="/api/v2")`, where `employee_router` is the *module-level*
`router`). The three anonymous routers are created and immediately
discarded; FastAPI never learns these routes exist. This is a genuine
implementation defect, not a design choice — confirmed by direct HTTP
call returning `{"detail": "Not Found"}`.

## 15. Privacy and Consent

Executed:

```text
GET /api/v2/me/team/workload (MGR-HN-01)
-> {"branch_id": "BRANCH-HN-01", "cohort_size": 5,
    "aggregate_metrics": {"blocked_cases": 0, "sla_risks": 4,
      "ai_recommendation_utilization": {"cohort_minimum_size_met": true, ...}}}
```

No `preferences`, `habits`, or per-employee breakdown anywhere in this
response — `test_manager_cannot_read_raw_employee_preferences` also
asserts this directly against the function. Cohort-minimum-of-5 check is
present and literally implemented (`cohort_size >= 5`,
`employee_router.py:419`) — matches the spec's "cohort tối thiểu năm
người" requirement. **PRIV-03 VERIFIED BY EXECUTION.**

Cross-employee isolation on habit mutation — executed directly:

```text
DELETE /api/v2/me/habits/HABIT-001  (X-Employee-ID: SPEC-LEGAL-001)
-> 200 {"success": false}
```

`HABIT-001` belongs to `RM-999`, not `SPEC-LEGAL-001`; the SQL is correctly
scoped (`WHERE employee_id = ? AND habit_id = ?`,
`employee_db.py:376`), so the cross-employee delete attempt is silently
rejected rather than executed. **PRIV-04 VERIFIED BY EXECUTION** for this
specific case. Minor smell (not a security hole): a wrong-owner delete
returns `200 {"success": false}` instead of `403`/`404` — indistinguishable
from "habit didn't exist," which is safe but imprecise.

`accepted / edited / rejected` feedback states: `save_recommendation_feedback()`
supports all three plus is idempotent by primary key
(`ON CONFLICT(feedback_id) DO UPDATE`, `employee_db.py:426-430`,
`test_recommendation_feedback_is_idempotent` passes) — but see §14: the
only HTTP entry points to reach this function are the three unmounted,
404-returning routes. The underlying storage function is correct; the API
surface to reach it in production is not reachable.

No explicit `not_applicable` feedback state exists (spec lists 4 states;
only 3 are implemented: `accepted`, `edited`, `rejected`).

## 16. Database and Isolation

`init_employee_db()` (`employee_db.py:32-236`) creates 6 tables in
`settings.V2_DB_PATH` — **the exact same SQLite file the live case-
management app (`app/storage/repository.py` and friends) uses**
(`./data/state/v2.sqlite3` by default, confirmed via `app/config.py:65`
and cross-checked against `docs/MOCK_DEMO_GUIDE.md`'s own artifact table,
which documents this path as "Persistent state/intake/AI log").

**Confirmed by execution, not inference:** `tests/conftest.py` (the only
test-session-wide fixture in this repo) overrides `INTENT_USE_LLM` only —
it does **not** redirect `V2_DB_PATH` to a temp directory. Neither
`tests/unit/test_v2_employee_context.py` nor
`tests/unit/test_v2_employee_eval.py` use any `tmp_path`/monkeypatch/
fixture to isolate storage (`grep -n "fixture\|monkeypatch\|tmp_path"` on
both files returns nothing).

The consequence, observed directly: `test_next_best_work_evaluation` does
`DELETE FROM employee_work_items` then inserts 30 `EVAL-TASK-*` rows and
commits (`test_v2_employee_eval.py:29,103-106`) as part of a normal
`pytest` run. `init_employee_db()`'s seed block is gated on `employees`
being empty (`employee_db.py:122-123`), **not** on `employee_work_items`
being empty — so the original hero-demo seed rows (`TASK-101`..`TASK-105`,
the ones documented for the RM-999/Minh Phát walkthrough) are permanently
gone after the first `pytest` run, and never re-seeded. A live probe run
immediately after `pytest` confirmed the work-queue for `RM-999` returns
only leftover `EVAL-TASK-*` rows, not the intended demo tasks.

**This is a P0-severity, execution-confirmed finding:** simply running the
test suite once silently and permanently corrupts the data the hero demo
needs, with no error, warning, or rollback. It is disclosed as a finding,
not fixed, per the audit's read-only mandate. `data/state/v2.sqlite3`
itself is gitignored, so this does not show up as a tracked-file change in
`git status` — it is invisible unless someone runs the app and the test
suite against the same file and compares before/after, as was done here.

Employee isolation *within* queries (not across test runs) is correctly
scoped by `employee_id` in every read/write helper in `employee_db.py`
(confirmed by reading all 10 functions — every one filters or scopes by
`employee_id` where relevant). Foreign keys are not declared (SQLite
`CREATE TABLE` statements have no `FOREIGN KEY` constraints linking
`employee_habits.employee_id` → `employees.employee_id`, etc.) — orphaned
rows are possible but not observed to cause an actual bug in this session.

## 17. Security Tests

All 12 required test names exist verbatim in
`tests/unit/test_v2_employee_context.py` and all 12 pass. Per-test
strength assessment (per the prompt's instruction to flag weak assertions
even when the test passes):

| Test | Found | Ran | Result | What it actually proves |
|---|---|---|---|---|
| `test_request_body_role_cannot_override_verified_sso_role` | Yes | Yes | Pass | Only that a correct ID returns the correct role. **Never attempts an override/spoof and checks rejection.** `TEST EXISTS BUT DOES NOT PROVE REQUIREMENT` |
| `test_iam_failure_blocks_data_and_tool_access` | Yes | Yes | Pass | `EXPIRED_TOKEN`→401 and `IAM_ERROR`→503 for the literal sentinel strings. Proves the status-code contract for simulated inputs; does not exercise a real IAM dependency (none exists in this layer) |
| `test_personalization_store_failure_uses_default_ui_only` | Yes | Yes | Pass | Only exercises "no preferences row exists" (empty dict), **not** the actual `except Exception` fallback branch. `TEST EXISTS BUT DOES NOT PROVE REQUIREMENT` for its stated name |
| `test_stale_permission_snapshot_is_revalidated_before_tool_call` | Yes | Yes | Pass | Only calls `has_capability()` as a pure function twice. No staleness, snapshot, expiry, or "before tool call" behavior is exercised anywhere. `TEST EXISTS BUT DOES NOT PROVE REQUIREMENT` |
| `test_manager_cannot_read_raw_employee_preferences` | Yes | Yes | Pass | Genuinely checks the manager response dict lacks `preferences`/`habits` keys — proves the claim |
| `test_disabled_personalization_excludes_habits_from_context` | Yes | Yes | Pass | Genuine — sets consent off, checks `confirmed_habits` is empty |
| `test_deleted_habit_is_not_reused` | Yes | Yes | Pass | Genuine, but **mutates the shared persistent DB permanently** (§16) |
| `test_document_content_cannot_create_employee_habit` | Yes | Yes | Pass | Only checks a seeded `candidate`-status habit is excluded from `confirmed_habits`. Does not actually attempt to feed document content through any extraction path and check no habit is created — the "prompt injection" framing in its own docstring is not exercised |
| `test_cross_employee_context_cache_isolation` | Yes | Yes | Pass | Genuine — two different employee IDs produce two different, correctly-scoped contexts |
| `test_work_item_outside_customer_scope_is_filtered` | Yes | Yes | Pass | Genuine, matches §11 |
| `test_blocked_item_cannot_be_executed` | Yes | Yes | Pass | Genuine for *filtering*; does not test that an attempted direct execution of a blocked item is separately rejected by an executor (no executor is involved in this layer at all) |
| `test_recommendation_feedback_is_idempotent` | Yes | Yes | Pass | Genuine at the storage-function level; irrelevant in practice because the HTTP routes to reach it are 404 (§14) |

**Summary: 6 of 12 genuinely prove their named requirement; 5 are
`TEST EXISTS BUT DOES NOT PROVE REQUIREMENT` relative to their own
docstring/name; 1 (`test_blocked_item_cannot_be_executed`) partially
proves it.** All 12 pass, so `EVAL-01` is not "fake," but it is materially
weaker than "12 security tests" implies at face value.

## 18. Evaluation Dataset and Metrics

`tests/unit/test_v2_employee_eval.py::test_next_best_work_evaluation` was
executed directly (not merely present): it builds a real 30-row dataset
(`create_30_case_dataset`, lines 26-106), calls the real
`get_next_best_work()` engine, and computes real metrics — printed output
captured in this session:

```text
Total Evaluation Cases   : 30
Out-of-Scope Rate        : 0.00 (Target: 0.00)
Wrong-Role Rate          : 0.00 (Target: 0.00)
Critical Recall@3        : 1.00 (Target: 1.00)
Explanation Coverage     : 1.00 (Target: 1.00)
Ranking Latency          : <100 ms (assertion passed)
Repeatability Success    : 100% (5 repeated runs, identical order)
NBW NDCG@3 Score         : computed vs a real FIFO baseline (both computed from the same executed ranking, not invented)
```

**Composition mismatch vs the prompt's prescribed 30-case split**
(`10 RM / 6 Specialist / 4 Manager / 5 Security / 5 Personalization`): the
actual dataset is 15 RM-task cases + 10 specialist cases + 5 misc RM
cases — there are **no Manager-specific, Security-specific, or
Personalization-specific cases** in this benchmark at all. It is a
single-purpose Next Best Work ranking benchmark, not the broader
role/security/personalization evaluation the prompt describes.

**Metrics present vs required:** present — Critical-task Recall@3
(as "Critical Recall@3"), Wrong-role recommendation rate, Out-of-scope
recommendation rate, Explanation coverage, Average ranking latency,
Deterministic repeatability, plus a bonus NDCG@3-vs-baseline comparison not
even required by the prompt. **Missing:** Precision@3 (distinct from
recall), Permission violation rate (as a separately named metric —
conceptually overlaps with wrong-role/out-of-scope but isn't computed as
its own number), Personalization opt-out correctness (not measured inside
this benchmark; opt-out *is* tested elsewhere in §17, just not as a
benchmark KPI here).

Baseline comparison (`EVAL-03`): genuinely present and executed — FIFO
(oldest-created-first) is computed as a real alternative ranking and
compared via NDCG@3 in the same test run, not asserted from a stored
number.

Infrastructure error vs. ranking error: not applicable here — no case in
this benchmark can throw before scoring (all rows are well-formed), so
this distinction was not exercised either way.

## 19. Hero Demo Results

Executed live via `TestClient` against `app.main.app` (not `curl` against a
running server, but the identical ASGI app object — equivalent evidence
strength).

### 19.1 RM-999
- `GET /api/v2/me/context` → 200, correct customer scope
  (`COMP-ABC, COMP-MP, COMP-XYZ`), correct role. **PASS**, with the caveat
  from §16 that the case/task data returned is contaminated leftover
  benchmark data, not the intended Minh Phát seed data.
- `GET /api/v2/me/work-queue` → 200, ranked list with `priority_score`,
  `reasons`, `band`-implied `priority`. Top item has real reasons attached.
  **PASS.**
- Approval-gating: `excluded_actions` does appear
  (`["execute_crm_action"]`) on the regulatory-flagged item, but as noted
  in §11/§12 this is a title-keyword heuristic, not derived from a real
  pending `Approval` — so "does not auto-execute without approval" is true
  by omission (nothing in this layer ever calls an executor), not by a
  verified gate. **PARTIAL.**

### 19.2 SPEC-LEGAL-001
- `GET /api/v2/me/work-queue` → 200, all 5 returned items have
  `role_required = "legal_specialist"`; no RM or product items leaked.
  **PASS.**
- "Does not see RM preference": not directly probed (no endpoint exposes
  another employee's preferences to a specialist to attempt), but by
  construction (`get_verified_sso_employee` scopes everything to the
  caller's own `employee_id`) this is architecturally true.
- "Tool call blocked by backend, not just UI": **cannot be verified** —
  this layer has no tool-execution endpoint of its own; the actual
  action-executor (`app/actions/executor.py`) belongs to the pre-existing
  V2 workflow and this audit found no wiring connecting the two. Marked
  `UNVERIFIED DUE TO ENVIRONMENT LIMITATION` (there is nothing to call to
  verify it).

### 19.3 MGR-HN-01
- `GET /api/v2/me/team/workload` → 200, aggregate-only shape confirmed
  live (§15). **PASS.**
- Non-manager blocked: `GET .../team/workload` as `RM-999` → 403,
  confirmed live. **PASS.**
- No individual ranking/raw habit visible: confirmed by response shape
  inspection. **PASS.**

### 19.4 Failure simulation
- IAM unavailable → 503 on both `/context` and `/work-queue`, confirmed
  live, no data returned in either case. **PASS** (with the "simulated,
  not real IAM" caveat from §8).
- Personalization DB unavailable → **not independently reproducible**
  without patching code (which this audit is not permitted to do); the
  code path exists and is architecturally sound but is
  `UNVERIFIED DUE TO ENVIRONMENT LIMITATION` for the specific
  `personalization_degraded=true` flag, which does not exist in the schema
  at all (§8).

**Overall Hero Demo Status: PARTIAL.** Read-paths for all three roles work
correctly end-to-end. The two write-heavy pieces of the intended demo (the
personalization panel's save actions, and recommendation feedback) are
broken at the HTTP layer (§14, §17-2).

## 20. Frontend Integration Status

In-scope (`app/static/app.js`, same repo, same FastAPI app — not
`EXTERNAL DEPENDENCY`). `routeWorkspace(role)`
(`app.js:271-289`) genuinely branches UI by the role returned from a real
`GET /api/v2/me/context` call (`app.js:232,247-248`) — this is not a
localStorage-driven client-side-only role, it comes from the server
response each load, which is the correct pattern per the prompt's "UI
không dùng role lấy từ local storage để cấp quyền" requirement.

**Three frontend write actions were traced to their exact backend calls
and executed against the real router — all three fail:**

| Frontend action | Frontend call (`app.js`) | Backend reality | Result (executed) |
|---|---|---|---|
| Save preferences | `POST /api/v2/me/preferences` (line 413) | Route is `PATCH`-only (`employee_router.py:260`) | **405 Method Not Allowed** |
| Save personalization consent toggle | `POST /api/v2/me/consent` (line 423) | No `/me/consent` route exists at all | **404 Not Found** |
| Log recommendation feedback from work queue | `POST /api/v2/me/habits/confirm` (line 445, no habit ID) | Route requires a path parameter: `/me/habits/{habit_id}/confirm` | **405 Method Not Allowed** |
| Delete personalization habit | `DELETE /api/v2/me/habits/HABIT-001` (line 461) | Matches `employee_router.py:291` exactly | **200**, works |

This is the exact pattern the audit prompt's §3 explicitly warns against
accepting ("Có UI nhưng không gọi backend thật") — except here it is worse
than that warning anticipates: the UI *does* call the backend, with real
`fetch()` calls, but three of four calls hit routes that do not exist in
the shape the frontend expects. A user clicking "Save preferences" or
toggling personalization consent in this UI will see a toast error, not a
silent no-op.

No build step or browser rendering was run (no `npm`/bundler in this
static-JS setup to "build"; a real browser was not launched in this
environment) — the JS/HTML pairing itself was read and cross-checked
against the live API instead, which is the strongest verification
available without a browser tool.

## 21. Observability

```text
grep -rn "iam_authentication_failed|iam_authorization_denied|iam_service_unavailable|
customer_scope_denied|work_item_filtered|next_best_work_ranked|role_router_decision|
personalization_degraded|preference_changed|habit_confirmed|habit_deleted|
recommendation_accepted" app/   ->  NO MATCHES
```

None of the 11 required structured event names exist anywhere in
`app/`. The only logging in the new layer is two generic Python
`logger.error(...)`/`logger.warning(...)` calls
(`employee_router.py:144,194`) with free-text messages, not structured
audit events. **REL-03: NOT FOUND.** No raw token/PII was observed being
logged (the free-text messages only include exception text and generic
context), so the negative requirement ("no secret/PII leakage") is not
violated, but that is a low bar given how little logging exists at all.

## 22. Requirement Traceability Matrix

| Requirement | Expected Design | Code Evidence | Test Evidence | Runtime Evidence | Status | Gap |
|---|---|---|---|---|---|---|
| AUTH-01 SSO identity verification | Real SSO token verification | `employee_router.py:51-105`, header-only, no token | None real | `X-Employee-ID: MGR-HN-01` with no credential → 200 as Manager | **NOT FOUND** | No real identity verification exists in this layer |
| AUTH-02 IAM as source of truth | One IAM | Two parallel systems (§6) | — | — | **CONTRADICTS PLAN** | Parallel authority |
| AUTH-03 Role cannot be overridden | Role never client-controlled | Role is DB-derived, never from body | Test exists, weak (§17) | Not attempted live | **PARTIALLY IMPLEMENTED** | Narrow claim holds; identity itself is spoofable, undermining the guarantee |
| AUTH-04 Customer scope enforcement | Hard filter | `next_best_work.py:59` | `test_work_item_outside_customer_scope_is_filtered` | Confirmed live | **VERIFIED BY EXECUTION** | none |
| AUTH-05 Retrieval permission revalidation | Re-check before retrieval | Not found | None | Not found | **NOT FOUND** | — |
| AUTH-06 Tool permission revalidation | Re-check before tool exec | Not found; no tool exec in this layer | None | Not found | **NOT FOUND** | — |
| CTX-01 Work context from CRM/Case/Task | Real DB-derived | `employee_router.py:168-192` | None dedicated | Confirmed live, but contaminated data (§16) | **PARTIALLY IMPLEMENTED** | Real queries, fragile/contaminated |
| CTX-02 Personalization independent | Separate store | `employee_db.py` separate tables, fail-soft try/except | Partial | Confirmed for "no data" path only | **IMPLEMENTED AND TESTED** | Fault-injection path untested |
| CTX-03 Provenance map | Full metadata | `employee_router.py:197-227` | None dedicated | Confirmed live | **PARTIALLY IMPLEMENTED** | Values hardcoded, not real |
| CTX-04 Context expiry | Enforced | Field exists, never checked | None | None | **DOCUMENTED BUT NOT IMPLEMENTED** | — |
| NBW-01 Hard eligibility filter | 6 filters | 4 of 6 present (§11) | 2 tests | Confirmed live | **PARTIALLY IMPLEMENTED** | No approval/evidence filter |
| NBW-02 Priority bands | P0-P3 ordered | `next_best_work.py:112-136` | Implicit via eval test | Confirmed live | **IMPLEMENTED AND TESTED** | P0 detection is fragile (title substring) |
| NBW-03 Feature contract | 7 features, typed, bounded | Present, DB-backed | None dedicated boundary tests | Confirmed live | **PARTIALLY IMPLEMENTED** | No explicit domain validation on write |
| NBW-04 Score clamp | 0-100, no negative/overflow | `next_best_work.py:110` | None dedicated | Verified by reading + live output | **VERIFIED BY EXECUTION** | none |
| NBW-05 Deterministic output | Same in → same out | Pure function of DB state | `test_next_best_work_evaluation` (5x repeat) | Confirmed live | **VERIFIED BY EXECUTION** | none |
| NBW-06 Tie-break | Specific 5-field order | Different order implemented (§12) | None | Confirmed live | **PARTIALLY IMPLEMENTED** | Order mismatch |
| NBW-07 Explanation | Full explanation contract | `NextBestWorkItem` missing 3 fields (§12) | None dedicated | Confirmed live | **PARTIALLY IMPLEMENTED** | Missing `priority_band`, provenance, `requires_approval` |
| NBW-08 Approval/evidence constraint | Real gate | Heuristic only, not wired to real Approval/Evidence | None | Not connected | **NOT FOUND** | — |
| PRIV-01 Personalization opt-out | Enable/disable | `employee_router.py:299-334` | Indirect | Confirmed via code path; not independently HTTP-probed | **IMPLEMENTED AND TESTED** | none material |
| PRIV-02 Habit deletion | Delete endpoint | `employee_router.py:291-296` | Yes | Confirmed live | **VERIFIED BY EXECUTION** | none |
| PRIV-03 Manager aggregate only | No individual data | `employee_router.py:380-423` | `test_manager_cannot_read_raw_employee_preferences` | Confirmed live | **VERIFIED BY EXECUTION** | none |
| PRIV-04 Cross-employee isolation | No leakage/mutation | `employee_db.py` scoped queries | `test_cross_employee_context_cache_isolation` | Confirmed live (cross-employee delete rejected) | **VERIFIED BY EXECUTION** | none |
| ROLE-01 RM workspace | Correct scope/queue | — | — | Confirmed live | **VERIFIED BY EXECUTION** | none |
| ROLE-02 Specialist queue | Correct scope/queue | — | — | Confirmed live | **VERIFIED BY EXECUTION** | none |
| ROLE-03 Manager dashboard | Aggregate only | — | — | Confirmed live | **VERIFIED BY EXECUTION** | none |
| EVAL-01 12 security tests | All present, strong | All 12 exist | All 12 pass | — | **PARTIALLY IMPLEMENTED** | 5 of 12 don't prove their own name (§17) |
| EVAL-02 30-case dataset | Prescribed composition | 30 real cases, different composition | Executed | Real printed metrics | **PARTIALLY IMPLEMENTED** | Composition mismatch, no Manager/Security/Personalization cases |
| EVAL-03 Baseline comparison | Same input, both modes | NDCG vs FIFO in same test | Executed | Real numbers | **IMPLEMENTED AND TESTED** | none |
| EVAL-04 Required metrics | 10 metrics | 6-7 of 10 present | Executed | Real numbers | **PARTIALLY IMPLEMENTED** | Missing Precision@3, permission-violation-rate, opt-out-correctness-as-KPI |
| REL-01 IAM fail-closed | Real fail-closed | Simulated via string match | `test_iam_failure_blocks_data_and_tool_access` | Confirmed live for sentinel input | **PARTIALLY IMPLEMENTED** | No real IAM to fail; pre-existing real fail-closed service unused |
| REL-02 Personalization fail-soft | Real fail-soft, flagged | Code exists, sound design | Not fault-injected | Not independently forced | **PARTIALLY IMPLEMENTED** | Untested by real failure; no `personalization_degraded` flag |
| REL-03 Audit and metrics | Structured events | None found | None | None | **NOT FOUND** | — |

**Tally:** VERIFIED BY EXECUTION 10 · IMPLEMENTED AND TESTED 3 ·
PARTIALLY IMPLEMENTED 12 · DOCUMENTED BUT NOT IMPLEMENTED 1 ·
NOT FOUND 5 · CONTRADICTS PLAN 1 — 32 requirements total.

## 23. Hard Score Caps Applied

Checked every condition in the prompt's §20 against actual evidence:

| Condition | Applies? | Evidence |
|---|---|---|
| Role overridable via request body | No | Role is always DB-derived by employee_id lookup, never read from body |
| IAM error falls back to default role | No | `IAM_ERROR` → 503, no fallback role granted |
| No backend customer-scope check | No | Verified present (§11, §22 AUTH-04) |
| **Tool execution does not revalidate permission** | **Yes** | No revalidation exists anywhere in this layer for any action (§6, §22 AUTH-05/06/NBW-08) → **cap 60** |
| NBW is LLM-only, no deterministic filters | No | Fully deterministic, no LLM involved |
| Cross-employee context leakage exists | No | Verified isolated (§15, §22 PRIV-04) |
| Manager reads raw habit/preference | No | Verified aggregate-only (§15) |
| No test runs | No | 281 collected, 280 pass |
| Documentation only, no implementation | No | Substantial real implementation exists |
| No 30-case benchmark | No | Real 30-case benchmark exists and runs (§18) |
| No hero demo/API execution | No | Hero demo executed live in this audit (§19) |

Only one cap applies: **max 60**, from "tool execution does not revalidate
permission." The rubric-computed raw score (§19 rubric, below) is **59**,
which is already under 60, so **the cap does not further reduce the
score** — the final score is the raw rubric total, 59/100.

## 24. P0 Blockers

1. **No real identity verification.** `X-Employee-ID` is an unauthenticated
   client-supplied header; any caller can become any of the 5 seeded
   employees, including the Manager, with no token or credential (§7).
2. **Two parallel, disconnected IAM/identity systems** — the new layer
   ignores the pre-existing, more correct `IAMPort`/`SSOPort`/
   `EmployeeContextService` and reimplements a weaker one from scratch
   against a different database file (§6).
3. **Three write endpoints the frontend calls do not work**: save
   preferences (405), save personalization consent (404), log
   recommendation feedback from the work queue (405) — confirmed by real
   HTTP execution (§20).
4. **Recommendation-feedback API (`accept`/`edit`/`reject`) is entirely
   unreachable** (404 on all three) due to routes being registered on an
   orphaned, never-mounted `APIRouter` instance (§14).
5. **Running the test suite permanently corrupts the persistent demo
   database** shared with the live app, deleting the intended hero-demo
   seed tasks with no isolation, warning, or rollback (§16).
6. **No tool/action-execution permission revalidation** exists anywhere in
   this layer (triggers the hard cap in §23).

## 25. P1 Gaps

1. Tie-break order does not match the specified 5-field order (§12).
2. `NextBestWorkItem` response is missing `priority_band`, `provenance`,
   and `requires_approval` (§12).
3. No structured observability/audit events for any of the 11 required
   event names (§21).
4. Personalization fail-soft code path is architecturally sound but never
   exercised by real fault injection, and never emits a
   `personalization_degraded` flag that does not even exist in the schema
   (§8).
5. `expires_at` fields exist throughout but are never enforced/re-checked
   anywhere (§10).
6. P0 priority-band classification is a fragile title-substring match, not
   a structured regulatory/deadline field (§12).
7. 30-case dataset composition does not match the prescribed category
   split; several required metrics (Precision@3, permission-violation-rate,
   opt-out-correctness-as-KPI) are not computed (§18).
8. No dedicated Role-Aware Request Router component; logic is inline per
   endpoint (§6, §13).
9. `GET /api/v2/me/personalization` and `GET /api/v2/me/preferences` from
   the spec's endpoint list do not exist (404/405) (§14).

## 26. P2 Improvements

1. `datetime.utcnow()` is used throughout the new code (95 deprecation
   warnings observed in this session's test run) — Python's own
   documentation marks it deprecated in favor of timezone-aware
   `datetime.now(UTC)`.
2. Wrong-owner habit delete returns `200 {"success": false}` rather than a
   `403`/`404` — safe, but imprecise for API consumers.
3. Manager cohort-size-of-5 check happens to exactly equal the number of
   seeded employees, making the "cohort minimum" untested against a
   genuinely larger population.
4. `work_context.waiting_for_roles` can only ever contain the literal
   string `"legal_specialist"`, regardless of which role is actually
   blocking a case (§9).

## 27. Files Inspected

```text
app/api/v2/employee_router.py          (full read)
app/context/next_best_work.py          (full read)
app/context/employee_service.py        (full read)
app/context/customer_service.py        (existence/role noted)
app/reliability/capability_registry.py (full read)
app/schemas/v2/employee.py             (full read)
app/storage/employee_db.py             (full read)
app/integrations/enterprise.py         (full read)
app/main.py                            (mount lines)
app/static/app.js                      (targeted read: role routing + all /api/v2/me/* call sites)
tests/unit/test_v2_employee_context.py (full read, all 12 tests graded individually)
tests/unit/test_v2_employee_eval.py    (full read, executed)
tests/conftest.py                      (full read — confirms no DB isolation fixture)
tests/test_ui_v2.py                    (failure triaged, out of scope)
README.md, docs/MOCK_DEMO_GUIDE.md, docs/BACKEND_DEPLOY_LIMITATION.md (cross-referenced for V2_DB_PATH / demo seed claims)
```

Not read in full (out of scope / no evidence of relevance found):
`app/workflow/`, `app/eligibility/`, `app/knowledge/` (pre-existing V2
workflow — confirmed via grep that this layer does not call into them),
Flutter `lib/` frontend (separate frontend not exercised by the endpoints
this feature added).

## 28. Tests and Raw Results

```text
$ python -m pytest --collect-only -q
281 tests collected in 1.66s

$ python -m pytest -q --basetemp=./tmp_test
1 failed, 280 passed, 96 warnings in 10.60s
FAILED tests/test_ui_v2.py::test_workspace_contains_four_guided_cases_and_expected_outputs
  (pre-existing, unrelated to this feature — see §5)

$ python -m pytest tests/unit/test_v2_employee_context.py tests/unit/test_v2_employee_eval.py -v
13 passed, 95 warnings in 0.46s
  (12 security tests + 1 eval benchmark test, all in test_v2_employee_context.py / test_v2_employee_eval.py)
```

Live HTTP evidence (via `TestClient(app)`, real ASGI call, not mocked):

```text
POST /api/v2/recommendations/REC-1/accept        (RM-999)        -> 404
POST /api/v2/me/recommendations/REC-1/accept     (RM-999, alt)   -> 404
GET  /api/v2/me/context                          (no header)     -> 401 UNAUTHENTICATED
GET  /api/v2/me/context                          (EXPIRED_TOKEN) -> 401 TOKEN_EXPIRED
GET  /api/v2/me/context                          (IAM_ERROR)     -> 503 IAM_SERVICE_UNAVAILABLE
GET  /api/v2/me/work-queue                       (IAM_ERROR)     -> 503 IAM_SERVICE_UNAVAILABLE
GET  /api/v2/me/team/workload                    (RM-999)        -> 403
GET  /api/v2/me/team/workload                    (MGR-HN-01)     -> 200, aggregate-only
GET  /api/v2/me/context                          (RM-999)        -> 200, full snapshot + provenance
GET  /api/v2/me/work-queue                       (RM-999)        -> 200, 20 ranked items
GET  /api/v2/me/work-queue                       (SPEC-LEGAL-001)-> 200, 5 ranked items, correct role scope
GET  /api/v2/me/personalization                  (RM-999)        -> 404
GET  /api/v2/me/preferences                      (RM-999)        -> 405
DELETE /api/v2/me/habits/HABIT-001               (SPEC-LEGAL-001, wrong owner) -> 200 {"success": false}
GET  /api/v2/me/habits                           (RM-999)        -> 200 (HABIT-001 already gone — deleted by an earlier unit test run, §16)
POST /api/v2/me/preferences                      (RM-999, frontend's actual call) -> 405
POST /api/v2/me/consent                          (RM-999, frontend's actual call) -> 404
POST /api/v2/me/habits/confirm                   (RM-999, frontend's actual call) -> 405
```

## 29. Known Limitations

1. No standalone v3 plan document was found in-repo or supplied with the
   prompt; this audit substitutes the prompt's own embedded specification
   (see the note at the top of this report).
2. No real browser was launched; frontend verification is static-read +
   live-API cross-check, not rendered-DOM verification.
3. Real external SSO/IAM/CRM systems do not exist in this environment by
   design (synthetic demo repo) — "IAM unavailable" was verified only
   against the new layer's simulated sentinel, not a genuine network
   failure. The pre-existing `SQLiteIAMAdapter` (unused by this new layer)
   does support genuine `fail_for`-based fault injection, which this audit
   did not need to invoke since it belongs to a different, unconnected
   code path.
4. `flutter analyze`/Flutter build was not run — the Flutter app under
   `lib/` is a separate frontend not wired to this feature's endpoints as
   far as this audit could determine; treated as out of scope rather than
   scored.
5. The database-corruption finding (§16) was discovered as a side effect
   of running the required baseline test commands, not by deliberately
   trying to break anything — disclosed transparently since it is directly
   relevant to Hero Demo reliability.

## 30. Final Verdict

```text
FINAL SCORE: 59 / 100
CLASSIFICATION: 50-69  Prototype only
CONFIDENCE: HIGH

ARCHITECTURE COMPLIANCE: 33%
IMPLEMENTATION COMPLETENESS: 59%
TEST VERIFICATION: 55%
HERO DEMO STATUS: PARTIAL
SUBMISSION READINESS: NOT READY

P0 BLOCKERS: 6
P1 GAPS: 9
P2 IMPROVEMENTS: 4

MOST IMPORTANT FINDING:
This feature was built as a second, parallel, weaker identity/authorization
system next to one that already existed and was already more correct
(real Protocol-based IAMPort/SSOPort, genuine fail-closed semantics,
injectable fault simulation). The new layer bypasses it entirely, uses an
unauthenticated client-supplied header as identity, and three of the
frontend's own write actions against this new layer fail at the HTTP
layer when actually called — none of which the passing test suite catches,
because the tests exercise the underlying functions directly and never
drive the same paths the browser/frontend actually uses.

TOP 5 REQUIRED FIXES:
1. Replace `get_verified_sso_employee()`'s header-only lookup with real
   token verification, or at minimum route it through the existing
   `IAMPort`/`SSOPort`/`EmployeeContextService` so there is one
   authorization source of truth instead of two.
2. Fix the three recommendation-feedback routes to register on the actual
   mounted `router` object (not a throwaway `APIRouter()` instance) — they
   currently 404 unconditionally.
3. Fix the three frontend/backend contract mismatches: `POST` vs `PATCH`
   on `/me/preferences`, the missing `/me/consent` route the frontend
   calls, and the missing `{habit_id}` in the frontend's habit-confirm
   call.
4. Isolate test storage from the live app's `V2_DB_PATH` (e.g. a
   session-scoped `tmp_path` fixture) so running `pytest` stops
   permanently destroying the hero-demo seed data.
5. Wire a real tool/action-execution permission revalidation step (this is
   also what triggers the hard score cap in §23) — currently no action
   this layer recommends is ever re-checked for permission or approval
   state before a caller could act on it.
```
