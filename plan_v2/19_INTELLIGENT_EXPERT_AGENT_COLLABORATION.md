# 19 — Intelligent Expert Agent Collaboration & Evidence-grade Metadata

## 1. Mục tiêu hiểu được

Nâng cấp V2 từ workflow tuần tự có LLM hỗ trợ thành một hệ thống cộng tác có kiểm soát, trong đó:

1. `ProductExpert`, `CreditExpert` và `InsuranceExpert` có thể tự phân tích nhiệm vụ chuyên môn từ context được giao, dùng tool đúng domain và trả về kết quả có cấu trúc.
2. Expert Agent có thể yêu cầu Agent khác hỗ trợ, nhưng không gọi trực tiếp tool hoặc sửa kết quả thuộc domain khác.
3. `PlannerCoordinator` tạo kế hoạch ban đầu, quản lý vòng cộng tác, giải quyết dependency và tổng hợp phương án cuối.
4. Rule engine, Evidence Validator, Risk Gate và Approval Gate vẫn là lớp deterministic, không bị LLM hoặc Coordinator ghi đè.
5. Mọi kết luận quan trọng phải giải thích được bằng metadata đủ rõ: nguồn nào, phiên bản nào, hiệu lực khi nào, ai sở hữu, retrieval vì sao, claim được chứng minh bởi chunk nào và còn hạn chế gì.

Luồng mục tiêu:

```text
Context + Intent đã xác nhận
→ Coordinator lập DAG nhiệm vụ
→ Expert Agents phân tích độc lập trong domain
→ Collaboration qua message có schema
→ Evidence/Rule/Risk validation
→ Coordinator synthesis
→ RM xem lý do, nguồn, điểm chưa chắc chắn
→ RM approval
→ Executor thực thi payload đã duyệt
```

Hai chỉ tiêu không thay đổi:

- `Unsafe external action rate = 0%`.
- `Eligibility unsafe pass rate = 0%`.

Chỉ tiêu bổ sung:

- `Cross-agent unauthorized tool-call rate = 0%`.
- `Unsupported important claim rate = 0%`.
- `Hard-block override rate = 0%`.
- `Collaboration convergence rate ≥ 95%` trong tối đa 3 vòng.

## 2. Giả định và phạm vi

### 2.1. Giả định

- Context và intent đầu vào đã đi qua V2 Context/Intent/Confidence modules.
- Product, Credit và Insurance có kho dữ liệu riêng, Source Card riêng và tool profile riêng.
- Dữ liệu hiện tại là `SYNTHETIC DEMO DATA`; chưa phải chính sách SHB thật.
- LLM provider được chọn qua port/config; workflow không phụ thuộc trực tiếp một nhà cung cấp.
- Mọi write action vẫn nằm ngoài Expert Agent và chỉ do `ActionExecutor` thực hiện sau approval.

### 2.1.1. Quyết định runtime thống nhất (18/07/2026)

- Ba Expert Agent chạy trong LangGraph là `ProductExpert`, `CreditExpert`, `InsuranceExpert`.
- Legal/Eligibility là bước deterministic dùng Rule Engine và Legal RAG; không được trình bày trên UI như một LLM Expert độc lập.
- Operations là deterministic composer chạy sau Coordinator synthesis; không phải Expert Agent và không có quyền tự thực thi.
- Ba Specialist Workspace tương ứng trực tiếp với ba Expert runtime: Product, Credit, Insurance. Legal/Compliance reviewer vẫn là vai trò kiểm soát nội bộ cho risk gate, không thay đổi kết quả Agent và không được tính vào ba Agent.
- Mọi đoạn cũ trong tài liệu còn mô tả `LegalExpert` hoặc `OperationsExpert` là worker runtime được xem là superseded bởi quyết định này và contract JSON hiện hành.

### 2.2. Trong phạm vi

- Agent manifest và boundary cho từng Expert.
- Typed task, finding, assistance request, constraint và synthesis contract.
- Collaboration loop tối đa 3 vòng, dedup và convergence gate.
- Evidence-grade metadata cho source/document/chunk/retrieval/claim/agent run.
- MCP/tool allowlist theo role, server-side enforcement và negative tests.
- AI Decision Log có thể đọc được nhưng không chứa raw PII, secret hoặc internal chain-of-thought.
- Deterministic fallback khi LLM hoặc MCP unavailable.

### 2.3. Ngoài phạm vi

- Agent tự trị không giới hạn.
- Agent tự thay đổi prompt, policy, tool allowlist hoặc rule registry.
- Agent tự gửi email, tạo CRM case/task hoặc thay đổi dữ liệu thật.
- Fine-tuning trong giai đoạn này.
- Lưu hoặc hiển thị Chain-of-Thought nội bộ.
- Legal Agent tự phê duyệt ngoại lệ hoặc biến hard block thành pass.

## 3. Kiểm tra hướng hiện tại và quyết định chỉnh lại

Prototype hiện tại trong `app/agents/expert_agents.py` và `app/agents/coordinator.py` chứng minh được ý tưởng LLM wrapper + fallback + một vòng đề xuất sản phẩm thay thế. Tuy nhiên chưa được coi là kiến trúc đích.

