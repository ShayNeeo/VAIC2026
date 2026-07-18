# Role-Aware P0 Fix Implementation Report

Scope: fix the P0 findings in `docs/ROLE_AWARE_REPO_VERIFICATION_REPORT.md`
(score 59/100) without adding new features. Branch:
`feat/v2-employee-copilot-layer` (worked in place — worktree isolation was
attempted first and blocked by the environment; see §17). Not committed,
not pushed, per instructions.

## 1. Executive Summary

Five of the report's six P0 blockers are now fixed and verified by real
HTTP execution (`fastapi.testclient.TestClient` against the live app, not
mocked): identity is no longer an unauthenticated client-supplied header,
the two parallel IAM systems are consolidated into one, the three broken
frontend/backend contract calls are fixed, the recommendation-feedback
endpoints that 404'd unconditionally now work, and the test suite no
longer destroys the persistent demo database it shares with the live app.
The sixth (tool-execution permission revalidation) is partially addressed
via a new `require_capability()` chokepoint, but is not fully wired into
the pre-existing V2 workflow's approval/evidence system — disclosed as a
remaining gap in §18, not claimed as closed.

Full suite: **299 passed, 1 failed** (same pre-existing, out-of-scope UI
test as the original audit), run twice, identical both times. Employee
Copilot tests specifically: **32 passed, 0 failed** (up from 13, all now
HTTP-driven). The three previously-404 recommendation endpoints now return
200, confirmed live. Additionally, per explicit user direction mid-task,
the Flutter app (`lib/main.dart`) — discovered to be the actual production
frontend, entirely disconnected from this backend (it calls the removed
`/api/v1` API) — was wired to the new `/api/v2/me/*` endpoints. This part
is **UNVERIFIED DUE TO ENVIRONMENT LIMITATION**: no Flutter/Dart SDK is
installed in this environment, so it could not be compiled or run; it was
written and manually cross-checked against the file's existing patterns
instead (see §18).

## 2. Baseline State

```text
git branch --show-current  -> feat/v2-employee-copilot-layer
git status --short          -> only docs/ROLE_AWARE_REPO_VERIFICATION_REPORT.md
                                (untracked, from the prior audit turn) +
                                scratch/, tmp_test/ (pre-existing, unrelated)
git diff --stat              -> empty (clean tracked tree)

python -m pytest --collect-only -q  -> 281 tests collected
python -m pytest -q                 -> 280 passed, 1 failed
  FAILED tests/test_ui_v2.py::test_workspace_contains_four_guided_cases_and_expected_outputs
  (pre-existing, unrelated to Employee Copilot -- confirmed again in this
  session, unchanged from the original audit)

Untracked file NOT part of this task's scope:
  app/static/app_new.js -- was present at the start of the P0-fix prompt
  turn per the user's own message, but had already disappeared from
  `git status` by the time this task began (confirmed: not present in any
  `git status --short` output taken in this session). Never opened, edited,
  staged, or referenced by any change in this report.
```

Route table before any fix (from the verification report, re-confirmed at
the start of this task): `POST /api/v2/recommendations/{id}/accept|edit|reject`
were defined in code but not reachable (404), `GET /api/v2/me/personalization`
and `GET /api/v2/me/preferences` did not exist (404/405), and identity
resolution (`get_verified_sso_employee()`) trusted a raw `X-Employee-ID`
header against `employee_db.py`'s own SQLite table — a second, disconnected
identity store from the pre-existing `SQLiteSSOAdapter`/`SQLiteIAMAdapter`
(`app/integrations/enterprise.py`) already used by
`app/api/v2/router.py`.

## 3. Root Causes

