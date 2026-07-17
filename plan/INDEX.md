# INDEX — SHB Corporate Expert Workspace, kế hoạch triển khai

Đọc file này **trước tiên** trong mọi phiên build (kể cả phiên AI mới, kể cả sau khi context bị compact). File này ngắn (khoảng 1 trang) và luôn phải đọc trọn vẹn. Sau đó chỉ mở **đúng module đang cần**, không mở toàn bộ `SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md` (1156 dòng / ~34k token — quá lớn để load lặp lại mỗi phiên).

**Là người, không phải AI, và muốn biết nhanh "hệ thống đang có gì, còn thiếu gì, tôi nhận việc nào"?** Đọc [`BUILD_STATUS.md`](BUILD_STATUS.md) thay vì file này — đó là bản tổng quan theo khối chức năng thật trong code, viết cho người mới join team.

## 0. Quy tắc bắt buộc khi build với AI

1. Luôn đọc `INDEX.md` + `PROGRESS.md` trước khi bắt đầu bất kỳ task nào.
2. Chỉ mở thêm module trong `modules/` liên quan trực tiếp đến task đang làm (xem bảng điều hướng bên dưới).
3. Không copy lại toàn bộ `SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md` vào prompt — chỉ dùng nó khi cần đối chiếu diagram/nội dung không có trong bản trích.
4. Schema chuẩn (Shared Case State, Tool I/O) nằm ở **một nơi duy nhất**: `modules/07_tools_and_shared_state.md`. Mọi agent module khác chỉ tham chiếu tới đó, không tự định nghĩa lại field mới — tránh lệch schema giữa các phiên build.
5. Sau khi hoàn thành hoặc thay đổi bất kỳ task nào, **cập nhật `PROGRESS.md` ngay** (không đợi cuối ngày) — đây là cách phiên AI tiếp theo phục hồi ngữ cảnh nhanh mà không cần đọc lại toàn bộ plan.
6. Nếu code đi lệch khỏi plan (vì lý do kỹ thuật hoặc thời gian), ghi lại lệch ở đâu và vì sao trong `PROGRESS.md`, không âm thầm sửa plan gốc.

## 1. Cấu trúc thư mục

```
plan/
├── INDEX.md                                   <- luôn đọc trước (cho AI)
├── BUILD_STATUS.md                            <- đã build gì / cần build gì theo khối (cho người, để nhận việc)
├── PROGRESS.md                                <- trạng thái build hiện tại, cập nhật liên tục (decision/deviation log)
├── SHB_MULTI_AGENT_IMPLEMENTATION_PLAN.md      <- bản đầy đủ 45 mục (archive/tham chiếu, ít khi cần đọc trọn)
└── modules/                                    <- bản trích theo chủ đề, mỗi file < 200 dòng
    ├── 00_context_and_business.md
    ├── 01_architecture.md
    ├── 02_planner_agent.md
    ├── 03_product_agent.md
    ├── 04_legal_agent.md
    ├── 05_operations_agent.md
    ├── 06_evidence_guardrails_approval.md
    ├── 07_tools_and_shared_state.md
    ├── 08_data_and_rag.md
    ├── 09_api_ui_error_observability.md
    ├── 10_evaluation_and_testing.md
    ├── 11_roadmap_and_backlog.md
    ├── 12_risks_assumptions_open_questions.md
    └── 13_acceptance_and_dod.md
```

## 2. Bảng điều hướng: đang làm gì thì đọc file nào