| Hiện trạng | Vấn đề | Quyết định trong plan mới |
|---|---|---|
| Prompt yêu cầu `Chain-of-Thought (CoT)` trong output | Không nên yêu cầu, lưu hoặc hiển thị reasoning nội bộ; log dễ dài, nhạy cảm và khó kiểm chứng | Thay bằng `decision_rationale_summary`, `facts`, `inferences`, `unknowns`, `assumptions`, `evidence_refs` |
| Role chủ yếu được mô tả bằng system prompt | Prompt không phải authorization boundary | Role lấy từ immutable Agent Manifest + authenticated runtime identity |
| Coordinator gọi trực tiếp object Agent và dùng `engine_ref` private methods | Coupling cao, khó test/replay và Agent chưa thực sự độc lập | Giao tiếp qua typed port + immutable artifact; Coordinator là nơi duy nhất commit SharedCaseState |
| Product Agent có reference trực tiếp tới Product service; Legal/Operations tương tự | Chưa chứng minh fail-closed khi Agent cố gọi tool domain khác | Tool Gateway/MCP profile riêng + exact allowlist + server enforcement |
| Hard-coded product IDs cho alternative query | Catalog thay đổi sẽ làm logic stale | Alternative constraints theo metadata `product_family`, `credit_flag`, `capability`, không hard-code ID |
| Alternative recommendation ghi đè recommendation cũ | Mất dấu sản phẩm bị block và lý do | Giữ `primary_candidates`, `blocked_candidates`, `alternatives`; mỗi revision có lineage |
| Collaboration phụ thuộc `product_agent.client` | Hành vi khác nhau khi có/không có LLM | Coordinator policy deterministic quyết định có collaboration; Agent có LLM/fallback nhưng cùng contract |
| LLM bổ sung text vào fallback result | Chưa có schema riêng cho finding và uncertainty | Validate `ExpertFinding` trước khi nhận; invalid output dùng fallback và ghi degradation event |
| AI log chỉ tóm tắt theo module | Thiếu task/revision/help/conflict/convergence metadata | Bổ sung Agent Run Log và Collaboration Trace đã sanitize |

Plan này supersede phần yêu cầu CoT và “Legal suy luận ngoại lệ hard block” trong bản đính kèm. Hard block chỉ có thể dẫn tới `pending_review`, `rejected` hoặc yêu cầu Product tìm phương án khác; không được chuyển thành pass bởi LLM.

## 4. Bản đồ bài toán → kỹ thuật

| Nhu cầu thực tế | Kỹ thuật áp dụng | Vì sao chọn | Artifact | Cách kiểm chứng |
|---|---|---|---|---|
| Expert hiểu nhiệm vụ riêng | Immutable Agent Manifest + structured task | Role không phụ thuộc prompt tự khai | `AgentManifest`, `ExpertTask` | Contract test, wrong-role test |
| Expert suy luận từ dữ liệu đang có | LLM structured output trên grounded facts + deterministic fallback | Cho phép semantic reasoning nhưng không thay business rule | `ExpertFinding` | Schema validity 100%, citation tests |
| Expert độc lập | Port riêng, runtime riêng, không mutate SharedCaseState | Giảm coupling và side effect chéo | `ExpertAgentPort` | Mutation/ownership tests |
| Expert hỗ trợ nhau | Coordinator-mediated `AssistanceRequest` | Có audit, dedup, loop guard và quyền kiểm soát | Collaboration message contract | E2E collaboration cases |
| Tổng hợp tối ưu | Constraint-aware deterministic synthesis + optional LLM wording | Hard constraints phải thắng; LLM chỉ diễn đạt | `SynthesisResult` | Hard-block preservation tests |
| Metadata thuyết phục | Multi-layer provenance + evidence score breakdown | RM thấy vì sao hệ thống tin một claim | Knowledge/Evidence metadata contracts | Metadata completeness gate |
| Tool đúng Agent | MCP profile isolation + server-side exact allowlist | Không dựa vào prompt để giữ quyền | Tool Registry/MCP endpoints | Unauthorized call rate = 0 |
| Không lộ reasoning nhạy cảm | Rationale summary, no-CoT policy, sanitized log | Đủ giải thích nhưng không lưu nội dung suy luận nội bộ | AI Log schema | Log leakage tests |
| Không lặp vô tận | Revision budget + message dedup + convergence hash | Collaboration phải bounded | `CollaborationSession` | Max-loop/replay tests |

## 5. Nguyên tắc kiến trúc

1. **Bounded autonomy:** Agent tự chủ trong một task và một domain, không tự chủ về quyền hoặc side effect.
2. **Coordinator owns control flow:** Worker không tự gọi lẫn nhau; mọi yêu cầu hỗ trợ đi qua Coordinator.
3. **Coordinator does not own truth:** Coordinator tổng hợp nhưng không được ghi đè hard rule, citation validity, ACL hoặc approval decision.
4. **Deterministic before generative:** Retrieval, rule evaluation, permission, dedup, state transition và payload hash là code deterministic.
5. **Grounded before persuasive:** Không có evidence thì không được dùng văn phong chắc chắn.
6. **No hidden-reasoning persistence:** Không yêu cầu hoặc lưu CoT; chỉ lưu rationale ngắn gắn fact/evidence.
7. **One writer:** Chỉ Workflow/Coordinator commit SharedCaseState; Expert trả immutable artifact.
8. **Fail closed:** Tool denied, stale source, schema invalid, contradiction hoặc missing evidence đều không được tự nâng thành pass.
9. **Synthetic truthfulness:** Metadata và UI luôn chỉ rõ dữ liệu synthetic, không trình bày như chính sách thật.

