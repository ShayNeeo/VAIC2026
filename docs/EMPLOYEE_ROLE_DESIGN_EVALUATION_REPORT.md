# Employee Role Design Evaluation Report

Scope: **role/business/security design only** — how RM, Product/Legal/
Operations Specialist, and Manager are divided, not implementation
completeness of the P0 fixes (see `docs/ROLE_AWARE_REPO_VERIFICATION_REPORT.md`
and `docs/ROLE_AWARE_P0_FIX_IMPLEMENTATION_REPORT.md` for that). Read-only:
no code, tests, or docs were changed to produce this report. Every table
below was built by reading the actual code and, where marked, by executing
real HTTP requests against the live app.

**Source-of-truth note:** as with the two prior audits in this
conversation, `<ROLE_AWARE_PLAN_PATH>` was left as an unfilled placeholder
and no standalone multi-role design document exists anywhere in this repo
(`plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md` is the closest match, but it
describes a *single*-employee context-assembly pipeline, not a multi-role
RM/Specialist/Manager taxonomy — it predates and is orthogonal to the
Role-Aware Employee Copilot layer). This audit evaluates the role design
against the specification embedded directly in the audit prompt (§2, §5–§13)
and against the actual demand of the sales-case customer journey visible
in the rest of the codebase, per that prompt's own fallback instruction.

## 1. Executive Summary

The role split (RM / Product Specialist / Legal Specialist / Operations
Specialist / Manager) is a sound, industry-standard shape for a corporate
banking sales desk, and the parts of it that were built this session are
genuinely correct: identity is IAM-derived (not client-declared), customer
scope and specialist-subtype queue isolation are real and verified live,
Manager is provably aggregate-only, and personalization/habit data cannot
grant privilege. That is the good news, and it is real, not theoretical.

The design has one significant, concrete gap that keeps it out of the
"ready to pilot" band: **Product, Legal, and Operations Specialists can
see their queue but cannot act on it.** Every case-mutating endpoint in
the codebase (`resume`, `approve`, `reject`, `approval-preview`) is gated
by `owned(case_id, employee_id)`, which only ever matches the case's
*assigned RM* — there is no code path anywhere by which a Legal Specialist
clears a legal block, a Product Specialist confirms a bundle, or an
Operations Specialist marks a checklist item done. The Next Best Work
engine correctly tells a Legal Specialist "this case needs you"
(`waiting_for_roles: ["legal_specialist"]`), but there is nothing for them
to click. In the current implementation, the RM is the only actor who can
ever change a case's outcome — the specialist roles are informationally
real (correct visibility, correct isolation) but operationally decorative.
This is the single largest finding in this report and drives the hard
score cap in §16.

## 2. Final Score

```text
FINAL ROLE DESIGN SCORE: 70 / 100
CLASSIFICATION: 70-79 — Chấp nhận được cho MVP nhưng cần chỉnh
```

Raw rubric total was 71 (§17 below); one hard cap applies (§16) and caps
it at 70 since 71 > 70.

## 3. Role Inventory

| Role | Nguồn định nghĩa | Workspace | Customer scope | Allowed actions (as actually enforced) | Forbidden actions | Status |
|---|---|---|---|---|---|---|
| `relationship_manager` (RM) | `RoleType.RM` (`app/schemas/v2/employee.py`), seeded `RM-999` (`enterprise_core.sqlite3`), `CapabilityRegistry` | RM Workspace (own, both `app/static/app.js` and Flutter `EmployeeWorkspaceScreen`) | `["COMP-ABC","COMP-XYZ","COMP-MP"]`, from real IAM `access_scope.managed_customer_ids` | Read own context/work-queue, edit own preferences, create/resume/approve/reject own cases (`owned()` check in `app/api/v2/router.py`), accept/edit/reject own recommendations | Manager dashboard (403, verified live) | **IMPLEMENTED AND VERIFIED** |
| `product_specialist` | Same sources, seeded `SPEC-PROD-001` | Shared "Specialist Workspace" (browser UI: `role.endsWith("_specialist")` branch in `app.js:279`) | Same 3 customers (IAM-seeded identically to RM for demo purposes) | Read own role-filtered work queue, own context/personalization | Manager dashboard; **no case-mutation endpoint exists for this role at all** (§8) | **PARTIALLY DESIGNED** — visibility real, action path missing |
| `legal_specialist` | Same sources, seeded `SPEC-LEGAL-001` | Shared Specialist Workspace | Same 3 customers | Read own role-filtered work queue, own context/personalization | Manager dashboard; **no case-mutation endpoint** (§8) | **PARTIALLY DESIGNED** |
| `operations_specialist` | Same sources, seeded `SPEC-OPS-001` | Shared Specialist Workspace | Same 3 customers | Read own role-filtered work queue, own context/personalization | Manager dashboard; **no case-mutation endpoint** (§8) | **PARTIALLY DESIGNED** |
| `manager` | Same sources, seeded `MGR-HN-01` | Manager Console | Same 3 customers (used only for its own `/me/context`; the aggregate dashboard ignores scope and reads global counts) | `GET /me/team/workload` (aggregate only, verified live) | Reading any individual employee's preferences/habits (no endpoint exists to do so — verified: no route in `employee_router.py` takes another employee's ID as a parameter) | **IMPLEMENTED AND VERIFIED** |
| `auditor` | `RoleType.AUDITOR` enum value + one `CapabilityRegistry` entry (`{"case:read","audit:view_history","audit:export_report"}`) | None | None seeded | None enforced anywhere | — | **DOCUMENTED ONLY** — no seeded employee, no test, no endpoint checks for it, not in the frontend role switcher |
| `admin` | `RoleType.ADMIN` enum value + one `CapabilityRegistry` entry | None | None seeded | None enforced anywhere | — | **DOCUMENTED ONLY** |
| Team Lead | — | — | — | — | — | **NOT FOUND** — does not exist in any form (enum, policy, seed, doc) |

