# Project Strategy: Applied AI, Agent, RAG and Production Systems

This workspace is a reusable Vietnamese knowledge base for solving real-world AI and software problems. It includes production-grade techniques for problem framing, product strategy, data workflows, AI agents, RAG systems, tool-calling workflows, evaluation suites, guardrails, observability, fine-tuning, alignment, and human-in-the-loop UX.

The goal is not to force every problem into "RAG" or "agent". The goal is to help the assistant reason clearly, choose the right techniques, avoid vague implementation, and produce traceable outputs for practical projects.

## 1. Source Of Truth

- Primary knowledge guide: `docs/AI_Agent_RAG_Study_Guide.md`
- Project strategy and required behavior: `AGENTS.md`
- Claude Code entrypoint: `CLAUDE.md`
- Usage playbook for IDEs: `docs/AI_IDE_STARTUP_PROMPT.md`
- VAIC 2026 README/AI_LOG generation playbook: `docs/VAIC_README_AI_LOG_PROMPT.md`
- Original lecture sources: the PDF files in this workspace
- SHB hackathon problem brief: `docs/SHB_Corporate_Expert_Workspace_Multi_Agent_Proposal.docx`
- Implementation plan, build status and living build log: `plan/` (start at `plan/INDEX.md`)

When the user asks about a practical AI/software problem, product workflow, automation, data-driven assistant, AI agents, RAG, tool calling, MCP, guardrails, evaluation, observability, fine-tuning, alignment, GraphRAG, or HITL, read the relevant parts of `docs/AI_Agent_RAG_Study_Guide.md` before designing or coding.

## 2. Activation Triggers

Use this strategy whenever the task mentions or implies:

- a real-world AI product, business workflow, automation, internal tool, decision-support system, or knowledge workflow
- uncertain model output, private data, external actions, user-facing AI, compliance, reliability, or measurable quality
- "make this production-ready", "make it useful in practice", "avoid vague results", "use company data", or "build an AI feature"
- agent, AI agent, autonomous agent, copilot, assistant workflow
- RAG, retrieval, vector store, embedding, chunking, semantic search
- tool calling, function calling, MCP, A2A, API tools
- multi-agent, supervisor, worker, router, LangGraph
- guardrails, AI safety, prompt injection, PII, jailbreak
- evaluation, benchmark, RAGAS, LLM-as-judge, golden dataset
- monitoring, logging, tracing, observability, SLO, dashboard
- reliability, fallback, cache, timeout, retry, circuit breaker
- memory systems, GraphRAG, knowledge graph
- fine-tuning, LoRA, QLoRA, DPO, ORPO, alignment
- human-in-the-loop, approval workflow, audit trail
- product requirements, technical design, architecture review, system design, AI workflow design

If the user uses broad language such as "build an AI app", "make a chatbot", "automate this workflow", "make it production-ready", "use company documents", or "solve this business problem with AI", treat it as an activation trigger.

## 3. Operating Protocol

For activated tasks, follow this order:

1. Classify the task: product strategy, workflow automation, data pipeline, structured LLM feature, agent, RAG, agent + RAG, evaluation, safety, observability, reliability, fine-tuning, or architecture review.
2. Read the relevant sections of `docs/AI_Agent_RAG_Study_Guide.md`.
3. State the assumptions if the user did not provide domain, data source, user type, risk level, or target environment.
4. Map the problem to techniques before coding. Explain whether the solution needs prompt engineering, structured output, RAG, tools, workflow orchestration, agent behavior, fine-tuning, guardrails, eval, observability, or a non-AI solution.
5. Design before coding. Provide the architecture, data flow/control flow, risk gates, eval plan, and observability plan.
6. Implement only after the design is clear enough for a safe first version.
7. Verify with tests, scripts, sample queries, or manual checks appropriate to the repository.
8. Summarize what was built, what was verified, and what remains risky or unfinished.

Do not jump straight to code for broad applied-AI tasks unless the user explicitly asks for a narrow implementation detail.

## 4. Strategy For Real-World AI Problems

For any practical AI/software problem, first create a problem-to-technique map:

| Question | Required Answer |
| --- | --- |
| User goal | Who needs the outcome and what decision/action improves? |
| Current workflow | What happens today without AI? |
| AI role | Should AI classify, summarize, retrieve, recommend, draft, decide, or execute? |
| Data needed | What data is required, where it lives, who owns it, and how fresh it must be? |
| Output contract | What exact output format, schema, report, or UI state is needed? |
| Risk level | What happens if the AI is wrong, slow, unsafe, or overconfident? |
| Technique choice | Prompt/schema, RAG, tools, workflow, agent, fine-tune, rules, or non-AI? |
| Evaluation | How will quality be measured before and after release? |
| Operations | How will logs, traces, cost, latency, fallback, and alerts work? |

Technique selection defaults:

- Use structured prompting and output schemas for transformation, extraction, classification, and report generation.
- Use RAG when the answer depends on private, changing, or source-grounded knowledge.
- Use tools/API calls when the system must read live state or take external actions.
- Use workflow orchestration when the process has deterministic steps and decision points.
- Use an agent only when the system must choose tools/actions dynamically under constraints.
- Use multi-agent only when specialist roles, parallelism, review, or supervision are genuinely needed.
- Use fine-tuning only for stable style, format, latency, cost, or narrow repeated behavior.
- Use non-AI rules/code when deterministic logic is enough.

The assistant must avoid vague AI architecture. Every proposed technique must be tied to a user need, data source, risk, evaluation criterion, or operational requirement.

## 5. Strategy For AI Agent Tasks

When asked to build or review an AI agent, require these decisions:

- User and job-to-be-done: who uses the agent and what outcome they need.
- Scope: what the agent may do, must not do, and should ask a human to approve.
- Inputs and outputs: input types, output schema, expected format, citations if needed.
- Model role: system prompt, task instructions, constraints, refusal behavior.
- Tools: tool list, schema, validation, permissions, timeout, retry, error handling.
- State and memory: session state, persistent memory, privacy, expiration, deletion.
- Control flow: direct answer, retrieve, call tool, ask clarification, escalate, or stop.
- HITL: approval gates for destructive, financial, external, private, or irreversible actions.
- Safety: input guardrails, output guardrails, prompt-injection handling, PII policy.
- Observability: logs, traces, latency, cost, tool success rate, safety flags.
- Evaluation: golden test cases, regression tests, tool-call correctness, refusal cases.
- Reliability: fallback, cache, circuit breaker, rate limits, provider/tool failures.

Default architecture preference:

1. Structured prompt + schema.
2. Prompt + tools.
3. Prompt + RAG.
4. Workflow orchestration.
5. Single agent with tools.
6. Multi-agent only when the task truly needs specialist roles, parallelism, debate, or supervision.

## 6. Strategy For RAG Tasks

When asked to build or review RAG, require these decisions:

- Data sources: PDFs, docs, database, website, tickets, CRM, code, emails, or APIs.
- Ownership and permissions: who can access which document or chunk.
- Freshness: update frequency, versioning, invalidation, stale-data behavior.
- Parsing: how to preserve headings, tables, lists, code, page numbers, and source links.
- Cleaning: remove boilerplate, duplicates, broken encoding, empty text, unsafe content.
- Chunking: structure-aware chunks, overlap policy, metadata, parent-child references.
- Embeddings: model choice, dimension, batch strategy, re-embedding policy.
- Storage: vector DB, metadata schema, document IDs, version IDs, access filters.
- Retrieval: query rewrite, hybrid search, metadata filter, top-k, threshold, reranking.
- Context packing: context budget, deduplication, source diversity, conflict handling.
- Generation: grounded answer policy, citation policy, uncertainty/refusal policy.
- Evaluation: faithfulness, answer relevancy, context precision, context recall, golden set.
- Monitoring: retrieval empty rate, hit rate, latency, token cost, feedback, drift.

Default RAG answer policy:

- Answer only from retrieved context when the question asks about private or domain-specific knowledge.
- Cite sources when possible.
- If context is missing, stale, contradictory, or permission-blocked, say so and ask a clarifying question.
- Do not hide retrieval uncertainty behind confident language.

## 7. Strategy For Evaluation

Every non-trivial applied-AI, agent, or RAG design should include an evaluation plan.

Minimum evaluation package:

- 20-50 golden questions for a first prototype.
- Easy, medium, hard, out-of-scope, adversarial, and permission-sensitive cases.
- Expected answer or expected behavior for each case.
- Metrics for RAG: faithfulness, answer relevancy, context precision, context recall.
- Metrics for agents: task success, tool-call correctness, unsafe-action prevention, latency, cost.
- Regression tests for prompts, retrieval, tool schemas, and output schemas.
- Human review for high-risk outputs.

Do not claim "production-ready" without evaluation, observability, reliability, and safety coverage.

## 8. Strategy For Guardrails And Safety

Use defense in depth:

- Input validation and topic scope.
- PII detection/redaction where relevant.
- Prompt-injection and jailbreak handling for retrieved or user-provided text.
- Permission filtering before retrieval and before tool execution.
- Tool allowlists and approval gates.
- Output schema validation.
- Safety checks for harmful, private, illegal, or policy-sensitive content.
- Audit logs for important decisions and actions.

Actions that require explicit approval:

- deleting or overwriting data
- sending emails/messages externally
- payments, refunds, orders, account changes
- changing production configuration
- exposing private, regulated, or confidential data
- running broad automation across many records

## 9. Strategy For Observability And Reliability

Minimum observability:

- correlation ID or trace ID
- model name and prompt/template version
- retrieved document IDs and metadata filters
- tool calls, arguments after sanitization, status, latency
- token usage and estimated cost
- safety flags and refusal/escalation events
- user feedback where available

Minimum reliability:

- timeout for every model/tool/network call
- retry only when safe and idempotent
- fallback path when model, retrieval, or tool fails
- cache strategy with TTL and invalidation
- circuit breaker for unstable external dependencies
- clear error messages that do not expose secrets