## 6. Kiến trúc đề xuất

```mermaid
flowchart TD
    RM["RM Workspace"] --> CTX["Context + Intent + Confidence"]
    CTX --> PC["PlannerCoordinator"]
    PC --> DAG["Typed Task DAG"]

    DAG --> PA["ProductExpert Runtime"]
    DAG --> LA0["Legal Global Pre-check"]
    DAG --> OA0["Operations Preliminary Readiness"]

    PA --> PMCP["Product MCP Profile"]
    LA0 --> LMCP["Legal MCP Profile"]
    OA0 --> OMCP["Operations MCP Profile"]

    PA --> BUS["Collaboration Message Bus"]
    LA0 --> BUS
    OA0 --> BUS
    BUS --> PC
    PC --> REV["Revision / Assistance Tasks"]
    REV --> PA
    REV --> LA["Legal Product-specific Evaluation"]
    REV --> OA["Operations Finalization"]

    PA --> FIND["Versioned Expert Findings"]
    LA --> FIND
    OA --> FIND
    FIND --> EV["Evidence Validator"]
    EV --> RG["Rule + Risk Guardrail Gate"]
    RG --> SYN["Constraint-aware Synthesis"]
    SYN --> STATE["SharedCaseState V2.x"]
    STATE --> RM
    RM --> APP["Approval Service"]
    APP --> EXE["ActionExecutor"]
```

`Product`, `Legal` và `Operations` là các specialist runtime độc lập. `Evidence Validator`, `Rule Engine`, `Risk Gate`, `Approval` và `Executor` không được chuyển thành LLM Agent.

## 7. Agent Manifest và trách nhiệm

Mỗi Agent có manifest versioned, load khi khởi động và không được model sửa:

```json
{
  "agent_type": "ProductExpert",
  "manifest_version": "1.0.0",
  "objective": "Tìm và xếp hạng sản phẩm có nguồn",
  "accepted_task_types": ["product_discovery", "product_alternative"],
  "allowed_tools": ["product_search", "product_get_chunk", "product_list_sources"],
  "forbidden_decisions": ["eligibility_pass_fail", "external_action"],
  "output_schema": "ExpertFinding/1.0.0",
  "max_tool_calls": 6,
  "timeout_ms": 20000,
  "fallback_policy": "deterministic_product_service"
}
```

| Component | Input được phép | Tool được phép | Output bắt buộc | Không được làm |
|---|---|---|---|---|
| `PlannerCoordinator` | Context, intent, findings, constraints | Dispatch/status/artifact store; không có domain search | Task DAG, revision requests, synthesis | Không tự tạo product/legal fact; không override hard block |
| `ProductExpert` | Business need, approved customer attributes tối thiểu, constraints | Product search/get/list | Candidate/alternative products, rationale, prerequisites, evidence | Không quyết eligibility, không gọi Legal/Ops tool, không cam kết phí/hạn mức nếu thiếu exact evidence |
| `LegalExpert` | Product finding, customer facts, documents, active rule output | Legal search/get/list; deterministic eligibility engine | Constraints, per-rule result, missing evidence, review requirement | Không đổi product catalog, không miễn hard block, không tạo task/email |
| `OperationsExpert` | Accepted options, legal constraints, documents, SLA/SOP | Operations search/get/list; checklist resolver/draft builder | Checklist, dependencies, SLA reference, drafts | Không thay đổi legal outcome, không gửi/ghi hệ thống thật |
| `EvidenceValidator` | Claims + evidence refs | Exact chunk get + citation verify | Supported/partial/contradicted/stale report | Không discovery rộng, không đề xuất sản phẩm |
| `ActionExecutor` | Approved exact payload | Write tools | External status/ID | Không reasoning, không sửa payload |

## 8. Contract suy luận của Expert

### 8.1. Không dùng Chain-of-Thought

Không tạo field `cot`, `chain_of_thought`, `internal_reasoning`, `thoughts` hoặc tương đương. Agent có thể thực hiện reasoning nội bộ, nhưng output chỉ được chứa thông tin kiểm chứng được:

```json
{
  "finding_id": "FND-PRODUCT-001",
  "agent_type": "ProductExpert",
  "task_id": "TASK-PRODUCT-001",
  "revision": 1,
  "conclusion": "Payroll và Cash Management phù hợp với mục tiêu giảm thao tác chi lương và tập trung dòng tiền.",
  "decision_rationale_summary": [
    "Nhu cầu chi lương được nêu trực tiếp trong request.",
    "Quy mô nhân sự và mô hình nhiều tài khoản khớp metadata phân khúc của hai sản phẩm."
  ],
  "known_facts": [],
  "inferences": [],
  "unknowns": [],
  "assumptions": [],
  "recommendations": [],
  "constraints": [],
  "evidence_refs": [],
  "confidence": {},
  "assistance_requests": []
}
```

### 8.2. Phân biệt fact và inference