Consistency check: role *names* match exactly across backend
(`RoleType` values), the enterprise IAM role-mapping
(`map_enterprise_role_to_role_type`), the browser demo UI
(`app.js:277`'s `roleLabel` map), and the new Flutter persona switcher
(`kDemoPersonas`). No duplicate names or drift found. `AUDITOR`/`ADMIN`
exist only in the enum and the policy map — they are the one place names
are defined without any corresponding workspace, seed data, or UI branch.

## 4. Role Responsibility Review

### 4.1 Relationship Manager

Matches the spec's expected list closely for the parts that are wired:
manages assigned customers (scope-enforced, verified), creates/resumes
cases, sees missing information via the pre-existing eligibility/workflow
engine, requests specialist review implicitly (a `pending_review` status
routes `waiting_for_roles: ["legal_specialist"]` into `WorkContext`),
prepares drafts (via the pre-existing Operations service), approves own
drafts (token-bound, `owned()`-gated). Correctly **cannot**: self-approve a
high-risk case (`RiskGuardrailGate` forces `need_review`, never `approve`,
whenever `risk_level="high"` — see §8), read another employee's data,
reach the Manager dashboard.

**Assessment:** RM is not overloaded in principle, but *is* overloaded in
practice as an unintended side effect of §4.2–4.4's gap: because no
specialist role can act on a case, the RM ends up being the only actor who
can ever resolve a `pending_review`/blocked case, even one that is
substantively a legal or product question. This is a workflow-design
consequence, not a stated design intent.

### 4.2 Product Specialist

`CapabilityRegistry` grants `product:recommend`, `product:verify_fit`,
`product:add_justification`, `proposal:review` — a sensible, distinct
capability set (not copy-pasted from RM or another specialist). **None of
these capabilities are checked by any actual endpoint.** The role's entire
real-world footprint today is: see a role-filtered Next Best Work queue
(verified live, correctly isolated — no RM- or Legal-only items leak in),
manage own preferences, submit recommendation feedback on *their own*
recommended items (a `POST /api/v2/recommendations/{id}/feedback` call
that only writes a feedback row, never touches case state). There is no
"confirm product-fit" action that changes anything an RM or the workflow
engine would see. **Status: PARTIALLY DESIGNED** — correct visibility,
correct isolation, no consequential action.

### 4.3 Legal & Compliance Specialist

Same structural gap as Product, with a sharper business consequence
because Legal is the role the workflow explicitly names as the blocker
(`WorkContext.waiting_for_roles` hardcodes `"legal_specialist"` whenever
a case's status is `pending_review` — `app/api/v2/employee_router.py`,
`get_my_context()`). The system correctly *identifies* that a case is
waiting on Legal. It has no endpoint for Legal to clear that wait. Their
`CapabilityRegistry` entry (`legal:verify_evidence`,
`legal:check_issue`, `legal:block_non_eligible`) describes exactly the
missing capability, unimplemented. **Status: PARTIALLY DESIGNED**, and
this is the report's single most important finding (§1, §16).

### 4.4 Operations Specialist

Same pattern again: correct capability *definitions*
(`ops:prepare_task`, `ops:generate_checklist`,
`ops:update_implementation`), correct queue isolation, zero wiring to any
endpoint that actually prepares a checklist, retries a failed action, or
reviews a payload. The pre-existing `app/actions/executor.py`
(`ActionExecutorV2`) — the actual place "failed/replayed action" logic
lives — has no role check at all; it is only ever reachable via the
RM-owned `execute` endpoint. **Status: PARTIALLY DESIGNED**.

### 4.5 Sales Manager

The best-implemented non-RM role. `GET /me/team/workload` genuinely
returns aggregate-only data (`blocked_cases`, `sla_risks`,
`ai_recommendation_utilization` with a `cohort_minimum_size_met` gate at
`cohort_size >= 5`) and is verifiably blocked for every other role (403,
tested live for RM/Product/Legal/Operations). No endpoint exists for a
manager to read any individual employee's habits/preferences, and no
endpoint exists for a manager to reassign a case or override a policy —
which satisfies "Manager không được... Approve thay role chuyên trách" by
the same absence-of-capability pattern that hurts the specialists above
(here, the absence is the *correct* outcome). **Status: IMPLEMENTED AND
VERIFIED.**

## 5. Missing and Redundant Roles

- **Auditor**: genuinely useful for a bank pilot (read-only evidence/
  approval/action history export), and the report's own §6 correctly
  frames it as pilot-scope, not MVP-required. Current status:
  **DOCUMENTED ONLY** — recommend keeping it out of the MVP hero demo
  exactly as the prompt suggests, and building it only when a real
  compliance stakeholder asks for export, not preemptively.
- **Administrator**: same verdict — pilot-scope, currently a stub. No
  policy-management, no config-management surface exists yet to
  administer, so there is nothing for this role to do even if implemented
  today.
- **Team Lead**: does not exist in any form. Given the MVP has exactly one
  Manager persona and no evidence of a two-tier management structure
  (regional vs. branch) anywhere in the seed data or docs, there is no
  current signal this is needed. **Do not add it** — it would be adding
  role complexity without a corresponding responsibility gap to fill,
  which the prompt's own §6 explicitly warns against.
- **No redundant/duplicate role found** among RM/Product/Legal/Operations/
  Manager — each has a distinct, non-overlapping `CapabilityRegistry`
  entry and a distinct customer-facing purpose. The redundancy risk is not
  "too many roles," it is "three of the five roles have no way to
  discharge their named responsibility" (§4.2–§4.4).

## 6. RACI Matrix

Built from actual code (which endpoint exists, which role can call it),
not from aspiration. Where an activity has no real endpoint for the
nominally-responsible role, this is marked explicitly rather than
papered over.

| Activity | RM | Product | Legal | Operations | Manager | Auditor | Admin |
|---|--:|--:|--:|--:|--:|--:|--:|
| Create sales case | **A/R** | - | - | - | I | - | - |
| View customer context | **A/R** (own scope) | I (queue only) | I (queue only) | I (queue only) | I (aggregate) | - | - |
| Edit customer snapshot | **A/R** | - | - | - | - | - | - |
| Confirm extracted profile | **A/R** | - | - | - | - | - | - |
| Recommend product bundle | I | **A/R*** | - | - | - | - | - |
| Review product evidence | I | **A/R*** | - | - | - | - | - |
| Review legal evidence | I | - | **A/R*** | - | - | - | - |
| Resolve UBO conflict | **A/R** (only actor who *can*) | - | R* (no path) | - | - | - | - |
| Generate missing-document checklist | **A/R** | - | - | **R*** (no path) | - | - | - |
| Prepare proposal | **A/R** | C | - | - | - | - | - |
| Prepare email draft | **A/R** | - | - | - | - | - | - |
| Create opportunity draft | **A/R** | - | - | - | - | - | - |
| Create follow-up task | **A/R** | - | - | - | - | - | - |
| Request approval | **A/R** | - | - | - | - | - | - |
| Approve draft (risk_level=none only) | **A/R** | - | - | - | - | - | - |
| Approve draft (risk_level=high) | **NO ROLE CAN — see §8** | - | - | - | - | - | - |
| Execute approved action | **A/R** | - | - | - | - | - | - |
| Review failed action | **A/R** (default, no Ops path exists) | - | - | R* (no path) | - | - | - |
| View audit trail | I (own case only) | - | - | - | I | A/R* (unimplemented) | - |
| View team workload | - | - | - | - | **A/R** | - | - |
| Modify role policy | - | - | - | - | - | - | A/R* (unimplemented) |

`*` = the capability is named in `CapabilityRegistry` and/or surfaced by
`waiting_for_roles`/Next Best Work, but **no API endpoint currently lets
that role discharge it** — the RACI cell reflects design intent, not
enforced reality.

**Findings against §7's checklist:**
- Every activity **does** have exactly one nominal Accountable role — no
  ambiguous double-accountability found.
- **"Approve draft (risk_level=high)" has no Accountable role at all** in
  the *implemented* system: `RiskGuardrailGate` forces `need_review` for
  any high-risk case and nothing currently transitions a case out of
  `need_review` except an RM re-running analysis after uploading new
  documents (which only helps a `pending_information` case, a different
  status) — this is the concrete instance of **MISSING RESPONSIBILITY**
  the report keeps surfacing.
- Legal review and business approval are **not** conflated — good: the
  RM's approval token only ever authorizes the *action payload* (CRM/task
  creation), never a legal or eligibility decision, which remains
  deterministic and machine-decided (`EligibilityEngine`,
  `EvidenceValidator`). This separation is real and correctly designed.

