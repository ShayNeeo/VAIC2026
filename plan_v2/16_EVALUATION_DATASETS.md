# 16 — Evaluation Datasets and Regression Framework

## 1. Objective

Định nghĩa dữ liệu, rubric và runner để đo riêng từng lớp: context, intent, retrieval, eligibility, workflow, safety và end-to-end. Không dùng demo đẹp làm bằng chứng chất lượng.

## 2. Dataset layout

```text
data/eval/v2/
├── context_cases.jsonl
├── intent_cases.jsonl
├── product_rag_cases.jsonl
├── eligibility_cases.jsonl
├── workflow_cases.jsonl
├── security_cases.jsonl
├── reliability_cases.jsonl
└── e2e_cases.jsonl
```

Mỗi record có `case_id`, `dataset_version`, `difficulty`, `tags`, input, expected behavior và reviewer metadata.

## 3. Context/intent record schema

```json
{
  "case_id": "INT-001",
  "dataset_version": "2.0.0",
  "difficulty": "medium",
  "tags": ["workspace_context", "no_clarification"],
  "employee_context": {},
  "workspace_context": {},
  "conversation_state": {},
  "message": "Kiểm tra còn thiếu gì",
  "expected": {
    "primary_intent": "check_missing_documents",
    "required_resolved_slots": {
      "customer_id": "COMP-ABC",
      "case_id": "CASE-001"
    },
    "forbidden_questions": ["Khách hàng nào?", "Case nào?"],
    "expected_action": "continue_workflow"
  }
}
```

## 4. RAG record schema

Required:

- Query + resolved context/filters.
- Expected product/document/chunk IDs.
- Relevant/non-relevant source labels.
- Expected OOS behavior.
- Effective date and access scope.
- Expected answer claims/citations when applicable.

Metrics computed deterministically: Hit@K, Recall@K, Precision@K, MRR, source/version correctness, ACL violations.

## 5. Eligibility record schema

Required:

- Customer/product/document snapshots with versions.
- Active rule registry version.
- Expected per-rule outcome.
- Expected aggregate status.
- Missing information.
- Expected evidence IDs.
- Forbidden unsafe outcome.

High-risk cases require two human reviewers and adjudication.

## 6. Workflow record schema

Required:

- Initial state.
- Incoming event/change.
- Expected transition.
- Expected nodes executed/skipped.
- Expected preserved/invalidated artifacts.
- Expected external action count.

Use for resume, replay, concurrency and max-loop tests.

## 7. Security dataset

Categories:

- Direct/indirect prompt injection.
- Tool privilege escalation.
- Cross-customer/RM access.
- PII extraction/log leakage.
- Approval token tampering/replay/expiry.
- Payload change after approval.
- Malicious/unsupported documents.
- Retrieval ACL bypass.

Expected result must specify block/allow, stable error/event code and audit severity.

## 8. Labeling guideline

- Annotators see current taxonomy/rule versions.
- Label explicit facts separately from inferred fields.
- Every expected intent/entity links to message/context evidence.
- Ambiguous cases include all acceptable hypotheses.
- Clarification labels explain decision impact.
- Product/legal labels include source/version.
- Disagreement adjudicated and recorded.

Track inter-annotator agreement for intent/entity/high-risk outcomes.

## 9. Automated versus judge metrics

### Deterministic first

- Schema validity.
- Exact intent/entities.
- Slot source/confidence policy.
- Retrieval IDs/ranks.
- Rule/transition outcomes.
- Tool/action counts.
- Citation quote/source match.
- Security allow/deny.

### LLM-as-judge only where needed

- User-goal semantic equivalence.
- Email clarity/tone.
- Decision brief completeness.
- Claim support when deterministic/semantic checks inconclusive.

Judge rubric fixed/versioned, calibrated against human labels and not sole gate for safety.

## 10. Regression runner

Proposed artifacts:

| File | Responsibility |
|---|---|
| `evaluation/loaders.py` | Versioned JSONL validation |
| `evaluation/context_eval.py` | Context/slot metrics |
| `evaluation/intent_eval.py` | Intent/entity/clarification |
| `evaluation/rag_eval.py` | Retrieval/source metrics |
| `evaluation/eligibility_eval.py` | Rule/outcome metrics |
| `evaluation/workflow_eval.py` | Transition/resume/action counts |
| `evaluation/security_eval.py` | Block/leak/replay metrics |
| `evaluation/report.py` | JSON + Markdown report |

Runner records model/prompt/index/rule/workflow versions and seed/config.

## 11. CI gates

- Contract/unit tests every PR.
- Changed module’s relevant eval subset every PR.
- Full offline eval nightly or before release.
- Security suite required for approval/tool/context changes.
- Compare against last approved baseline; fail on threshold breach or statistically/materially worse key metric.

## 12. Online evaluation

Pilot-only with governance:

- RM correction events.
- Unnecessary clarification feedback.
- Draft edit rate.
- Dedup hit/false-positive review.
- Sampled evidence/eligibility human review.
- No raw sensitive content exported to evaluation platform.

## 13. Acceptance

- Dataset schemas validate.
- Every MVP acceptance scenario has at least one case.
- Reports are reproducible and versioned.
- Safety metrics are deterministic and gating.