- `known_facts`: dữ liệu trực tiếp từ Context/CRM/document/retrieved chunk, có provenance.
- `inferences`: kết luận semantic của Agent; mỗi inference phải tham chiếu fact/evidence.
- `unknowns`: dữ liệu cần nhưng chưa có.
- `assumptions`: giả định tạm thời; không được dùng để pass hard rule.
- `constraints`: điều kiện cứng hoặc giới hạn cần downstream tuân thủ.
- `recommendations`: hành động/giải pháp đề xuất, không phải external action.

### 8.3. Confidence không phải một số tùy ý

Không cho LLM tự sinh một `confidence=0.93` không có cơ sở. Confidence gồm các thành phần:

| Thành phần | Nguồn tính | Ý nghĩa |
|---|---|---|
| `evidence_coverage` | Validator | Tỷ lệ claim có evidence hợp lệ |
| `source_authority` | Source Card | Mức thẩm quyền A–E/decision role |
| `freshness_status` | Effective dates/freshness policy | current, warning, stale, blocked |
| `retrieval_quality` | Dense/sparse/rerank trace | Chất lượng tìm kiếm, không phải correctness cuối |
| `consistency_status` | Conflict detector | consistent, conflicting, unresolved |
| `rule_certainty` | Rule engine | deterministic, not_applicable, unknown |
| `input_completeness` | Required-field checker | Đủ/thiếu input quan trọng |

`display_confidence` chỉ được tính từ policy versioned và dữ liệu calibration; không dùng để override rule/approval.

## 9. Metadata thuyết phục

Metadata phải trả lời được 7 câu hỏi của RM và reviewer:

1. Thông tin này đến từ đâu?
2. Ai chịu trách nhiệm về nguồn?
3. Phiên bản và thời gian hiệu lực là gì?
4. Hệ thống lấy đúng đoạn nào?
5. Vì sao đoạn đó được chọn?
6. Claim nào được đoạn đó hỗ trợ hoặc mâu thuẫn?
7. Có giới hạn, stale, synthetic hoặc permission nào cần biết?

### 9.1. Source-level metadata

| Field bắt buộc | Ví dụ | Vì sao thuyết phục |
|---|---|---|
| `source_id`, `source_name` | `SYN-PRODUCT-REFERENCE-V1` | Định danh ổn định |
| `authority_tier` | `E_SYNTHETIC` | Không đánh đồng demo với policy thật |
| `decision_role` | `DISCOVERY`, `VERIFICATION`, `AUTHORITATIVE` | Nguồn được dùng để làm gì |
| `business_owner`, `data_steward` | Product Owner/Data Steward | Có người chịu trách nhiệm |
| `approval_reference` | `MVP-SYNTHETIC-DATA-ONLY` | Chứng minh publish gate |
| `allowed_uses`, `prohibited_uses` | demo / no production decision | Giới hạn sử dụng rõ ràng |
| `sensitivity`, `residency`, `retention` | INTERNAL/local/repo lifecycle | Quản trị dữ liệu |
| `update_cadence`, `max_age`, `stale_behavior` | manual / 30 days / BLOCK | Freshness có hành vi cụ thể |
| `dataset_version`, `source_hash` | version + SHA-256 | Tái lập index |
| `quality_report_ref` | ingest run ID | Nguồn chỉ serving sau quality gate |

### 9.2. Document-level metadata

```text
document_id, source_id, title, document_type
document_version, publication_date, effective_from, effective_to
lifecycle_status, language, jurisdiction, audience
product_ids, policy_ids, workflow_ids
file_name, mime_type, file_hash
parser_name, parser_version, extraction_quality
ingestion_run_id, indexed_at
access_scope, sensitivity
```

### 9.3. Chunk-level metadata

```text
chunk_id, document_id, document_version, source_id
parent_chunk_id, previous_chunk_id, next_chunk_id
section_path, page_number, line_start, line_end
sheet_name, table_id, row_key, header_context
chunk_type, language, product_ids, rule_ids, workflow_ids
effective_from, effective_to, active, superseded_by
access_scope, segment, industry
content_hash, embedding_model, embedding_version, embedding_dimension
chunking_strategy, chunking_version
synthetic_flag, data_disclaimer
```

Table chunk phải giữ đơn vị, currency, header và row key. Legal rule chunk không được tách `condition/operator/threshold/severity/source_quote` khỏi nhau.

### 9.4. Retrieval metadata

Mỗi lần search ghi và trả tối thiểu:

```text
query_id, trace_id, task_id, agent_type, tool_name
query_hash, query_rewrite_version
metadata_filters, ACL decision, effective_at
candidate_chunk_ids
dense_score, sparse_score, fusion_score, rerank_score, final_rank
threshold, selected/rejected reason
index_version, embedding_version, retrieval_policy_version
latency_ms, degraded_mode, empty_reason
```

Raw query có PII không ghi vào operational log; lưu hash và sanitized summary nếu cần.

### 9.5. Claim/Evidence metadata

```text
claim_id, finding_id, agent_type, claim_type, claim_text_sanitized
support_status: supported | partially_supported | contradicted | stale | unauthorized | missing
evidence_refs[]: chunk_id + content_hash + source/version/location + quote/span
validation_method: exact | deterministic_rule | semantic | human
evidence_coverage, contradiction_refs[]
validator_version, validated_at, review_status
```

### 9.6. Agent-run và collaboration metadata