## 10. Fine-Tuning And Alignment Policy

Prefer this order before fine-tuning:

1. Improve prompt and output schema.
2. Add few-shot examples.
3. Add RAG for changing or private knowledge.
4. Add tools for realtime data or actions.
5. Fine-tune only for stable style, format, narrow behavior, latency, or cost reasons.

Do not use fine-tuning as the primary way to store frequently changing knowledge.

For DPO/ORPO/alignment tasks, require preference data, chosen/rejected examples, safety cases, evaluation, and rollback strategy.

## 11. Deliverable Standards

For any design response, include:

- problem-to-technique mapping
- recommended architecture
- data flow or control flow
- key tradeoffs
- risks and guardrails
- evaluation plan
- observability plan
- first implementation steps

For any implementation response, include:

- requirement-to-artifact mapping
- files changed
- how to configure and run
- how to test
- known limitations

## 12. Output Contract And Reporting

The assistant must produce clear, traceable, Vietnamese reports. Do not end with only "done" or a vague summary.

For planning or architecture tasks, use this structure:

1. Mục tiêu hiểu được: restate the user goal in concrete terms.
2. Giả định: list any assumptions about users, data, tools, environment, risk level, or constraints.
3. Bản đồ bài toán -> kỹ thuật: map the user problem to prompt/schema, RAG, tools, workflow, agent, fine-tune, rules, or non-AI logic.
4. Kiến trúc đề xuất: explain the chosen architecture and why it is the simplest suitable option.
5. Luồng xử lý: describe data flow or control flow step by step.
6. Thành phần cần tạo: list files, services, prompts, tools, schemas, indexes, eval sets, dashboards, or configs.
7. Tiêu chí an toàn: guardrails, permissions, HITL, PII, prompt-injection handling.
8. Tiêu chí đánh giá: test cases, metrics, golden set, expected behavior.
9. Tiêu chí vận hành: logs, traces, metrics, fallback, cache, alerts, cost and latency.
10. Kế hoạch triển khai: concrete next steps in order.
11. Rủi ro còn lại: what is not solved yet and what needs user confirmation.

For implementation tasks, the final report must include:

- Tóm tắt kết quả: what was built or changed.
- Danh sách file tạo/sửa: path, purpose, and key contents.
- Cách hoạt động: how the created pieces work together.
- Cách cấu hình: required environment variables, config files, secrets, model names, database/vector store settings.
- Cách chạy: exact commands or IDE steps when applicable.
- Cách kiểm thử: commands, sample inputs, expected outputs, and verification status.
- Báo cáo chất lượng: what was checked for correctness, safety, reliability, and formatting.
- Hạn chế/rủi ro: what remains incomplete, mocked, unverified, or dependent on external services.

When files are created or modified, include a compact artifact table:

| File | Loại | Mục đích | Nội dung chính | Cách dùng |
| --- | --- | --- | --- | --- |

For applied-AI tasks, include a requirement-to-technique table:

| Nhu cầu thực tế | Kỹ thuật áp dụng | Vì sao chọn | Artifact tạo ra | Cách kiểm chứng |
| --- | --- | --- | --- | --- |

For agent/RAG work, include a production-readiness table:

| Hạng mục | Đã có? | Ghi chú |
| --- | --- | --- |
| Data strategy | Có/Chưa/Một phần | ... |
| Retrieval quality | Có/Chưa/Một phần | ... |
| Guardrails/HITL | Có/Chưa/Một phần | ... |
| Evaluation | Có/Chưa/Một phần | ... |
| Observability | Có/Chưa/Một phần | ... |
| Reliability | Có/Chưa/Một phần | ... |
| Security/privacy | Có/Chưa/Một phần | ... |

If the task creates prompts, tool schemas, eval data, RAG indexes, or agent workflows, explain how each artifact was derived from the knowledge base and what criterion it satisfies.

If something cannot be verified, state it directly. Never imply that untested code, unindexed data, or unevaluated prompts are production-ready.

## 13. What To Avoid

- Do not build demo-only RAG without ingestion checks and eval.
- Do not add multi-agent architecture just because the user says "agent".
- Do not force RAG or agent architecture when a simpler workflow, schema, rules, or normal software solution is enough.
- Do not store secrets, raw PII, or sensitive prompts in logs.
- Do not give broad tool permissions without validation and approval gates.
- Do not rely only on prompt wording for safety.
- Do not claim correctness without evidence.
- Do not ignore cost, latency, permissions, or stale data.
- Do not omit the list of created/modified files after implementation.
- Do not omit run/test instructions when code, configs, prompts, indexes, or data artifacts are created.
- Do not hide assumptions that materially affect the architecture or safety.

## 14. Response Style

- Reply in Vietnamese unless the user asks otherwise.
- Use concise headings and practical checklists for strategy.
- Use concrete examples when explaining abstract concepts.
- Ask only when a missing decision is risky; otherwise make reasonable assumptions and state them.
- When implementing code, keep changes scoped and include a verification path.
- Prefer tables for artifact inventories, production-readiness reports, and requirement-to-output mapping.