## 7. Separation of Duties

| SoD Rule | Expected separation | Actual roles | Risk | Status |
|---|---|---|---|---|
| Propose vs. approve (low-risk case) | Different actor, or a genuinely low-stakes action | RM proposes (creates case) AND approves (own token) | Low — `risk_level` is deterministic and `none` only when Eligibility/Evidence both cleared; this is confirming an AI-drafted administrative payload, not overriding a credit decision | **ACCEPTABLE FOR MVP** |
| Propose vs. approve (high-risk case) | A different, qualified role must clear the flag before any approval is possible | **Nobody** — `RiskGuardrailGate` never emits `outcome="approve"` when `risk_level="high"`; the case is stuck at `need_review` with no defined resolver | Structural block prevents an unsafe auto-approval, but also means no legitimate resolution path exists either | **MISSING RESPONSIBILITY** (not an active SoD violation, but its mirror image — safety by paralysis rather than by design) |
| Approve vs. execute | — | Same RM, but gated by a separate, cryptographically-bound, one-time approval token (`ApprovalServiceV2`) verified independently by `ActionExecutorV2` before execution | Low — this is a legitimate "confirm, then a second system independently re-verifies" pattern, not a rubber stamp | **WELL DESIGNED** |
| Product self-confirms legal evidence | Must not happen | Cannot happen — Product has no case-mutation endpoint at all (see §4.2); evidence validation is done deterministically by `EvidenceValidator`, not by any specialist role | None found | **WELL DESIGNED** (by absence of capability, not by an explicit rule) |
| Legal self-creates and self-executes a CRM action | Must not happen | Cannot happen — same reason | None found | **WELL DESIGNED** |
| Manager can override any policy | Must not happen | No override endpoint exists anywhere for Manager | None found | **WELL DESIGNED** |
| Admin can read/write customer data unchecked | Must not happen | Admin role has no implementation at all — cannot currently read anything | None found (because nothing exists yet) | **NOT APPLICABLE — unimplemented** |
| RM can self-expand customer scope | Must not happen | `customer_scope` is always IAM-derived, never client- or self-editable — no endpoint accepts a scope value from the caller | None found | **WELL DESIGNED** |

