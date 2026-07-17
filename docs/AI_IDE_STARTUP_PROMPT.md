# Prompt khởi động AI IDE trước khi xây dựng project

Dùng prompt này khi mở một project bằng Claude Code, Codex, Antigravity hoặc AI coding IDE khác. Mục tiêu là buộc AI đọc và nắm các file chiến lược/kỹ thuật trước khi bắt đầu thiết kế hoặc code.

> **Lưu ý cho repo `hakathon` này cụ thể:** `AGENTS.md` và `CLAUDE.md` vẫn nằm ở thư mục gốc (bắt buộc, để Claude Code tự động load). File này và `AI_Agent_RAG_Study_Guide.md`, `VAIC_README_AI_LOG_PROMPT.md` đã được chuyển vào `docs/`. Trạng thái build hiện tại nằm ở `plan/BUILD_STATUS.md` và `plan/PROGRESS.md`, không phải trong file này. Danh sách file bên dưới là template dùng chung cho mọi project — khi áp dụng ở repo khác, đặt lại các file đó cùng thư mục theo đúng hướng dẫn gốc.

## Prompt

```text
Trước khi bắt đầu xây dựng, hãy đọc đầy đủ các file sau trong project:

- AGENTS.md
- CLAUDE.md nếu có
- AI_Agent_RAG_Study_Guide.md
- IDE_CONTEXT_SETUP.md nếu có

Sau khi đọc xong, chưa được code ngay.

Hãy làm 4 việc trước:

1. Xác nhận bạn đã đọc được từng file hay chưa.
Trả lời theo bảng:
File | Đã đọc được? | Vai trò của file | Nội dung quan trọng bạn sẽ áp dụng

2. Trích xuất các kỹ thuật chính mà bạn sẽ dùng trong quá trình xây dựng.
Trả lời theo bảng:
Nhóm kỹ thuật | Khi nào áp dụng | Dấu hiệu cần dùng | Không nên dùng khi nào | Artifact liên quan

Các nhóm kỹ thuật bắt buộc phải kiểm tra:
- Problem framing
- Prompt engineering
- Structured output
- RAG
- Tool calling / MCP
- Workflow orchestration
- Agent
- Multi-agent
- Guardrails / AI Safety
- Human-in-the-loop
- Evaluation / Benchmarking
- Observability / Logging / Tracing
- Reliability / Fallback / Cache / Circuit breaker
- Data pipeline / Data observability
- Fine-tuning / Alignment
- Reporting / Output contract

3. Với mọi bài toán tôi đưa sau đó, bạn phải làm bước:
Bài toán thực tế -> Kỹ thuật phù hợp -> Artifact cần tạo -> Cách kiểm chứng
trước khi viết code.

4. Chỉ sau khi hoàn thành 3 bước trên, hãy hỏi tôi:
“Bây giờ bạn muốn áp dụng bộ kỹ thuật này cho bài toán nào?”
```

## Cách dùng

1. Đặt file này cùng thư mục với:
   - `AGENTS.md`
   - `CLAUDE.md`
   - `AI_Agent_RAG_Study_Guide.md`
   - `IDE_CONTEXT_SETUP.md`
2. Mở project bằng AI IDE.
3. Copy toàn bộ prompt trong khối `text` ở trên.
4. Dán vào AI IDE trước khi yêu cầu xây dựng bất kỳ bài toán nào.

## Prompt tiếp theo sau khi AI đã xác nhận hiểu

```text
Bây giờ áp dụng bộ kỹ thuật vừa đọc cho bài toán sau:

[Mô tả bài toán thực tế của tôi]

Trước khi code, hãy lập bảng:
Nhu cầu thực tế | Kỹ thuật áp dụng | Vì sao chọn | Artifact cần tạo | Cách kiểm chứng

Không mặc định dùng RAG hoặc agent. Hãy chứng minh vì sao cần hoặc không cần từng kỹ thuật.
```