```text
agent_run_id, agent_type, agent_manifest_version
task_id, task_type, input_artifact_hash, output_artifact_hash
model_provider, model_name, prompt_version, schema_version
tool_policy_version, tools_called, denied_tool_calls
started_at, completed_at, latency_ms, token_usage, estimated_cost
fallback_used, retry_count, stop_reason
revision, parent_finding_id
assistance_request_ids, conflict_ids, convergence_hash
```

Không log raw prompt, raw document/PII, API key, approval token hoặc Chain-of-Thought.

### 9.7. Cách trình bày metadata cho RM

Mỗi đề xuất hiển thị một “Why this?” card:

```text
Đề xuất: Dịch vụ chi lương
Phù hợp vì: nhu cầu chi lương + quy mô nhân sự khớp phân khúc
Nguồn: Product Catalog / phiên bản 2026.07-demo-v2
Vị trí: Payroll > Đối tượng áp dụng
Hiệu lực: 01/01/2026–31/12/2026
Owner: Product Owner
Trạng thái evidence: Supported (2/2 claims)
Giới hạn: SYNTHETIC DEMO DATA — không dùng làm cam kết khách hàng
```

UI không chỉ hiển thị một score. Score phải đi kèm source, evidence coverage, freshness và missing data.

## 10. Tool isolation và MCP profile

### 10.1. Nguyên tắc

- Agent identity đến từ runtime credential, không lấy từ request body hoặc prompt.
- Mỗi Agent kết nối MCP endpoint/token riêng và chỉ discover tool thuộc profile.
- Tool Gateway kiểm lại `agent_type + exact permission + domain + customer/branch scope`.
- Generic cross-domain search chỉ dành cho `KnowledgeAdmin`, không cấp cho Expert Agent.
- Ingestion/update index không expose cho LLM; chỉ Data Steward CLI/job.

### 10.2. Tool matrix

| Agent | MCP profile | Tool được phép | Tool bị cấm điển hình |
|---|---|---|---|
| ProductExpert | `/mcp/product` | `product_search`, `product_get_chunk`, `product_list_sources` | legal search, operations search, CRM write |
| LegalExpert | `/mcp/legal` | `legal_search`, `legal_get_chunk`, `legal_list_sources`, deterministic rule evaluation port | product ranking, operations draft, CRM write |
| OperationsExpert | `/mcp/operations` | `operations_search`, `operations_get_chunk`, `operations_list_sources`, checklist/draft ports | legal decision, product ranking, external send |
| EvidenceValidator | `/mcp/evidence` | `evidence_get_chunk`, `evidence_verify_citation` | broad discovery, write action |
| PlannerCoordinator | internal orchestration | dispatch, status, artifact read, synthesis policy | domain RAG, CRM/email write |
| KnowledgeAdmin | `/mcp` | governed cross-domain QA tools | external action |
| ActionExecutor | action gateway | exact approved write tools | RAG reasoning, payload modification |

Nếu Product cần legal interpretation, Product gửi `AssistanceRequest(target=LegalExpert)` cho Coordinator; Product không được gọi `legal_search`.

## 11. Collaboration protocol

### 11.1. Message types

| Type | Sender | Receiver | Mục đích |
|---|---|---|---|
| `TaskAssignment` | Coordinator | Expert | Giao task có objective, input refs, constraints và budget |
| `ExpertFinding` | Expert | Coordinator | Trả kết luận có evidence và uncertainty |
| `AssistanceRequest` | Expert | Coordinator | Xin domain khác trả lời một câu hỏi cụ thể |
| `ConstraintNotice` | Legal/Risk | Coordinator | Công bố constraint/hard block versioned |
| `RevisionRequest` | Coordinator | Expert | Yêu cầu sửa finding theo constraint mới |
| `ConflictNotice` | Validator/Coordinator | Experts | Nêu hai finding/source mâu thuẫn |
| `SynthesisResult` | Coordinator | Workflow | Kết quả cuối đã bảo toàn constraints |

Agent không gửi message tự do; mọi payload validate bằng `agent_collaboration.schema.json`.

### 11.2. AssistanceRequest bắt buộc cụ thể

```json
{
  "request_id": "HELP-001",
  "from_agent": "LegalExpert",
  "target_agent": "ProductExpert",
  "question_type": "find_non_credit_alternative",
  "question": "Tìm phương án phi tín dụng vẫn đáp ứng mục tiêu quản lý dòng tiền.",
  "input_refs": ["FND-LEGAL-001"],
  "constraints": ["exclude:credit=true"],
  "expected_output": "ExpertFinding",
  "priority": "high"
}
```

Không cho AssistanceRequest chứa lệnh “bỏ qua policy”, yêu cầu tool cụ thể ngoài domain hoặc payload external action.

### 11.3. Vòng cộng tác bounded

```text
Round 0: Coordinator tạo task DAG và budget
Round 1: Expert chạy task độc lập; Legal global pre-check/Ops preview có thể song song Product
Round 2: Product-specific Legal + Operations; Coordinator chuyển assistance/constraint
Round 3: Chỉ revision bị ảnh hưởng; Evidence Validator kiểm claim
Stop: converged | no_new_information | hard_block | budget_exhausted | human_review
```

Guard:

- `max_rounds = 3`.
- `max_assistance_requests_per_agent = 2`.
- Dedup theo `sender + target + question_type + input_hash + constraint_hash`.
- Không chạy lại Agent nếu dependency/output hash không đổi.
- Nếu hai revision liên tiếp có cùng `convergence_hash`, dừng.
- Timeout hoặc schema-invalid dùng deterministic fallback một lần; sau đó `pending_review`.

### 11.4. Quy tắc giải quyết xung đột

Thứ tự ưu tiên:

```text
Authorization/ACL
> deterministic hard rule
> authoritative current source
> verified internal source
> active approved synthetic source
> derived Agent inference
> ungrounded suggestion
```

- Hard block không bị bỏ khỏi kết quả. Candidate chuyển sang `blocked_candidates` kèm reason/evidence.
- Source cùng authority nhưng khác version: phiên bản hiệu lực mới thắng; nếu cùng hiệu lực và mâu thuẫn → `pending_review`.
- Product và Operations không được “biểu quyết” để thắng Legal hard rule.
- Coordinator không tự hòa giải contradiction bằng LLM wording.

## 12. Dữ liệu mẫu và pipeline cho Expert Agent

### 12.1. Dữ liệu hiện có được dùng

| Domain | File hiện có | Cách dùng |
|---|---|---|
| Product | `products.csv`, `product_pricing_limits.csv`, `solution_bundles.csv` | Product master, pricing reference, bundle candidates |
| Product docs | Cash Management, Payroll, Trade Finance Markdown | Section-aware product/reference chunks |
| Legal | `product_policies.csv`, KYC, Working Capital, Guarantee Markdown | Rule/evidence chunks; không tự quyết pass/fail |
| Operations | `sop_workflows.csv`, `checklist_definitions.csv`, `sla_rules.csv`, `email_templates.csv`, `raci_matrix.csv` | SOP/checklist/SLA/template/RACI chunks |
| Customer | `enterprise_profiles.csv`, accounts/loans/UBO/documents | Structured mock CRM tool; không đưa vào shared vector RAG |
| Evaluation | customer requests, cases, tool examples, golden/security cases | Test/eval only; không serving như policy |

### 12.2. Quy tắc generation

- Mọi record sinh thêm phải có `synthetic_flag=true` và namespace ID ổn định.
- Không dùng tên/số tài khoản/PII thật.
- Cross-reference phải hợp lệ: product policy/checklist/pricing chỉ trỏ product tồn tại.
- Ngày hiệu lực không mâu thuẫn; có ít nhất một expired/superseded version để test.
- Mỗi product có tối thiểu overview, prerequisites, pricing reference, policy link, checklist link.
- Mỗi hard-rule case có positive, missing, failed và conflicting test record.
- Mỗi Agent có ít nhất 10 normal, 5 edge, 5 adversarial cases.

### 12.3. Ingestion pipeline

```text
Manifest + Source Cards
→ path/UTF-8/MIME validation
→ schema + uniqueness + foreign-key checks
→ effective-date + lifecycle checks
→ PII/injection quarantine
→ structure/table-aware parsing
→ metadata enrichment
→ chunk + hash + embedding/sparse index
→ offline retrieval/evidence eval
→ atomic publish
→ ingest report + index manifest
```

Publish là all-or-nothing. Nếu một source fail quality gate, serving index cũ tiếp tục hoạt động và ingestion run ghi `failed`.

## 13. Control flow end-to-end

1. Context Service tạo snapshot, provenance, freshness và ACL.
2. Intent/Confidence module tạo resolved intent; chỉ hỏi khi thiếu thông tin có decision impact.
3. PlannerCoordinator tạo `CollaborationSession` và typed task DAG.
4. ProductExpert tìm candidates từ Product MCP, trả facts/inferences/unknowns/evidence.
5. Legal global pre-check có thể chạy song song; product-specific evaluation chỉ chạy sau khi có product IDs.
6. Operations có thể chuẩn bị generic readiness preview, nhưng checklist cuối phụ thuộc accepted product + Legal constraints.
7. Expert gửi AssistanceRequest nếu cần domain khác; Coordinator validate và tạo task mới.
8. Nếu credit hard-block, Product nhận constraint `exclude credit`; blocked credit vẫn được giữ trong audit/UI.
9. Evidence Validator xác minh claim/citation/hash/version/effective date.
10. Coordinator synthesis chọn phương án chính và alternative theo constraints; không thay đổi rule outcome.
11. Risk Gate quyết định `pending_information`, `pending_review` hoặc `pending_approval`.
12. Operations artifacts và customer draft được tạo; mọi external side effect vẫn rỗng.
13. RM xem metadata/evidence/conflict/unknown, sửa và phê duyệt.
14. ActionExecutor thực hiện exact payload đã duyệt bằng idempotency key.

## 14. Synthesis policy

Synthesis không phải “Agent nào nói hay hơn thì thắng”. Coordinator dùng các gate theo thứ tự:

1. Loại khỏi primary mọi candidate ACL-invalid, stale-blocked, unsupported hoặc hard-blocked.
2. Giữ candidate bị block trong `blocked_candidates` để giải thích.
3. Chấm candidate còn lại theo objective fit, evidence coverage, input completeness và operational readiness.
4. Chọn một `primary_solution`; tối đa hai `alternative_solutions` có khác biệt thực sự.
5. Hợp nhất missing information theo canonical field/document ID.
6. Hợp nhất checklist/task theo dedup key và dependency.
7. Sinh RM brief và customer draft chỉ từ supported claims.