No `CRITICAL SOD GAP` (propose+approve+execute a genuinely high-risk
action by one role) was found — the system's actual failure mode is the
opposite: it is *safe* by never letting anyone, including the right
specialist, clear a high-risk flag through this layer at all.

## 8. Role Handoffs

| From | To | Trigger | Payload | Expected result | Return/escalation | Status |
|---|---|---|---|---|---|---|
| RM | Product | Complex/multi-product query (`ComplexityRouter`) | Case context | Product reviews queue item | **None — no notification, no return path; Product would have to independently notice a queue item** | **PARTIALLY DESIGNED** |
| RM | Legal | `pending_review`/eligibility failure | `waiting_for_roles: ["legal_specialist"]` set on `WorkContext` | Legal reviews and clears the block | **No return path exists** — no endpoint for Legal to signal resolution back to the case | **MISSING RESPONSIBILITY** |
| RM | Operations | Case reaches `pending_approval`/prepares for execution | Execution plan/checklist (existing `OperationsService`, pre-Employee-Copilot) | Ops prepares checklist | Ops has no dedicated view or action surface of its own beyond the generic role-filtered NBW queue | **PARTIALLY DESIGNED** |
| Product → Legal | — | — | — | — | **Not found** — no direct specialist-to-specialist handoff exists; everything routes back through the RM-owned case | **NOT FOUND** |
| Legal → Operations | — | — | — | — | **Not found**, same reason | **NOT FOUND** |
| Specialist → RM | Recommendation feedback | `accept`/`edit`/`reject`/`feedback` | Feedback row (`employee_recommendation_feedback`) | — | Feedback is stored but **nothing reads it back to notify the RM** — it currently only feeds the Manager's aggregate utilization number | **PARTIALLY DESIGNED** |
| RM → Approval | `approval-preview` → `approve` | Exact payload hash | Token issuance/consumption | Idempotent, audited | Well-defined, works | **IMPLEMENTED AND VERIFIED** |
| Approval → Action Executor | Token verified | Payload | CRM/task creation (mock) | Audited, idempotent | Well-defined | **IMPLEMENTED AND VERIFIED** |
| Action failure → Operations/RM | Execution error | — | — | **No retry/replay endpoint reachable by any role in this layer** (the fix-prompt's own §11.4 asked for a `test_tool_execution_revalidates_permission`-style check partly because this gap was already suspected) | — | **NOT FOUND** |

**Stuck-case check:** yes — any case that reaches `need_review` with
`risk_level="high"` has no defined return path in the current
implementation (confirmed above). This is not a hypothetical edge case;
it is the *only* outcome for a hard eligibility failure or invalid
evidence, i.e. exactly the cases where getting a human review right
matters most.

**SLA/escalation check:** no SLA-breach escalation path exists between
roles — Manager can *see* `sla_risks` in the aggregate count, but nothing
routes an overdue item to anyone; there is no "escalate to Manager" action
anywhere in the code.

## 9. Employee Context by Role

Every role currently receives the **same generic `WorkContext` shape**
(`active_case_id`, `assigned_customer_ids`, `pending_task_ids`,
`blocked_case_ids`, `waiting_for_roles`) regardless of role — there is no
role-specific context assembly (no `ProductContext`/`LegalContext`/
`OperationsContext`/`ManagerContext` distinct shape exists in
`app/schemas/v2/employee.py`, despite the audit prompt's §10 describing
exactly such role-specific fields: UBO/KYC conflicts for Legal,
low-confidence recommendations for Product, checklist/SOP references for
Operations). What each role *actually* gets that differs is the **Next
Best Work queue contents** (correctly role-filtered, §11), not the
context snapshot itself.

- **Context correctness:** what exists is correct as far as it goes (no
  leakage, correctly scoped), just under-specified for non-RM roles.
- **No excess/leaked data** found for any role.
- **Sufficiency:** RM's context is workable; Product/Legal/Operations'
  context is thin — they cannot see *why* a work item needs their subtype
  of attention beyond the item's `title`/`reasons` strings, no structured
  conflict/evidence-status field is surfaced to them the way §10 of the
  audit prompt specifies.
- **Provenance:** present uniformly (`provenance_map`), but values
  (`source_version: "v1.2"`, etc.) are hardcoded literals, not derived
  from a real versioned IAM/CRM source — same finding as the prior P0
  audit, unchanged.
- **Staleness:** `expires_at` is computed but never checked/enforced
  anywhere (same finding as the prior audit).

## 10. Next Best Work by Role

Verified live (§16's test run): role-based hard filtering works correctly
— a Legal Specialist's queue never contains an RM- or Product-only item,
and vice versa (`role.value != role_required: continue` in
`get_next_best_work`). Explanation strings (`reasons`) are generic
templates ("Nhiệm vụ thông thường thuộc phạm vi chăm sóc được phân công")
rather than role-specific business language as the prompt's example list
suggests (e.g. "Resolve UBO conflict" as a distinct, named recommendation
type) — the underlying data model does not currently distinguish *why
a task belongs to Legal* beyond its `role_required` field. No role was
observed being recommended a wrong-type action (e.g. Legal being told to
"create product bundle") — the hard filter genuinely prevents this class
of error.

## 11. Specialist Workspace Evaluation

The grouped "Specialist Workspace" (one UI branch,
`role.endsWith("_specialist")` in `app.js:279`; same generic
`EmployeeWorkspaceScreen` in the new Flutter code) is backed by **real,
independently-verified backend permission separation by subtype** — this
is the important part, and it is correct: `SPEC-LEGAL-001` cannot see
`SPEC-PROD-001`'s queue items or vice versa (verified live, zero
cross-subtype leakage in either direction), and neither can invoke a tool
the other subtype's `CapabilityRegistry` entry would allow (though, per
§4.2–4.4, *neither* can currently invoke any tool at all, which trivially
satisfies "cannot call the other's tool" without proving the intended
protection actually works once real tools exist).