| Đang làm task nào | Đọc module | Không cần đọc |
|---|---|---|
| Hiểu bài toán, pitch, phạm vi | `00_context_and_business.md` | phần agent chi tiết |
| Vẽ/chỉnh workflow tổng, LangGraph graph, security boundary | `01_architecture.md` | data/API detail |
| Code Planner Agent (routing, DAG, retry, escalation) | `02_planner_agent.md` + `07_tools_and_shared_state.md` | Product/Legal/Ops detail |
| Code Product Agent (matching, bundle, RAG catalog) | `03_product_agent.md` + `07_tools_and_shared_state.md` + `08_data_and_rag.md` | Legal/Ops detail |
| Code Legal Agent (KYC/UBO, eligibility) | `04_legal_agent.md` + `07_tools_and_shared_state.md` + `08_data_and_rag.md` | Product/Ops detail |
| Code Operations Agent (checklist, email draft, case/task) | `05_operations_agent.md` + `07_tools_and_shared_state.md` | Product/Legal detail |
| Code Evidence Validator / Guardrail Gate / Approval flow | `06_evidence_guardrails_approval.md` + `07_tools_and_shared_state.md` | roadmap/backlog |
| Định nghĩa/sửa Tool Registry hoặc Shared Case State schema | `07_tools_and_shared_state.md` (nguồn chuẩn duy nhất) | — |
| Chuẩn bị dữ liệu mẫu, chunking, vector store | `08_data_and_rag.md` | agent-specific prompt detail |
| Code API endpoint, UI, error handling, logging | `09_api_ui_error_observability.md` | agent internals |
| Viết eval script, golden dataset, so sánh single vs multi-agent | `10_evaluation_and_testing.md` | roadmap |
| Xem lịch 48h, backlog TSK-XXX, pilot 3 tháng | `11_roadmap_and_backlog.md` | agent detail |
| Tra rủi ro, giả định cần SHB xác nhận, câu hỏi mở | `12_risks_assumptions_open_questions.md` | — |
| Kiểm tra tiêu chí nghiệm thu / Definition of Done trước khi báo "xong" | `13_acceptance_and_dod.md` | — |

## 3. Quy ước nhãn nội dung (giữ nguyên từ plan gốc)

- `[CONFIRMED INPUT]` — thông tin đã xác nhận, không phải suy đoán.
- `[PROPOSED DESIGN]` — thiết kế đề xuất, chưa phải quyết định cuối của SHB.
- `[ASSUMPTION]` — giả định cần xác minh lại, xem `12_risks_assumptions_open_questions.md`.
- `[DATA REQUIRED]` — dữ liệu thật cần SHB cung cấp, hiện đang là placeholder dạng `<SHB_..._REQUIRED>`.
- `SYNTHETIC DEMO DATA` — dữ liệu giả lập, không phải dữ liệu SHB thật.

Không được xoá hoặc đổi nhãn này khi chỉnh sửa module — đây là cơ chế chống hallucination cốt lõi của plan.

## 4. Liên kết với code hiện có

Toàn bộ pipeline (Planner/Product/Legal/Operations/Evidence/Approval/API/UI) đã có code chạy được trong [`app/`](../app/), có test xanh (`pytest -q`). Xem trạng thái từng khối, file tương ứng và việc còn thiếu ở [`BUILD_STATUS.md`](BUILD_STATUS.md) — không lặp lại danh sách ở đây để tránh 2 nơi cùng lưu 1 thông tin rồi lệch nhau. Khi code tiếp, luôn đối chiếu field trong `app/schemas/state.py` với schema chuẩn ở `07_tools_and_shared_state.md` trước khi thêm field mới.

## 5. Tài liệu tham khảo (docs/)

Kiến thức nền, brief gốc và các prompt hỗ trợ nằm ở [`../docs/`](../docs/): `AI_Agent_RAG_Study_Guide.md` (kiến thức RAG/agent/guardrail nền tảng), `SHB_Corporate_Expert_Workspace_Multi_Agent_Proposal.docx` (đề bài gốc trước khi có plan chi tiết), `VAIC_README_AI_LOG_PROMPT.md` (template `AI_LOG.md`/README cho nộp bài — xem `BUILD_STATUS.md` Khối 17), `AI_IDE_STARTUP_PROMPT.md` (prompt khởi động AI IDE, dùng chung nhiều project).
