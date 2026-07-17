@AGENTS.md

# Claude Code Strategy

Claude Code should treat `AGENTS.md` as the shared project strategy and `docs/AI_Agent_RAG_Study_Guide.md` as the detailed Vietnamese knowledge base. Build status and per-block handoff notes live in `plan/BUILD_STATUS.md`.

## Required Claude Code Behavior

- For real-world AI/software tasks, workflow automation, AI product features, data-driven assistants, agent, RAG, tool calling, MCP, guardrails, evaluation, observability, reliability, fine-tuning, alignment, or HITL tasks, read the relevant sections of `docs/AI_Agent_RAG_Study_Guide.md` before designing or coding.
- Do not assume every task needs RAG or an agent. First map the real-world problem to the right technique: prompt/schema, RAG, tools, workflow, agent, fine-tune, deterministic code, or non-AI logic.
- Start with architecture, data/control flow, risk analysis, evaluation, observability, and reporting expectations before code when the task is broad.
- Use a checklist-driven plan for production AI work: user goal, data, retrieval if needed, tools if needed, prompts, output contract, safety, eval, observability, reliability, and HITL.
- After creating or modifying anything, produce a Vietnamese report that lists every created/changed file, what each file does, how it was created, how to run it, how to test it, and what remains unverified.
- Use the output/reporting contract in `AGENTS.md`; do not finish with a vague "done".
- Keep durable rules in `AGENTS.md`; keep this file small so Claude Code context is not wasted.
- If the loaded memory/instructions are unclear, ask the user to run `/memory` and confirm this file is active.

## Fast Verification Prompt

Use this prompt inside Claude Code to verify context loading:

```text
Bạn đã load những instruction nào từ CLAUDE.md/AGENTS.md? Nếu tôi đưa một bài toán AI thực tế, bạn sẽ phân tích bài toán, chọn kỹ thuật và báo cáo artifact như thế nào?
```