Output:

```text
primary_solution
alternative_solutions[]
blocked_candidates[] + blocking evidence
unresolved_conflicts[]
missing_information[]
operations_plan
customer_draft
evidence_validation_summary
human_review_requirements[]
```

## 15. Contract và state cần bổ sung

### 15.1. Contract mới

| File | Trách nhiệm |
|---|---|
| `contracts/agent_collaboration.schema.json` | Task, finding, assistance, constraint, session, synthesis |
| `contracts/knowledge_metadata.schema.json` | Source/document/chunk/retrieval/claim metadata |
| `contracts/tool_contracts.json` | Bổ sung exact caller/tool profiles và MCP endpoint |

### 15.2. SharedCaseState

Thay đổi additive dự kiến `2.1.0`:

```text
collaboration_session
expert_findings[]
assistance_requests[]
constraints[]
synthesis_result
agent_run_refs[]
```

Không nhét raw conversation hoặc raw prompt vào state. Artifact lớn lưu ở artifact repository; SharedCaseState chỉ giữ typed summary/ref/hash.

## 16. Thành phần cần tạo/sửa

| Artifact | Loại | Trách nhiệm |
|---|---|---|
| `app/agents/manifests.py` | New | Load/validate immutable Agent Manifest |
| `app/agents/contracts.py` | New | Pydantic task/finding/message/synthesis models |
| `app/agents/base.py` | New | Provider-neutral structured LLM port + fallback |
| `app/agents/product_expert.py` | Refactor | Product reasoning trên grounded result |
| `app/agents/legal_expert.py` | Refactor | Legal explanation + constraint; rule remains deterministic |
| `app/agents/operations_expert.py` | Refactor | SOP/checklist/draft reasoning |
| `app/agents/coordinator.py` | Refactor | DAG, collaboration, convergence, synthesis; không dùng `engine_ref` private API |
| `app/workflow/agent_node.py` | New | Adapter giữa Coordinator và Workflow engine |
| `app/workflow/synthesis.py` | New | Deterministic constraint-aware synthesis |
| `app/tools/agent_gateway.py` | New | Exact allowlist + identity/scope enforcement |
| `services/rag_mcp/*` | Modify | MCP profiles Product/Legal/Ops/Evidence/Admin |
| `app/observability/agent_trace.py` | New | Sanitized Agent Run/Collaboration log |
| `app/safety/evidence_validator.py` | Modify | Claim support/contradiction/stale validation |
| `plan_v2/contracts/*` | Modify/New | Machine-readable source of truth |
| `data/eval/v2/agent_collaboration_cases.json` | New | Golden collaboration/security cases |

## 17. Safety và guardrails

- Agent runtime identity lấy từ trusted orchestrator/service credential.
- Prompt/user/document không thể đổi role hoặc tool permission.
- Tool call validate input schema, allowlist, ACL, effective date, timeout và result schema.
- Product output chỉ chứa controlled product IDs.
- Legal `overall_status` luôn lấy từ Eligibility Engine; LLM chỉ bổ sung explanation có evidence.
- Operations output luôn `external_side_effects=[]`.
- Evidence-invalid claim bị loại khỏi customer draft và primary recommendation.
- Prompt injection trong retrieved document được coi là data và quarantine.
- No-CoT output validator từ chối các field/từ khóa reasoning nội bộ đã cấu trúc.
- Raw PII được minimize/mask trước Agent; không ghi operational log.
- External action vẫn approval-bound, payload-hashed và idempotent.

## 18. Observability và AI Decision Log

Mỗi case cần có ba lớp log tách biệt:

1. `Audit Log`: actor/action/state transition/tool decision, bất biến.
2. `Agent Run Log`: model/prompt/schema/tool/latency/token/fallback/output hash.
3. `AI Decision Log`: rationale summary dễ đọc, nguồn/evidence, unknown/conflict/next step.

Event tối thiểu:

```text
collaboration_started
expert_task_assigned
expert_finding_validated
assistance_requested
assistance_deduplicated
constraint_issued
revision_requested
tool_call_allowed | tool_call_denied
evidence_supported | evidence_contradicted
collaboration_converged | collaboration_budget_exhausted
synthesis_completed
human_review_required
```

Không lưu Agent-to-Agent raw chat. Lưu typed message, sanitized summary và content hash.

## 19. Reliability và fallback

| Failure | Behavior |
|---|---|
| LLM timeout/provider unavailable | Expert dùng deterministic service; same output contract; `fallback_used=true` |
| MCP profile unavailable | Circuit breaker; không gọi profile khác; manual/source browser fallback |
| Schema-invalid LLM output | Một repair attempt bằng schema; sau đó fallback |
| Tool denied | Không retry bằng tool khác; audit security event |
| Retrieval empty | `grounded=false`; Agent trả unknown/assistance hoặc stop |
| Conflicting source | Không tự chọn nếu authority/effective date không giải quyết; pending review |
| Collaboration loop lặp | Dedup + convergence hash; dừng tối đa round 3 |
| Agent output stale sau context update | Impact graph invalidates finding và downstream synthesis |
| Coordinator crash | Session/task/finding persisted; replay idempotent theo task input hash |

