# SHB Corporate Expert Workspace — MVP

Controlled multi-agent workspace hỗ trợ RM xử lý nhu cầu khách hàng doanh nghiệp bằng Planner, Product RAG, Legal/KYC, Operations, Evidence Validator và phê duyệt có chữ ký HMAC.

> Toàn bộ công ty, sản phẩm, chính sách và API trong repo là **SYNTHETIC DEMO DATA**. Hệ thống không kết nối Core Banking/CRM thật và không tự phê duyệt tín dụng.

## Kiến trúc

```text
RM Workspace / FastAPI
        ↓
Input Guardrail + Complexity Router
        ├── simple → Product RAG → Evidence Validator
        └── complex → Planner DAG
                       ├── Product Agent + local-first RAG
                       ├── Legal Agent (KYC/UBO/BCTC)
                       └── Evidence Validator → Operations Draft
                                                ↓
                                      RM Approval Token
                                                ↓
                                      Mock CRM Action Executor
```

Product RAG tham khảo kiến trúc `RAG_VSF`: query normalization, hybrid dense/sparse-lite, heuristic reranking, similarity threshold và context có citation. MVP dùng hash embedding deterministic và catalog in-memory để chạy offline.

## Chạy local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

`requirements.txt` là bộ runtime tối thiểu. Chỉ cài `requirements-optional.txt` khi phát triển Chroma/LangGraph/LLM thật.

Mở `http://localhost:8000` để chạy demo hoặc `http://localhost:8000/docs` để dùng Swagger.

## Demo ABC end-to-end

1. Tạo case `COMP-ABC` với yêu cầu Payroll + thấu chi và giấy đăng ký doanh nghiệp.
2. Hệ thống đề xuất Payroll, Cash Management, Working Capital; Legal chặn thiếu UBO/BCTC.
3. Nhấn **Bổ sung UBO + BCTC** trên UI để resume.
4. Case chuyển `pending_approval`.
5. Nhấn **RM Approve**; UI xin token ngắn hạn rồi gọi mock CRM executor.

## Kiểm thử

```powershell
pytest -q
pytest --cov=app --cov-report=term-missing
```

Các test bao phủ Planner DAG/cycle, Product RAG, ABC workflow, resume/approval, prompt injection, evidence hallucination, tool privilege escalation và API lifecycle.

## API chính

| Method | Endpoint | Chức năng |
|---|---|---|
| POST | `/api/v1/cases` | Tạo và phân tích case |
| GET | `/api/v1/cases/{case_id}` | Xem state + trace |
| POST | `/api/v1/cases/{case_id}/resume` | Bổ sung hồ sơ và chạy lại |
| POST | `/api/v1/cases/{case_id}/approval-token` | RM xin token phê duyệt |
| POST | `/api/v1/cases/{case_id}/approve` | Thực thi mock action sau approval |
| POST | `/api/v1/cases/{case_id}/reject` | Từ chối case |
| GET | `/api/v1/search/products?q=...` | Product RAG trực tiếp |

## Giới hạn

- Chưa ingest PDF/OCR; endpoint nhận metadata tài liệu có cấu trúc.
- Chưa có persistent vector index; RAG đang dùng catalog in-memory và hash embedding fallback.
- Legal policy, SOP, CRM và dữ liệu khách hàng đều là synthetic mock.
- In-memory case database mất dữ liệu khi restart.
- Chưa có SSO/RBAC enterprise, immutable audit store, OpenTelemetry/Jaeger hay 40-case golden benchmark.
- Đây là hackathon MVP, chưa đạt tiêu chuẩn production readiness của plan.