**Verdict: ACCEPTABLE FOR MVP.** The UI grouping is a reasonable, low-
effort choice for a hackathon build and does not itself cause any
permission leakage — the backend correctly enforces subtype boundaries
independent of how the UI groups them. It should not be graded down for
being visually shared. It should be revisited once real specialist
actions exist, at which point the UI may want subtype-specific panels for
usability (not security) reasons.

## 12. Privacy and Personalization

Re-confirmed, unchanged from the P0 fix pass:

- Only the owning employee can read/enable/disable/delete their own
  preferences/consent/habits — verified live (cross-employee habit
  deletion silently rejected, `success: false`, no data touched).
- Manager's aggregate view (`ai_recommendation_utilization`) contains only
  counts grouped by feedback type, never per-employee — verified live, no
  individual ranking field exists anywhere in the response shape.
- Candidate (unconfirmed) habits are excluded from
  `confirmed_habits` and cannot influence any authorization decision —
  confirmed by code path (habits never touch `AuthorizationContext`) and
  by test (`test_document_content_cannot_create_employee_habit`).
- Personalization store failure sets `personalization_degraded=true` and
  substitutes safe UI defaults; `authorization_context` is provably
  unaffected (separate code path, verified with real fault injection in
  the P0 pass).
- Consent has a `consent_version` field but no explicit re-consent flow
  when the version changes — minor, not a hard violation.

No hard-rule violation found in this category — this is the strongest
section of the design.

## 13. MVP vs. Pilot Role Scope

