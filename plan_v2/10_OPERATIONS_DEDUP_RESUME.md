# 10 — Operations, Artifact Reuse, Deduplication and Resume

## 1. Objective

Tạo hoặc cập nhật checklist, decision brief, email draft và case/task draft; ưu tiên reuse/update trước create và không phát sinh external action.

## 2. Inputs

- Validated intent/context.
- Product recommendations with evidence.
- Eligibility result and missing information.
- Existing case/task/artifacts.
- SOP/SLA version.
- RM preferences allowed for formatting.

Operations không được nhận raw unvalidated LLM claims.

## 3. Outputs

`operations_result` gồm:

- `decision_brief`.
- `required_document_checklist`.
- `missing_information`.
- `customer_message_draft`.
- `crm_case_draft`.
- `task_drafts`.
- `artifact_actions`: create/update/reuse/skip.
- `dedup_result`.
- `sop_version`.

Mọi output là draft cho đến module 11 approve/execute.

## 4. Checklist engine

Checklist = union có giải thích của:

- Product prerequisites.
- Legal missing documents.
- KYC/UBO requirements.
- SOP step requirements.
- Context-specific documents.

Deduplicate bằng controlled document taxonomy, không chỉ string equality.

Per item:

```text
document_type_id, display_name, reason
required_for_product_ids, severity
current_status, existing_document_id
source_rule_ids, evidence_ids
```

## 5. Email/message drafting

- Dùng template trước, LLM chỉ cải thiện văn phong.
- Chỉ dùng structured verified fields.
- Không thêm phí/lãi suất/hạn mức không có evidence.
- Recipient từ CRM là candidate; external send cần RM verify.
- Draft giữ version và content hash.
- RM edit tạo version mới; invalidate approval cũ.

Required sections:

1. Mục đích liên hệ.
2. Danh sách hồ sơ/thông tin cần bổ sung.
3. Hướng dẫn/kênh phản hồi nếu có nguồn.
4. Disclaimer phù hợp.
5. Không cam kết phê duyệt tín dụng.

## 6. Task deduplication

Canonical dedup key:

```text
tenant/org
+ customer_id
+ case_id or business_request_id
+ task_type
+ product_id (nullable)
+ workflow_step
+ normalized subject hash
```

Search active tasks in states: pending, assigned, in_progress, blocked. Completed task may be reused only if input/policy version unchanged and within validity window.

Decision:

| Existing artifact | Same input/version | Action |
|---|---|---|
| Active task | yes | reuse/attach |
| Active task | no | update if allowed, else create linked revision |
| Completed valid task | yes | reuse result |
| Completed stale | no | create new with supersedes link |
| Email draft unsent | same purpose | update existing draft |
| CRM case active | same request | append/update, not create duplicate |

## 7. Artifact cache and reuse

Cache/reuse key includes:

- customer ID.
- normalized input hash.
- product/policy/SOP versions.
- context profile version.
- workflow version.
- permission scope.

Never reuse across customers or permission scopes.

## 8. Resume behavior

When information arrives:

1. Store new artifact/version.
2. Compute changed field/document taxonomy.
3. Ask workflow impact graph for affected nodes.
4. Re-run affected nodes.
5. Diff old/new operations artifacts.
6. Update existing task/email draft.
7. Reset approval if approved payload changed.

## 9. SLA

- SLA from versioned SOP table/rule.
- LLM cannot invent SLA.
- VIP/urgent flags require source or RM selection.
- Due date calculation handles business calendar/timezone.

## 10. Proposed code artifacts

| File | Responsibility |
|---|---|
| `app/operations/models.py` | Draft/checklist/artifact models |
| `app/operations/checklist.py` | Controlled checklist union |
| `app/operations/brief.py` | Decision brief |
| `app/operations/message.py` | Template + drafting |
| `app/operations/dedup.py` | Canonical key/search/decision |
| `app/operations/artifacts.py` | Version/reuse/update logic |
| `app/operations/sla.py` | SOP/business calendar |
| `app/operations/service.py` | Facade |

## 11. Tests

- ABC email contains UBO and latest BCTC.
- Same missing item from product/legal appears once with both sources.
- Existing active task reused.
- Changed product version invalidates stale task result.
- RM email edit changes payload hash and invalidates approval.
- Resume updates draft, does not create second draft.
- SLA comes only from SOP registry.
- No unverified claim appears in customer message.

## 12. Acceptance

- Duplicate task/case rate = 0 in replay/concurrency tests.
- Checklist completeness ≥ 95% golden set.
- External side effects = 0 from Operations module.

