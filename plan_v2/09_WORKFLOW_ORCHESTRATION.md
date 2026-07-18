# 09 — Workflow Orchestration and State Machine

## 1. Objective

Điều phối deterministic, kiểm soát dependency, stop/retry/escalation và cho phép partial resume mà không chạy lại toàn bộ hệ thống.

## 2. Nodes

| Node | Reads | Writes | External tools |
|---|---|---|---|
| `collect_context` | request/session | context | read-only context tools |
| `extract_intent` | context/request | intent_result | model gateway |
| `resolve_slots` | context/intent | intent_result | read-only tools |
| `route_complexity` | intent | workflow route | none |
| `plan_tasks` | intent/route | workflow.tasks | none |
| `retrieve_products` | intent/context | product_result/evidence | product search |
| `evaluate_eligibility` | product/context/docs | eligibility/evidence | legal/KYC read tools |
| `validate_evidence` | results/evidence | evidence flags | knowledge read |
| `prepare_operations` | all validated results | operations drafts | none |
| `risk_guardrail_gate` | eligibility/evidence results | risk_gate_result, final status | none |
| `deduplicate_actions` | drafts/existing tasks | dedup result | CRM/task read |
| `await_information` | missing info | status | none |
| `await_approval` | validated drafts | approval pending | none |
| `execute_actions` | approved payload | execution result | write tools |
| `complete_case` | results | final state | none |

## 3. State transitions

```text
new
→ understanding
→ clarification_required (only if decision-changing missing slot)
→ planned
→ in_analysis
→ pending_information | pending_review | pending_approval
→ executing
→ completed | rejected | failed
```

Transition validation is centralized. Modules emit commands/events, not direct arbitrary status changes.

## 4. DAG planning

- Task IDs deterministic within case/run.
- Dependency graph checked for unknown IDs and cycles.
- Parallelize Product candidates/legal checks only when inputs independent.
- Max adaptive loops = 3.
- Cycle fallback: safe sequential order + audit warning.
- Planner cannot call business write tools.

## 5. Routing

Simple route criteria:

- One read-only intent.
- No external action.
- No high-risk eligibility decision.
- Context resolved above threshold.

Complex route if:

- Multi-intent.
- Credit/legal/KYC.
- Missing information loop.
- Draft/create/send intent.
- Cross-product dependencies.

Routing result and reasons logged; no hidden CoT.

## 6. Retry policy

| Failure | Retry | Max | Notes |
|---|---:|---:|---|
| Model timeout/5xx | yes | 2 | exponential backoff |
| Schema parse | repair | 1 | then fallback/typed failure |
| Read tool timeout | if safe | 1 | cache fallback |
| Write tool timeout | only with idempotency | 1 | query status before retry |
| Permission denied | no | 0 | fail closed |
| Invalid evidence | no automatic | 0 | re-retrieve or review |

## 7. Partial resume / impact graph

Changed artifact maps to earliest impacted node:

| Change | Resume nodes | Preserve |
|---|---|---|
| New UBO document | eligibility → evidence → operations | intent/product |
| New BCTC | eligibility → evidence → operations | intent/product |
| Customer switched | context → all downstream | audit only |
| Request goal changed | intent → all downstream | employee context |
| Product catalog version changed | product → eligibility → downstream | intent/context |
| Email text edited by RM | approval payload only | analysis results |

Every node stores `input_hash`, `output_ref`, dependencies and version. Resume invalidates only descendants with changed hash/version.

## 8. Idempotency

- Workflow run key: `case_id + request_message_id + workflow_version`.
- Node cache key: node + normalized input hash + dependency versions.
- External action key defined in module 10/11.
- Duplicate event delivery must not duplicate state transitions/actions.

## 9. Proposed code artifacts

| File | Responsibility |
|---|---|
| `app/workflow/models.py` | Node/task/command/event models |
| `app/workflow/state_machine.py` | Allowed transitions |
| `app/workflow/router.py` | Complexity route — `ComplexityRouter` (implemented 2026-07-18; allowlist of read-only-on-existing-case intents only, see file docstring for why) |
| `app/workflow/risk_gate.py` | Risk & Guardrail Gate — `RiskGuardrailGate` (implemented 2026-07-18; wires eligibility's existing passed/failed/pending_information/pending_review taxonomy from `08_ELIGIBILITY_LEGAL.md` section 5 + Evidence Validator result into one outcome/risk_level, not a new invented policy) |
| `app/workflow/planner.py` | DAG creation/validation |
| `app/workflow/engine.py` | Node execution |
| `app/workflow/retry.py` | Retry policy |
| `app/workflow/impact.py` | Resume dependency graph |
| `app/workflow/idempotency.py` | Run/node keys |
| `app/workflow/nodes/` | Typed node implementations |

## 10. Tests

- Simple read route bypasses planner.
- ABC multi-intent DAG dependencies.
- Cycle detection/fallback.
- Legal blocking transitions pending information.
- Product/legal conflict pending review.
- Max loop enforcement.
- UBO upload resumes only impacted nodes.
- Duplicate event does not rerun external action.
- Invalid transition rejected.

## 11. Acceptance

- Correct routing ≥ 95% golden set.
- No infinite loop.
- Correct resume-node selection ≥ 90% MVP.
- Replayed workflow events do not duplicate side effects.