1. The Employee Copilot layer was built without importing or reusing
   `EmployeeContextService`/`SSOPort`/`IAMPort`, which already existed and
   were already correctly wired into the main V2 router
   (`app/api/v2/router.py:162`). It reimplemented identity/role/permission
   lookup from scratch against a second, separate SQLite database
   (`data/state/v2.sqlite3`'s `employees` table) that had no overlap with
   the real one (`data/mock_database/enterprise_core.sqlite3`) — four of
   the five demo personas (`SPEC-LEGAL-001`, `SPEC-PROD-001`,
   `SPEC-OPS-001`, `MGR-HN-01`) did not exist in the real IAM database at
   all.
2. Three recommendation-feedback routes were declared on
   `@APIRouter(tags=[...]).post(...)` — a throwaway, anonymous `APIRouter`
   instance created inline as a decorator target and never
   `app.include_router()`'d anywhere.
3. The frontend's `fetch()` calls and the backend's route definitions were
   never cross-checked against each other during development (`POST` vs
   `PATCH /me/preferences`, a `/me/consent` call to a route that never
   existed, a `/me/habits/confirm` call missing the required `{habit_id}`
   path segment) — this was already fixed by a concurrent session's commit
   `545525b` before this task started; re-verified, not re-fixed, in §12.
4. `init_employee_db()` was defined but never called from anywhere in
   `app/` — a fresh checkout/CI run would have no `employees` table at all.
5. `employee_db.py` cached `settings.V2_DB_PATH` into a module-level
   constant at import time, so no test could redirect it to an isolated
   temp file — every employee-layer test ran against the same SQLite file
   the live demo app reads, and the 30-case eval test's
   `DELETE FROM employee_work_items` permanently destroyed the hero-demo
   seed tasks the first time the suite ever ran.

## 4. Identity Architecture Before

```text
X-Employee-ID header (client-supplied, unauthenticated, no token)
  -> get_verified_sso_employee()  [app/api/v2/employee_router.py, old]
     - "EXPIRED_TOKEN" / "IAM_ERROR" literal string checks
     - else: SELECT * FROM employees WHERE employee_id = ?  (employee_db.py,
       a table with its own separate seed data, never the real IAM)
  -> role/permissions/customer_scope taken directly from that row
```

Anyone could set `X-Employee-ID: MGR-HN-01` and receive a full manager
identity with zero verification.

## 5. Identity Architecture After

```text
Authorization: Bearer <token>
  (demo-* token, or -- only if settings.DEMO_AUTH_ENABLED -- a bare
   X-Employee-ID header, kept for backward compatibility with the browser
   demo UI and existing tests)
  -> require_verified_identity()  [app/api/v2/employee_router.py]
     - "EXPIRED_TOKEN" -> 401 before any IAM call
     - resolves the credential to an employee_id (demo-rm-999 -> RM-999)
     - EmployeeContextService(SQLiteSSOAdapter(fail_for={"IAM_ERROR"}),
                               SQLiteIAMAdapter(fail_for={"IAM_ERROR"}))
                               .get(employee_id, correlation_id=...)
       -- the SAME ports app/api/v2/router.py already uses
     - UpstreamUnavailableError (unknown identity) -> 403
     - UpstreamTimeoutError / ContextError (IAM down)  -> 503
  -> map_enterprise_role_to_role_type(role, organization_unit) -> RoleType
  -> VerifiedIdentity(employee_id, roles, permissions, customer_scope,
                       auth_source, identity_verified=True)
```

Every route in `employee_router.py` and the new `recommendation_router`
takes `identity: VerifiedIdentity = Depends(require_verified_identity)` —
none read `X-Employee-ID`, role, or employee_id from a request body or
query parameter. Verified live:

```text
DEMO_AUTH_ENABLED=false:
  GET /api/v2/me/context, X-Employee-ID: MGR-HN-01  -> 401 UNAUTHENTICATED
  GET /api/v2/me/context, Authorization: Bearer demo-mgr-hn-01 -> 401 (demo token also rejected)
  GET /api/v2/me/context, Authorization: Bearer MGR-HN-01      -> 200 (a real, non-demo bearer still resolves via IAM)

Role-spoof attempt (DEMO_AUTH_ENABLED=true, RM-999's real token + a bogus
extra header claiming a different role):
  GET /api/v2/me/context, headers={Authorization: Bearer demo-rm-999, X-Role: manager}
    -> 200, authorization_context.roles == ["relationship_manager"] (unaffected)
  GET /api/v2/me/team/workload, same headers -> 403 (still not a manager)
```

`DEMO_AUTH_ENABLED` (`app/config.py`) defaults to `true` only when
`APP_ENV=development` (the existing default for this MVP), mirroring the
existing `APPROVAL_SECRET` production-guard pattern in
`app/approval/service.py:32`.

## 6. IAM Consolidation

`app/integrations/enterprise.py` gained:

- `ensure_employee_copilot_demo_personas()` — idempotent (`INSERT OR
  IGNORE`), adds the 4 demo personas that only existed in the newer,
  disconnected `employee_db.py` table to the real
  `enterprise_core.sqlite3` `employees`/`permissions` tables. Never
  deletes or overwrites a row (unlike `scripts/init_enterprise_db.py`,
  which is a now-broken one-time migration that would wipe the table since
  its `app.integrations.{crm,iam,sso}` source modules were already deleted
  by an earlier, unrelated cleanup commit — not touched or re-run here).
- `map_enterprise_role_to_role_type(role, organization_unit)` — bridges
  the coarse IAM role vocabulary (`"RM"`/`"Specialist"`/`"Manager"`/
  `"DataSteward"`) to the fine-grained `RoleType` enum
  (`relationship_manager`/`legal_specialist`/`product_specialist`/
  `operations_specialist`/`manager`/`auditor`) the Next Best Work engine
  needs, using `organization_unit` to disambiguate which specialist type.

Verified live (all 5 personas resolve through the real adapters with
correct role mapping and customer scope):

```text
RM-999          -> RM / Corporate Banking HN        -> relationship_manager
SPEC-LEGAL-001  -> Specialist / Legal & Compliance   -> legal_specialist
SPEC-PROD-001   -> Specialist / Product              -> product_specialist
SPEC-OPS-001    -> Specialist / Operations           -> operations_specialist
MGR-HN-01       -> Manager / Branch HN Management    -> manager
```

`app/reliability/capability_registry.py` (`CapabilityRegistry`/
`has_capability()`) is unchanged and still used strictly as a policy
mapper (role -> allowed capability set) — it does not verify identity or
store permissions; see §10 for the new `require_capability()` call site
that intersects it with the IAM-granted permission list.

`employee_db.py` now stores **only** what it should: preferences, consent,
habits, work items, recommendation feedback. It is never consulted for
identity, role, or permission resolution.

## 7. Customer Scope Enforcement

Unchanged in mechanism (the hard filter in
`app/context/next_best_work.py:59`, `if customer_id not in customer_scope:
continue`, was already correct per the original audit) but now fed from
`identity.customer_scope`, which comes from the real IAM's
`access_scope.managed_customer_ids` — not from the old `employee_db`
table. Re-verified live: `SPEC-LEGAL-001`'s work queue returns only
`role_required="legal_specialist"` items; `RM-999` restricted to
`customer_scope=["COMP-XYZ"]` never sees `COMP-MP` tasks (existing test,
still passing).

## 8. API Contract Fixes

| Route | Before | After |
|---|---|---|
| `POST /api/v2/recommendations/{id}/accept` | 404 (orphaned router, never mounted) | **200**, verified live |
| `POST /api/v2/recommendations/{id}/edit` | 404 | **200**, verified live |
| `POST /api/v2/recommendations/{id}/reject` | 404 | **200**, verified live |
| `POST /api/v2/recommendations/{id}/feedback` | did not exist | **New**, unified alternative per spec §8.3, `{"feedback": "accepted"\|"edited"\|"rejected"\|"not_applicable"}`, 422 on an invalid value |
| `GET /api/v2/me/personalization` | 404 | **200**, `{enabled, activity_learning_enabled, allowed_event_categories, consent_version, personalization_degraded}` |
| `GET /api/v2/me/preferences` | 405 | **200** |

Root cause fix for the recommendation routes: they now live on a dedicated
`recommendation_router = APIRouter(prefix="/recommendations", ...)`,
exported from `employee_router.py` and mounted in `app/main.py` as
`app.include_router(recommendation_router, prefix="/api/v2")` — giving
exactly `/api/v2/recommendations/{id}/...`, matching the spec's literal
path (the old `/me`-prefixed router could never produce this path even if
correctly mounted).

Frontend/backend contract (`POST` vs `PATCH /me/preferences`, the
nonexistent `/me/consent` call, the missing `{habit_id}` in the habit-
confirm call): **already fixed by a concurrent session's commit
`545525b` "fix(frontend): connect all backend endpoints to UI"** before
this task began. Re-verified in this session (not re-fixed) — see §12.

## 9. Personalization Failure Behavior

`PersonalizationContext` gained a `personalization_degraded: bool` field
(`app/schemas/v2/employee.py`), set `True` only when the personalization
store itself raises (distinct from `enabled=False`, an employee's
deliberate opt-out). Verified with **real fault injection** this time
(the original audit found the old test only exercised "no data seeded",
never the actual `except Exception` branch):

```python
monkeypatch.setattr("app.api.v2.employee_router.get_consent", _raises_RuntimeError)
GET /api/v2/me/context
-> 200
-> personalization_context.enabled == False
-> personalization_context.personalization_degraded == True
-> personalization_context.preferences == {"default_case_view": "dashboard", ...}  (safe defaults)
-> authorization_context.permissions UNCHANGED (["case:read","case:write","approval:request"])
-> authorization_context.customer_scope UNCHANGED
```

`personalization_degraded` observability event and a `metrics.increment
("reliability.personalization_degraded")` counter fire on this path (§11
event list).

## 10. Backend Role Enforcement

`require_capability(identity, capability)` (new, `employee_router.py`) —
denies (`403`) unless the capability is **both** present in the IAM-
granted `identity.permissions` **and** allowed by
`CapabilityRegistry.has_capability(role, capability)` — the intersection
the fix-prompt's §6 pseudocode asked for. Wired onto `GET
/me/team/workload` (Manager-only) as a concrete, tested example; not yet
wired onto every route (see §18).

Verified: `has_capability(RoleType.LEGAL_SPECIALIST, "action:approve_own")
is False` — a legal specialist's role policy does not grant CRM-execute-
style capabilities. `require_capability()` raises `403` for
`RM-999` + `"system:manage_personalization"` (not in RM's IAM permission
list) even though nothing client-side prevents asking for it.

## 11. Security Tests Added

`tests/unit/test_v2_employee_context.py` was rewritten (see §12) with the
original 12 required test names preserved plus new ones. Full list, all
passing:

```text
test_missing_token_returns_401
test_invalid_token_returns_401
test_request_body_role_cannot_override_sso_role       (now genuinely attempts a spoof)
test_x_employee_id_cannot_impersonate_manager_in_production_mode  (new)
test_iam_unavailable_returns_503_and_no_data
test_valid_identity_without_permission_returns_403
test_unknown_identity_returns_403_not_500              (new)
test_rm_cannot_access_unassigned_customer
test_specialist_queue_filters_by_subtype
test_manager_aggregate_does_not_return_raw_employee_data
test_tool_execution_revalidates_permission             (new)
test_legal_specialist_cannot_execute_crm_action        (new)
test_disabled_personalization_excludes_habits_from_context
test_deleted_habit_is_not_reused
test_document_content_cannot_create_employee_habit
test_cross_employee_context_cache_isolation
test_cross_employee_habit_deletion_is_rejected         (new, explicit)
test_work_item_outside_customer_scope_is_filtered
test_blocked_item_cannot_be_executed
test_recommendation_feedback_is_idempotent             (now hits the real, previously-404 endpoint)
```

Observability events added (`app/observability/runtime.JsonEventLogger`,
the pre-existing house mechanism with automatic secret redaction, writing
to `settings.AUDIT_LOG_PATH`): `identity_verified`, `authentication_failed`,
`authorization_denied`, `iam_unavailable`, `personalization_degraded`,
`preference_updated`, `personalization_enabled`, `personalization_disabled`,
`habit_confirmed`, `habit_deleted`, `next_best_work_ranked`,
`recommendation_accepted`/`_edited`/`_rejected`/`_not_applicable`. Not
added: `customer_scope_denied`, `work_item_filtered`, `role_router_decision`
as separately named events — the filtering already happens inside
`get_next_best_work()`, which does not currently take a logger; flagged as
a P2 gap in §18 rather than force a signature change into a module the
original, working 30-case benchmark also depends on.

## 12. HTTP Contract Tests

All via `fastapi.testclient.TestClient`, not direct function calls:

```text
test_patch_preferences_real_http_contract       -> PATCH /api/v2/me/preferences, 200, persisted (re-read confirms)
test_get_preferences_real_http_contract         -> GET  /api/v2/me/preferences, 200
test_get_personalization_real_http_contract     -> GET  /api/v2/me/personalization, 200
test_enable_personalization_real_http_contract  -> POST /api/v2/me/personalization/enable, 200
test_disable_personalization_real_http_contract -> POST /api/v2/me/personalization/disable, 200
test_accept_recommendation_real_http_contract   -> POST /api/v2/recommendations/{id}/accept, 200
test_edit_recommendation_real_http_contract     -> POST /api/v2/recommendations/{id}/edit, 200
test_reject_recommendation_real_http_contract   -> POST /api/v2/recommendations/{id}/reject, 200
test_unified_recommendation_feedback_contract   -> POST .../feedback, 200 valid / 422 invalid feedback value
```

Frontend JS contract (section 11.5 of the fix prompt): not re-verified by
a browser or E2E run (none available in this environment) — instead,
every `fetch()` call site in `app/static/app.js` that touches `/api/v2/me/*`
was traced and manually diffed against the actual route table in §15;
confirmed to match (already fixed by commit `545525b`, see §8).

## 13. Hero Demo Results

All executed live via `TestClient`, not simulated:

**Scenario A — RM-999**: login (`GET /me/context`, 200) → work queue (200,
ranked, top item has real `reasons`) → `PATCH /me/preferences` (200,
persisted — confirmed by re-fetching context and seeing the new value) →
`POST /api/v2/recommendations/REC-HERO-A/accept` (200 — previously 404) →
context re-fetched, reflects the updated preference. **PASS.**

**Scenario B — SPEC-LEGAL-001**: work queue correctly filtered to
`legal_specialist`-only items (200). Attempted `GET /me/team/workload` →
**403**. **PASS.**

**Scenario C — MGR-HN-01**: `GET /me/team/workload` → 200, aggregate-only
(`blocked_cases`, `sla_risks`, `ai_recommendation_utilization` with
`cohort_minimum_size_met: true` at `cohort_size: 5`). `GET /me/habits`
(their own, empty) → 200 — no cross-employee read exists anywhere in this
router to even attempt reading another employee's habits. **PASS.**

**Scenario D — Failure modes**: `Authorization: Bearer demo-iam_error` →
**503** on both `/me/context` and `/me/work-queue`, response body contains
only the error object, no `employee_id`/`work_context`/queue data.
Personalization failure → see §9 (200, degraded, defaults, permissions
unaffected). **PASS.**

## 14. Full Test Results

```text
python -m pytest -q   (run 1)  -> 1 failed, 299 passed, 652 warnings in 11.91s
python -m pytest -q   (run 2)  -> 1 failed, 299 passed, 652 warnings in 12.12s
FAILED tests/test_ui_v2.py::test_workspace_contains_four_guided_cases_and_expected_outputs
  (identical both runs -- pre-existing, unrelated to the Employee Copilot
  layer, caused by an earlier UI-reskin commit rewriting app/static/index.html;
  not touched by this task)

python -m pytest tests/unit/test_v2_employee_context.py tests/unit/test_v2_employee_eval.py -q
  -> 32 passed, 0 failed
```

299 (full suite passing) = 280 (baseline) + 19 net new (32 employee tests
now vs 13 before, +19). The 652 warnings are all pre-existing
`datetime.utcnow()` deprecation warnings (not introduced by this task —
present in `employee_db.py`/`test_v2_employee_eval.py` before this session
touched them; not in scope to fix per "no new features/cleanup beyond P0").

## 15. Route Table

```text
GET    /api/v2/me
GET    /api/v2/me/context
GET    /api/v2/me/work-queue
GET    /api/v2/me/preferences                    (new)
PATCH  /api/v2/me/preferences
GET    /api/v2/me/habits
POST   /api/v2/me/habits/{habit_id}/confirm
POST   /api/v2/me/habits/{habit_id}/reject
DELETE /api/v2/me/habits/{habit_id}
GET    /api/v2/me/personalization                (new)
POST   /api/v2/me/personalization/enable
POST   /api/v2/me/personalization/disable
GET    /api/v2/me/team/workload
POST   /api/v2/recommendations/{rec_id}/accept    (fixed: was 404)
POST   /api/v2/recommendations/{rec_id}/edit      (fixed: was 404)
POST   /api/v2/recommendations/{rec_id}/reject    (fixed: was 404)
POST   /api/v2/recommendations/{rec_id}/feedback  (new, unified)
```

Printed directly from `app.routes` in this session, not transcribed from
memory.

## 16. Files Changed

| File | Change |
|---|---|
| `app/config.py` | Added `DEMO_AUTH_ENABLED` setting |
| `app/integrations/enterprise.py` | Added `ensure_employee_copilot_demo_personas()`, `map_enterprise_role_to_role_type()` |
| `app/storage/employee_db.py` | `get_db_connection()` reads `settings.V2_DB_PATH` live instead of a module-level cached constant (test isolation) |
| `app/schemas/v2/employee.py` | Added `VerifiedIdentity`, `PersonalizationContext.personalization_degraded` |
| `app/api/v2/employee_router.py` | Rewritten: `require_verified_identity()`, `require_capability()`, `recommendation_router`, `GET /preferences`, `GET /personalization`, observability events, `cases`-table defensive query, module-level schema/seed init |
| `app/main.py` | Mounts the new `recommendation_router` at `/api/v2` |
| `tests/unit/test_v2_employee_context.py` | Rewritten: HTTP-driven, DB-isolated, +7 new tests |
| `tests/unit/test_v2_employee_eval.py` | Added the same DB isolation fixture |
| `data/mock_database/enterprise_core.sqlite3` | 4 rows added to `employees`/`permissions` each (idempotent seed, no existing row touched) |
| `lib/core/api_client.dart` | Added Employee Copilot methods (`getMyContext`, `getMyWorkQueue`, `patchMyPreferences`, `getMyPersonalization`, `setPersonalizationEnabled`, `getMyHabits`, `deleteHabit`, `submitRecommendationFeedback`, `getTeamWorkload`) |
| `lib/core/models/employee_models.dart` | **New.** Plain (non-freezed) Dart models — see §18 for why not `@freezed` |
| `lib/core/controllers/employee_workspace_controller.dart` | **New.** `ChangeNotifier` controller, persona switcher over demo Bearer tokens |
| `lib/features/employee_workspace/employee_workspace_screen.dart` | **New.** Real screen consuming the above |
| `lib/features/queue/queue_screen.dart` | Added a `FloatingActionButton` entry point to the new screen (additive only) |
| `lib/main.dart` | Registers `EmployeeWorkspaceController` provider + `/employee-workspace` route |
| `docs/ROLE_AWARE_P0_FIX_IMPLEMENTATION_REPORT.md` | This file |

## 17. Concurrent File Protection

Worktree isolation was attempted first, per the task's own recommendation:
manual `git worktree add` was rejected by the user; the built-in
`EnterWorktree` tool failed with "not in a git repository" (environment
limitation, not a repo issue — `git` itself works fine in this directory).
User explicitly redirected to work in place on
`feat/v2-employee-copilot-layer`, accepting the risk.

`app/static/app_new.js`: checked via `git status --short` before this task
began and repeatedly during it — never present in any status output taken
in this session (it must have been removed or resolved by whatever other
session created it, before this task's first tool call). It was never
opened, read, edited, staged, or referenced by any change listed in §16.
No `CONCURRENT WORK DETECTED` condition was observed on any other tracked
file during this task — a `git log --oneline -3` re-check immediately
before writing this report showed no new commits beyond `545525b`, the
one already accounted for in §8.

No commit, no push, performed at any point in this task.

## 18. Remaining Gaps

1. **Flutter wiring is UNVERIFIED DUE TO ENVIRONMENT LIMITATION.** No
   `flutter`/`dart` binary is installed in this environment (`which
   flutter`/`which dart` both fail). The new Dart files
   (`employee_models.dart`, `employee_workspace_controller.dart`,
   `employee_workspace_screen.dart`) and the edits to `api_client.dart`/
   `main.dart`/`queue_screen.dart` were written by closely mirroring the
   existing file's exact patterns (const-context usage, `AppColors` tokens
   confirmed to exist by reading `app_theme.dart`, `go_router`
   `context.push`/`context.go` confirmed already used elsewhere in this
   codebase) and manually re-read line-by-line for syntax correctness, but
   **could not be compiled, analyzed, or run**. Deliberately avoided
   `@freezed` models for the new code (would require regenerating checked-
   in `.freezed.dart`/`.g.dart` part files via `build_runner`, which is
   not possible without the SDK) in favor of plain hand-written classes
   with manual `fromJson`.
2. **Pre-existing `/api/v1` case-queue calls in `api_client.dart` are
   still broken** (target the removed V1 API) — out of scope for this P0
   pass (the fix prompt's scope was the Employee Copilot layer's own
   contract, not the unrelated case-queue screens), not fixed here.
3. **Tool-execution permission revalidation is only partially wired.**
   `require_capability()` is real and tested (§10, §11) but is only
   applied to `GET /me/team/workload`. There is no endpoint in this layer
   that actually executes a CRM/case action (recommendations are advisory
   feedback only), so there was no natural second call site to wire it
   onto without inventing a new endpoint — which the fix prompt explicitly
   forbids ("không mở rộng tính năng mới"). The deeper gap from the
   original audit — `NextBestWorkItem.excluded_actions` is still a
   title-substring heuristic, not linked to the real `Approval`/`Evidence`
   state in `app/actions/executor.py`/`app/safety/evidence_validator.py`
   — is **not fixed** in this pass; fixing it correctly would require a
   `case_id` column on `employee_work_items` and a cross-module read from
   `V2Repository`, judged too large a change to do safely without
   dedicated design time in this pass.
4. **NBW tie-break order still does not match the original spec's 5-field
   order** (regulatory severity / SLA remaining / commitment time /
   created / id) — not touched in this pass; `next_best_work.py`'s scoring
   logic itself was out of this fix prompt's stated scope.
5. **Observability event coverage is not 100%** of the requested list —
   `customer_scope_denied`, `work_item_filtered`, `role_router_decision`
   are not separately emitted (see §11 for why).
6. `datetime.utcnow()` deprecation warnings (652 of them) are pre-existing,
   not newly introduced, and not cleaned up here (out of P0 scope).
7. Cold-start correctness (`init_employee_db()`/
   `ensure_employee_copilot_demo_personas()`/`V2Repository()` all now run
   at `employee_router.py` import time) was verified by construction and
   by the isolated-DB tests passing from a fresh temp file each time, but
   was not separately verified against a literal `rm -rf data/` fresh-
   clone scenario in this session.

## 19. Acceptance Criteria

| Criterion | Status |
|---|---|
| Production mode does not trust `X-Employee-ID` | **Met** — verified live, `DEMO_AUTH_ENABLED=false` |
| Identity from SSO/demo token server-side | **Met** |
| Role cannot be overridden | **Met** — spoof attempt tested, no effect |
| 401/403/503 semantics correct | **Met** — verified live for all three |
| One authorization source of truth | **Met** — `employee_router.py` now imports and uses only `SQLiteSSOAdapter`/`SQLiteIAMAdapter`/`EmployeeContextService`; `employee_db.py` no longer resolves identity |
| Capability Registry is policy-mapper only | **Met** — unchanged, `require_capability()` intersects it with real IAM permissions |
| Permission revalidated before retrieval | **Met** — every route depends on `require_verified_identity`, resolved fresh per request, no caching |
| Permission revalidated before tool execution | **Partially met** — see §18.3 |
| No cross-employee/customer leakage | **Met** — re-verified live |
| Manager sees aggregate only | **Met** — re-verified live |
| PATCH preferences persists | **Met** — verified via re-fetch |
| Personalization enable/disable works | **Met** |
| Recommendation feedback works, idempotent | **Met** — was 404, now 200, idempotency test passes |
| Frontend calls correct method/path | **Met** (already fixed by `545525b`, re-verified) for the browser demo UI; Flutter wiring added but **unverified** (§18.1) |
| IAM failure fails closed | **Met** |
| Personalization failure fails soft | **Met** — real fault injection this time |
| Targeted security tests pass | **Met** — 32/32 |
| HTTP contract tests pass | **Met** |
| Hero demo read+write passes | **Met** |
| Full suite passes twice | **Met** (with the one pre-existing, disclosed, out-of-scope failure both times) |
| `app/static/app_new.js` untouched | **Met** |
| No commit/push | **Met** |

## 20. Final Verdict

```text
BASELINE SCORE (from prior audit):        59 / 100
P0 BLOCKERS AT BASELINE:                  6
P0 BLOCKERS FIXED THIS PASS:              5 fully, 1 partially (§18.3)

FULL SUITE:            299 passed, 1 pre-existing unrelated failure (x2 runs, stable)
EMPLOYEE COPILOT TESTS: 32 passed, 0 failed (was 13)
HERO DEMO:              PASS (RM read+write, Legal, Manager, IAM failure, personalization failure)
FLUTTER WIRING:         UNVERIFIED DUE TO ENVIRONMENT LIMITATION (no SDK; code written, not compiled)

ESTIMATED RE-AUDIT SCORE RANGE: high-70s to low-80s out of 100.
Not independently re-scored against the original 100-point rubric in this
task (that is the next audit's job, not something to self-assign here) --
given as a range, not a claimed number, because several §18 gaps
(tie-break order, full tool-execution linkage to real Approval/Evidence
state, incomplete observability event coverage, unverified Flutter code)
would still cost points under that rubric's own hard-cap rules.

REMAINING P0-ADJACENT GAP: tool-execution revalidation is not fully linked
to the real approval/evidence system (§18.3) -- the single largest reason
this is not claimed as a full 100% P0 clear.
```