```text
MVP (implement now, already largely done):
  - Relationship Manager           -- fully implemented
  - Specialist (shared workspace)
      - Product subtype            -- visibility only, no action surface
      - Legal subtype              -- visibility only, no action surface
      - Operations subtype         -- visibility only, no action surface
  - Sales Manager                  -- fully implemented

Pilot (do not build until a real stakeholder need appears):
  - Auditor      -- policy-only until export/compliance requirement is concrete
  - Administrator -- policy-only until there is a policy surface to administer
  - Team Lead     -- no current signal this is needed; do not add speculatively
```

The role *count* is appropriately small for an MVP (5 functioning
personas). The problem is not "too many roles" or "too complex" — it is
that 3 of the 5 are read-only in practice. The single highest-leverage
next step for MVP feasibility is **not** adding roles, it is adding the
missing case-mutation/resolution endpoints for the 3 specialist roles that
already have correct identity, scope, and queue isolation waiting for
something to do.

## 14. Role Test Scenarios

25 scenarios executed live via `TestClient` against the running app in
this session (5 RM, 4 Product, 4 Legal, 3 Operations, 2 Manager, 2
cross-role security, plus 4 inline assertion checks) — **24/25 passed**;
the one failure (`ROLE-009`, a Product Specialist probing a
case-mutation endpoint) returned `422` instead of the expected `404`
because the test script's request body didn't satisfy `ResumeBody`'s
schema before the ownership check ran — a test-script imprecision, not a
finding about the system; the underlying claim ("no specialist role has a
working case-mutation path") is independently confirmed by code reading
in §4/§7/§8, not solely by this one HTTP call.

```text
Correct-role routing accuracy:      24/25 = 96% (of executed scenarios)
Wrong-role action rate:             0/25 = 0% (no role ever performed another role's action)
Missing responsibility rate:        NOT COMPUTED AS A CODE METRIC — established qualitatively via
                                     §4/§7/§8 code reading (3 of 5 core activities have no
                                     implemented resolver role); not fabricated as a percentage
                                     since no case-outcome dataset exists to compute it against.
Duplicate accountability rate:      0% — RACI in §6 found no activity with 2+ Accountable roles
Cross-role data leakage rate:       0/4 direct leakage probes triggered a leak (ROLE-007b, 011b, 017b, 020b)
Permission violation rate:          0/25 — no scenario succeeded where it should have been denied
Handoff completion rate:            NOT MEASURABLE — no handoff in §8 has a completion signal to measure
Role-specific recommendation Precision@3: NOT RE-COMPUTED here — see the existing 30-case
                                     benchmark in docs/ROLE_AWARE_P0_FIX_IMPLEMENTATION_REPORT.md §14,
                                     which already measures NBW ranking quality; re-running it was
                                     out of this audit's role-design scope.
```

Full scenario table (case_id / role / method / path / expected / actual /
pass) is reproducible from the executed script; representative rows are
quoted throughout §4–§12 rather than duplicated in full here.

## 15. Security and Leakage Risks

| Risk | Found? | Evidence |
|---|---|---|
| Role escalation via header/body | **No** | `ROLE-020`/`020b`: RM + `X-Role: manager` header still returns `roles: ["relationship_manager"]`, still 403 on Manager dashboard |
| Cross-employee habit mutation | **No** | `ROLE-019`: Legal attempting to delete an RM-owned habit ID returns `success: false`, no mutation |
| Cross-subtype queue leakage | **No** | `ROLE-007b`, `ROLE-011b`: zero cross-role items found in either direction |
| Manager reading individual data | **No** | `ROLE-017b`: no `preferences`/`habits`/`individual_ranking` key in the aggregate response |
| Unimplemented role granting silent access | **No** | Auditor/Admin have zero seeded credentials and zero endpoint checks — they cannot be used to gain access, only to be *denied* by default (fail-closed by absence, not fail-open) |
| **Specialist role unable to discharge its named responsibility** | **Yes** | §4.2–§4.4, §7, §8 — not a leakage/authorization risk, but a genuine business-continuity risk: a legally-blocked case has no human resolver path today |

## 16. Hard Score Caps

Checked every condition in the prompt's §18:

| Condition | Applies? |
|---|---|
| Role tự khai báo từ client | No — always IAM-derived |
| Không kiểm tra customer scope | No — verified enforced |
| Product/Legal/Operations dùng chung quyền backend | No — distinct `CapabilityRegistry` sets per subtype, even though none are currently wired to an endpoint |
| Một role propose+approve+execute action rủi ro cao | No — structurally impossible; high-risk cases can never reach `approve` (§7) |
| Manager xem raw habit/preference | No — verified aggregate-only |
| **Có activity không role nào chịu trách nhiệm** | **Yes** — "resolve a `need_review`/high-risk case" and "specialist review resolution" have no implemented Accountable actor (§6, §8) → **cap 70** |
| Không có RACI/handoff rõ | No (borderline) — real, if incomplete, signals exist in code (`waiting_for_roles`, role-filtered NBW); a full RACI/handoff matrix was buildable from evidence in §6/§8, which itself argues against "unclear" |
| Role chỉ tồn tại trong tài liệu, chưa có enforcement | Judgment call: applies narrowly to `Auditor`/`Admin` only (§3, §5), which are explicitly pilot-scope, not MVP-required, per the prompt's own §6 and §13 — **not applied as a blanket cap**, since all 5 MVP-required roles (RM/Product/Legal/Operations/Manager) do have real enforcement (identity, scope, queue isolation) |
| Không có test tình huống cross-role | No — 25 scenarios executed, including explicit cross-role security probes |

Only one cap applies: **max 70**. Raw rubric total (§17) is 71 → capped
to **70**.

## 17. Scoring Rubric

```text
A. Role coverage — 10/15
   - Journey has an accountable role: 3/6 (RM yes; specialist "review"
     activities have no working resolver)
   - No extra role: 3/3
   - No abandoned responsibility: 1/3 (need_review resolution gap)
   - MVP-reasonable role count: 3/3

B. Responsibility clarity — 8/15
   - RACI clear: 2/5 (buildable, but reveals real gaps once built)
   - One Accountable per activity: 2/4
   - No dangerous duplicate accountability: 3/3
   - Handoff clear: 1/3 (no return path for 3 of 4 specialist handoffs)

C. Authorization and least privilege — 18/20
   - Role from IAM/SSO: 4/4
   - Customer scope correct: 4/4
   - Tool permission per role: 2/4 (defined but barely enforced --
     nothing to enforce against yet)
   - Specialist subtype isolation: 3/3
   - Manager aggregate-only: 3/3
   - No privilege escalation: 2/2

D. Separation of duties — 8/15
   - Propose/approve/execute separated sensibly: 3/5
   - Product/Legal/Operations correctly separated: 2/4 (separated because
     they can't act at all, not because a rule enforces correct separated
     action)
   - Manager/Admin not all-powerful: 3/3
   - Audit/read-only role clear if needed: 0/3 (Auditor unimplemented)

E. Employee context quality — 5/10
   - Context matches role: 1/4 (generic shape for all non-RM roles)
   - No excess/leaked data: 2/2
   - Context sufficient to work: 1/2
   - Provenance/freshness: 1/2

F. Next Best Work by role — 9/10
   - Task matches role: 3/3
   - Hard filter blocks wrong role: 3/3
   - Explanation adequate: 1/2 (generic, not role-specific business language)
   - No self-execution: 2/2

G. Privacy and personalization — 9.5/10
   - Habit grants no privilege: 2/2
   - Employee control: 2/2
   - Manager aggregate only: 3/3
   - No employee ranking: 2/2
   - Consent clarity: 0.5/1

H. MVP feasibility — 3.5/5
   - Demoable in current scope: 3/3
   - Clear MVP/pilot roadmap: 0.5/2

RAW TOTAL: 10+8+18+8+5+9+9.5+3.5 = 71/100
```

## 18. P0 Role Design Gaps

1. **No case-mutation/resolution endpoint exists for Product, Legal, or
   Operations Specialist.** This is the report's headline finding — see
   §1, §4.2–§4.4, §6, §7, §8, §16.
2. **A `need_review`/high-risk case has no defined human resolver in the
   implemented system.** The risk gate correctly refuses to auto-approve
   it, but nothing then routes it to a role that can act — it is safe but
   stuck.
3. **No specialist-to-RM or specialist-to-specialist return/notification
   path.** Recommendation feedback is stored but never read back into the
   case or surfaced to the RM; a Legal review, even if it could be
   completed, has no way to inform the RM it was completed.

## 19. P1 Improvements

1. Employee Context is one generic shape for every role; give Legal a
   structured conflict/evidence-status field, Product a confidence/bundle
   field, Operations a checklist/SOP field, per the audit prompt's own
   §10 spec — not just a shared `WorkContext`.
2. Next Best Work `reasons` strings are generic templates; make them
   reference the actual triggering fact (e.g. "UBO chưa xác minh — hết hạn
   SLA trong 2 ngày" instead of a fixed sentence).
3. Build `Auditor` only when a concrete compliance/export requirement
   exists — do not add it speculatively (correctly deferred already, no
   action needed unless requirements change).
4. Add an SLA-breach escalation path to Manager (currently visible in
   aggregate count only, with no routing action).
5. Provenance values in `EmployeeContextSnapshot` are hardcoded literals;
   derive them from real source versions once a real IAM exists.

## 20. Final Recommended Role Model

```text
MVP (keep exactly as-is, but close the P0 gaps in §18 before pilot):

RM (relationship_manager)
  Purpose: single point of accountability for a corporate customer relationship.
  Responsibilities: own customer/case lifecycle end to end; the only role
    that can currently mutate case state.
  Allowed data: own assigned customers/cases/tasks (IAM-scoped).
  Allowed actions: create/resume/reject case, request specialist review
    (implicit via routing), approve own low-risk drafts, execute approved
    actions.
  Forbidden actions: self-approve a high-risk case (structurally
    impossible, by design), read other employees' data, Manager dashboard.
  Handoff targets: Product/Legal/Operations (currently visibility-only --
    see P0 gap), Approval/Executor (fully working).
  Next Best Work types: resume case, request missing document, review
    proposal draft.

Specialist (shared workspace, three IAM-distinct subtypes)
  Product Specialist
    Purpose: confirm product fit and bundle correctness for complex cases.
    Responsibilities (once P0 gap closed): review product-fit queue item,
      confirm/reject a recommended bundle, flag a low-confidence match.
    Allowed data: role-filtered work queue, own preferences.
    Forbidden actions: legal approval, CRM execution, customer reassignment.
    Next Best Work types: review low-confidence recommendation, validate
      multi-product bundle.
  Legal & Compliance Specialist
    Purpose: clear legal/eligibility blocks a deterministic engine flagged
      as needing human judgment.
    Responsibilities (once P0 gap closed): resolve UBO/KYC conflict,
      review expired/invalid evidence, set case to clear/blocked.
    Forbidden actions: propose products, execute CRM actions, read RM
      preferences.
    Next Best Work types: resolve UBO conflict, review expired source,
      validate high-risk claim.
  Operations Specialist
    Purpose: prepare and verify execution readiness.
    Responsibilities (once P0 gap closed): prepare checklist, retry a
      failed mock action, review a payload mismatch.
    Forbidden actions: confirm legal eligibility, approve customer
      proposals, send unapproved content.
    Next Best Work types: prepare approved checklist, retry failed action,
      review payload mismatch.

Sales Manager
  Purpose: team-level visibility and bottleneck detection, not case-level
    intervention.
  Responsibilities: monitor aggregate SLA/blocked-case counts, spot team
    bottlenecks.
  Allowed data: aggregate-only, cohort-gated (>=5 employees) utilization.
  Forbidden actions: read individual habit/preference, rank employees by
    AI acceptance, approve on behalf of a specialist role.
  Next Best Work types: review team bottleneck (not yet implemented as a
    distinct recommendation type for this role).

Pilot (build only when a concrete requirement appears):

Auditor    -- read-only evidence/approval/action history export.
Administrator -- role/policy/knowledge-source/retention management.
Team Lead  -- no current signal this is needed; do not add speculatively.
```

## 21. Final Verdict

```text
FINAL ROLE DESIGN SCORE: 70 / 100
CLASSIFICATION: 70-79 -- Chấp nhận được cho MVP nhưng cần chỉnh
CONFIDENCE: HIGH

ROLE COVERAGE: 67%        (10/15)
RESPONSIBILITY CLARITY: 53%   (8/15)
LEAST PRIVILEGE COMPLIANCE: 90%  (18/20)
SEPARATION OF DUTIES: 53%     (8/15)
CONTEXT FIT BY ROLE: 50%      (5/10)
MVP FEASIBILITY: 70%          (3.5/5)

ROLES WELL DESIGNED: 2  (Relationship Manager, Sales Manager)
ROLES NEEDING REVISION: 3  (Product Specialist, Legal Specialist, Operations Specialist -- visibility correct, action surface missing)
MISSING ROLES: 0  (Auditor/Admin correctly deferred to pilot; Team Lead correctly not added)
REDUNDANT ROLES: 0

SPECIALIST WORKSPACE VERDICT:
ACCEPTABLE FOR MVP. Shared UI is not a security problem -- backend subtype
isolation is real and verified. Revisit for usability (not security)
reasons once specialist roles have real actions to perform.

TOP 5 ROLE DESIGN GAPS:
1. No case-mutation/resolution endpoint for Product, Legal, or Operations
   Specialist -- they can see their queue, not act on it.
2. A high-risk (`need_review`) case has no defined human resolver role in
   the implemented system -- safe, but stuck.
3. No specialist-to-RM or specialist-to-specialist return/notification
   path -- feedback is stored but never surfaced back into the case.
4. Employee Context is one generic shape for every role instead of the
   role-specific fields (UBO conflicts for Legal, confidence for Product,
   checklist for Operations) the design should have.
5. Auditor/Admin roles are named in the schema and policy map with zero
   implementation -- harmless today (correctly pilot-scoped), but should
   not be listed as "supported roles" anywhere without that caveat.

FINAL RECOMMENDED ROLE STRUCTURE:
Keep the current 5-role MVP shape (RM, Product/Legal/Operations
Specialist, Manager) exactly as named -- it is the right shape. Do not add
Auditor/Admin/Team Lead until a concrete pilot requirement names them.
Spend the next engineering pass entirely on §18's P0 gaps: give the three
specialist roles a real action surface (case-mutation or resolution
endpoints gated the same way RM's are), define who resolves a
`need_review` case, and close the loop from specialist feedback back to
the RM.
```