## 20. Evaluation plan

### 20.1. Dataset tối thiểu

Thêm ít nhất 40 collaboration cases:

- 10 Product discovery/alternative cases.
- 10 Legal constraint/hard-block/missing-info cases.
- 8 Operations dependency/dedup cases.
- 6 conflict/stale/evidence cases.
- 6 permission/injection/loop/adversarial cases.

### 20.2. Chỉ số

| Nhóm | Metric | MVP gate |
|---|---|---:|
| Contract | ExpertFinding/message/schema validity | 100% |
| Grounding | Important claim evidence coverage | 100% |
| Safety | Hard-block override | 0% |
| Permission | Unauthorized cross-agent tool call succeeds | 0 |
| Collaboration | Correct assistance routing | ≥ 95% |
| Collaboration | Converges within 3 rounds | ≥ 95% |
| Synthesis | Blocked candidate preserved with reason | 100% |
| Synthesis | Duplicate checklist/task | 0% |
| Metadata | Required metadata completeness | 100% |
| Privacy | Raw PII/secret/CoT in logs | 0 |
| Reliability | Deterministic fallback task success | ≥ 95% synthetic set |

### 20.3. Acceptance scenarios

- **AC-A01:** Working Capital bị hard block do bad debt → trạng thái `pending_review`; Product đưa alternative phi tín dụng; credit candidate vẫn hiển thị trong blocked list.
- **AC-A02:** Thiếu BCTC → Legal trả `pending_information`; Operations tạo đúng missing checklist; Product không tự bỏ credit nếu RM vẫn muốn theo đuổi.
- **AC-A03:** Product cố gọi `legal_search` → server deny, audit event có policy version, workflow không leak data.
- **AC-A04:** Legal source cũ/mới mâu thuẫn → current effective authoritative source thắng hoặc pending review nếu không phân giải được.
- **AC-A05:** LLM provider down → cùng case vẫn chạy deterministic fallback và không đổi hard-rule outcome.
- **AC-A06:** Collaboration lặp cùng request → dedup, dừng và không tạo thêm task/finding.
- **AC-A07:** Claim bị sửa sau retrieval → content hash mismatch, Evidence Validator đánh `contradicted/stale`, không đưa vào customer draft.
- **AC-A08:** Log scan → không có raw prompt, PII, token hoặc CoT.

## 21. Kế hoạch triển khai

| ID | Giai đoạn | Dependency | Kết quả |
|---|---|---|---|
| V2-018 | Contract & migration design | V2-001,009 | Agent collaboration/metadata schemas, SharedCaseState 2.1 migration |
| V2-019 | Governed corpus & metadata | V2-006,008,018 | Corpus manifest, valid Source Cards, quality report, metadata-rich chunks |
| V2-020 | Agent manifests & ports | V2-018 | Immutable manifests, provider-neutral Agent port, fallback contract |
| V2-021 | Expert Agent refactor | V2-019,020 | Product/Legal/Ops findings; remove CoT prompts and direct state mutation |
| V2-022 | Tool/MCP isolation | V2-018,020 | Profile endpoints, tokens/scopes, exact allowlist, negative tests |
| V2-023 | Coordinator collaboration | V2-021,022 | Typed message bus, assistance, revision, dedup, convergence |
| V2-024 | Evidence & synthesis | V2-019,023 | Citation validation, conflict policy, primary/alternative/blocked synthesis |
| V2-025 | UI/log/evaluation hardening | V2-024 | Why-this panel, trace, 40 cases, security/reliability regression |

Không bật mặc định Agentic mode trước khi V2-018–V2-024 qua contract/security/eval gates. Giữ workflow deterministic hiện tại làm fallback và A/B baseline.

## 22. Definition of Done

Chỉ đánh dấu hoàn thành khi:

- Machine-readable contracts và Pydantic models khớp 100%.
- Không còn prompt/output yêu cầu CoT.
- Expert không mutate SharedCaseState và không gọi trực tiếp Agent khác.
- Mỗi profile chỉ discover tool của mình; wrong-profile/token/tool đều bị deny.
- Hard-rule output giống baseline deterministic trên toàn bộ golden set.
- Metadata source/document/chunk/retrieval/claim đạt completeness gate.
- Collaboration replay/resume/idempotency/max-loop tests pass.
- AI/Audit/Agent logs đã scan PII/secret/CoT.
- Full regression không làm hỏng V2 deterministic flow.
- `PROGRESS.md`, build log, run report và known limitations được cập nhật bằng kết quả test thật.

## 23. Rủi ro còn lại

- Dữ liệu hiện tại vẫn synthetic; metadata tốt không biến dữ liệu demo thành authoritative policy.
- LLM reasoning quality chưa được chứng minh trên case thật đã de-identify.
- Multi-agent tăng latency/cost và failure surface; cần đo lợi ích so với workflow baseline.
- Per-agent MCP token trong local sandbox chưa thay thế OAuth 2.1/mTLS/workload identity.
- Agent collaboration có thể tạo wording thuyết phục quá mức; Evidence Validator và UI disclaimer là bắt buộc.
- Fine-grained policy owner, SoD và model risk governance cần sign-off trước pilot.
