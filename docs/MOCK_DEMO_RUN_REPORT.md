# Mock Demo Run Report

## Thông tin lần chạy

| Trường | Kết quả |
|---|---|
| Thời điểm | `2026-07-17` |
| Data mode | `SYNTHETIC_DEMO_DATA` |
| UI/API | `http://127.0.0.1:8000` |
| Health | `ok` |
| SQLite quick check | `ok` |
| Schema version | `2/2` |
| Product chunks | `6` |
| Legal chunks | `9` |

## Hành trình browser E2E đã thực thi

| Bước | Kết quả |
|---|---|
| Persona | `RM-999`, `SESS-MP`, `COMP-MP` |
| Case mẫu | Payroll + Cash Management đủ điều kiện synthetic |
| Case ID | `CASE-ADAACD9BEC36` |
| Intake | Tạo case, nạp mock files, process thành công |
| Profile extraction | `11` field, `6` nhóm, `0` conflict chưa xử lý |
| RM confirmation | Snapshot revision `2`, hash `sha256:5653...2338a` |
| Intent | `find_product`, confidence `92%` |
| Product | `PROD-CASH-MGMT`, `PROD-PAYROLL` |
| Eligibility | `passed` |
| Trạng thái trước approval | `pending_approval` |
| Payload hash | `sha256:605a91b156667b4800ebcb50d1e73916490914beac52b952fd4d157c369c1f42` |
| Mock opportunity | `MOCK-OPP-C85D1908E4` |
| Mock task | `MOCK-TASK-C85D1908E4` |
| Trạng thái cuối | `completed` |
| Audit hash-chain | Hợp lệ |
| Browser console error/warning | `0` |

Không có external CRM/email action. Các mã trên được mock executor sinh và lưu local.

## AI Decision Log của case QA

| Chỉ số | Kết quả |
|---|---:|
| Entry | `7` |
| Module | RequirementExtractor, Planner, ProductRAG, EligibilityEngine, EvidenceValidator, OperationsComposer |
| Tổng latency | `10 ms` |
| Token | `0` — deterministic mode |
| Estimated cost | `0` |
| Raw PII logged | `false` |

Product RAG log giữ Product ID, match score, source document/version/location và retrieval score. Eligibility log giữ rule ID/version/status và nguồn chính sách. Không lưu prompt thô, raw PII, secret hoặc approval token.

## Regression và evaluation

- Full suite mới nhất sau RAG MCP: `172 passed`, `1` warning dependency không chặn.
- Business golden evaluation: `40/40`, unsafe approval rate `0%`.
- Security evaluation: `25/25`.
- Reliability evaluation: `20/20`.
- JavaScript syntax: `node --check app/static/app.js` thành công.
- Browser happy path hoàn tất từ intake đến mock execution; không có console error/warning.

## Trạng thái server bàn giao

Server mock chính trên cổng `8000` được giữ chạy để người dùng thao tác. Nếu cần khởi động lại, chạy `run_mock_demo.cmd` từ root repo.
