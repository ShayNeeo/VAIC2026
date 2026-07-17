# Kế hoạch — Product Agent MCP Server (Chỗ ngồi / SHB Corporate Expert Workspace)

> **Vai trò của bạn:** Product Agent owner. Bạn build **MCP server** cho Product Agent.
> **Workspace:** "Chỗ ngồi" — hệ thống multi-agent nội bộ giúp RM xử lý yêu cầu KH doanh nghiệp bằng cách điều phối Product / Legal / Operations.
> **Luồng cốt lõi của module này:** `RAG → Guardrails → verify`.
> **Model:** `gemma-4-31b-it` qua endpoint `https://generativelanguage.googleapis.com` (Google AI Studio key).
> **Deploy:** VPS `root@sgp1.w9.nu` port `2204` (IPv6, IPv4 qua NAT SSH).

---

## 1. Mục tiêu hiểu được

Xây MCP server đóng gói **Product Agent** thành tool callable cho orchestrator (Planner) và RM Workspace. Server nhận yêu cầu KH + company profile, chạy pipeline:

1. **RAG** — truy xuất catalog sản phẩm có nguồn, citation rõ ràng (dựa `RAG_VSF` hybrid + `app/rag/product_retriever.py`).
2. **Guardrails** — kiểm tra input (prompt injection, PII), output (claim có evidence, blocking legal), approval state.
3. **verify** — xác thực mọi claim quan trọng có Evidence Item hợp lệ trước khi trả bundle.

Output: `recommended_bundle` + `citations` + `missing_parameters` + guardrail verdict. Module **không** gọi CRM/write tool (vượt quyền → `TOOL_PERMISSION_DENIED`).

## 2. Giả định

- Dữ liệu catalog/legal là **SYNTHETIC DEMO** (như MVP). Sản phẩm thật do Product team sign-off sau.
- `gemma-4-31b-it` dùng để *rerank/generate matching reason* và *verify claim*, không thay thế matcher deterministic cho fee/limit (phải exact match).
- MCP server chạy trên VPS, expose streamable HTTP hoặc stdio qua SSH tunnel từ orchestrator.
- Orchestrator hiện tại là `app/services/orchestrator.py` (FastAPI in-process). MCP server sẽ là **external process** — orchestrator gọi qua MCP client.
- Chưa có persistent vector index thật → MVP giữ hash-embedding fallback, sau đó nâng lên FAISS/sentence-transformers như `RAG_VSF`.

## 3. Bản đồ bài toán → kỹ thuật

| Nhu cầu thực tế | Kỹ thuật áp dụng | Vì sao | Artifact tạo ra |
|---|---|---|---|
| Truy xuất sản phẩm có nguồn | Hybrid RAG (dense+sparse, heuristic rerank, threshold 0.35) theo `RAG_VSF` | Tránh hallucination, citation xác minh | `mcp_server/rag/` |
| Ghép bundle thay vì 1 sản phẩm | Deterministic matcher + LLM rerank reason | Matcher ổn định, LLM giải thích tự nhiên | `mcp_server/product/matcher.py` |
| Chặn injection/PII | Regex + semantic guard (gemma) | Bảo vệ prompt policy | `mcp_server/safety/` |
| Xác thực claim | Evidence validator (exact match fee/limit) | 100% claim quan trọng có evidence | `mcp_server/safety/verify.py` |
| Expose cho orchestrator | MCP server (FastMCP) tool `product_analyze` | Chuẩn, callable từ nhiều client | `mcp_server/server.py` |
| Deploy VPS | systemd service + SSH tunnel IPv6 | Chạy nền, truy cập qua NAT | `deploy/` |

## 4. Kiến trúc đề xuất

```
RM Workspace / Planner (FastAPI orchestrator)
        │  MCP client call
        ▼
Product Agent MCP Server (FastMCP, VPS :2204)
   ├── tool: product_analyze(request, profile, documents)
   │      └─> [1] RAG.retrieve()        → candidates + citations
   │      └─> [2] Guardrails.inspect()  → injection/PII pass?
   │      └─> [3] matcher.score()       → bundle + reasons (gemma rerank)
   │      └─> [4] verify.evidence()     → every claim grounded?
   │      └─> [5] Guardrails.output()   → block if ungrounded/blocking
   │      └─> return ProductResult (schema đồng nhất với SharedCaseState)
   └── tool: product_search(q)  → raw RAG context (debug/RM)
```

Model call: `POST https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent?key=...`
Dùng **chỉ** cho: (a) natural-language matching reason, (b) semantic evidence support score, (c) injection semantic check. Không dùng để sinh fee/limit.

## 5. Luồng xử lý (RAG → Guardrails → verify)

```
input (request_text, profile, documents)
  │
  ▼ [RAG]
  normalize_query → tokenize (underthesea nếu có, else regex VIE)
  → dense(hash/real embed) + sparse(BM25) → fusion 0.6/0.4
  → heuristic rerank (+keyword, +legal article, +table) → cap +0.25
  → threshold 0.35 gate → top_k context + citations
  │
  ▼ [GUARDRAILS - input]
  regex INJECTION_PATTERNS + gemma semantic injection judge
  → mask PII (CMND/account/PIN) trước khi đưa model
  → allowed? else return security_flags, no analysis
  │
  ▼ [MATCH + GENERATE]
  deterministic matcher (như product_agent.py) chọn product_ids
  gemma sinh matching_reason + semantic evidence score
  │
  ▼ [VERIFY]
  với mỗi claim quan trọng:
    - fee/limit → exact deterministic match (source quote) ELSE hallucination_flag
    - semantic claim → support score ≥ threshold ELSE re-retrieve 1 lần → pending_review
  │
  ▼ [GUARDRAILS - output]
  mọi claim có EvidenceItem.is_valid?
  legal_result có blocking? → không đề xuất product-opening
  → return ProductResult hoặc {allowed:false, reason}
```

## 6. Thành phần cần tạo (file mapping)

| File | Loại | Mục đích | Nội dung chính |
|---|---|---|---|
| `mcp_server/server.py` | code | FastMCP entrypoint, tool `product_analyze` + `product_search` | Khởi tạo RAG/Guardrails/Matcher/Verify, expose MCP |
| `mcp_server/rag/retriever.py` | code | Hybrid retrieval (port từ `app/rag/product_retriever.py`) | normalize, dense+sparse, rerank, threshold, citation |
| `mcp_server/rag/embedder.py` | code | Embedding: hash fallback → sentence-transformers e5 | Prefix `query:/passage:`, cache SQLite |
| `mcp_server/product/matcher.py` | code | Deterministic scoring + bundle logic | Giữ nguyên logic `product_agent.py`, thêm schema |
| `mcp_server/product/llm_reason.py` | code | Gọi gemma-4-31b-it sinh reason + semantic score | HTTP client Gemini endpoint, timeout/retry |
| `mcp_server/safety/input_guardrails.py` | code | Injection regex + PII mask + semantic judge | Port `app/safety/guardrails.py`, thêm gemma judge |
| `mcp_server/safety/verify.py` | code | Evidence validation (exact + semantic) | Port `app/safety/evidence_validator.py` |
| `mcp_server/schemas.py` | code | ProductResult / EvidenceItem Pydantic | Đồng bộ `contracts/shared_case_state.schema.json` |
| `mcp_server/config.py` | code | GOOGLE_API_KEY, model, endpoint, threshold env | Từ `.env` |
| `mcp_server/requirements.txt` | dep | fastmcp, httpx, pydantic, underthesea (opt) | Tối thiểu |
| `deploy/start.sh` + `deploy/product-agent.service` | deploy | systemd chạy server VPS | Bind IPv6 :2204 |
| `tests/test_mcp_product.py` | test | Test tool contract + guardrails + verify | Theo `15_ACCEPTANCE_TRACEABILITY.md` |

## 7. Tiêu chí an toàn (Guardrails)

- **Input:** regex injection patterns (VI/EN) + gemma semantic judge. Tài liệu upload = untrusted data, không được đổi system/tool policy.
- **PII:** mask CMND (`\d{12,19}`), account, PIN trước khi log/model. Log chỉ hash/redacted ID.
- **Tool privilege:** Product Agent **không** gọi `create_crm_case`/`send_email`. Vi phạm → `TOOL_PERMISSION_DENIED` + audit high-severity.
- **Verify:** 100% claim quan trọng có EvidenceItem hợp lệ. Fee/limit exact match. Ungrounded → `hallucination_flag`, không vào customer output.
- **Approval:** Product Agent không tự approve. Chỉ trả draft; RM duyệt qua orchestrator approval service.
- **HITL:** mọi action nghiệp vụ (tạo case/task) do orchestrator + RM, không tại MCP server này.

## 8. Tiêu chí đánh giá

- Payroll query → retrieve PROD-PAYROLL (Hit@5 ≥ 95% golden set).
- Distributed cash flow + revenue → PROD-CASH-MGMT.
- Credit intent → PROD-WORKING-CAPITAL (Legal thẩm định tiếp).
- Old policy version excluded; ACL-blocked chunk never returned.
- Prompt injection trong document → blocked/isolated.
- Unsupported product recommendation = 0.
- Mọi recommendation có valid evidence.
- PII absent từ logs.

Test file `tests/test_mcp_product.py` cover các case trên + concurrency/idempotency token (nếu gọi action — nhưng module này không gọi).

## 9. Tiêu chí vận hành

- **Trace:** mọi tool call có `trace_id`, `case_id`, `actor="Product-MCP"`.
- **Latency:** RAG hash fallback < 200ms; gemma call < 3s với timeout 5s + 1 retry.
- **Fallback:** embedding fail → Blake2b hash; gemma fail → chỉ dùng deterministic reason (không block).
- **Reliability:** MCP server crash → orchestrator trả `product_unavailable`, manual path.
- **Cost:** gemma chỉ gọi cho reason/semantic score, limit tokens (`maxOutputTokens` ~ 256).

## 10. Kế hoạch triển khai (theo order)

1. **Scaffold** `mcp_server/` + `requirements.txt` + `.env.example` (GOOGLE_API_KEY, GOOGLE_MODEL=gemma-4-31b-it, GOOGLE_ENDPOINT).
2. **Port RAG** `retriever.py` từ `app/rag/product_retriever.py` → thêm underthesea tokenize + e5 embedder option.
3. **Port matcher** `matcher.py` từ `product_agent.py` → Pydantic ProductResult.
4. **Guardrails input** từ `app/safety/guardrails.py` + thêm gemma semantic injection judge.
5. **Verify** từ `app/safety/evidence_validator.py` → exact fee/limit + semantic score.
6. **llm_reason.py** — gemma client (httpx, timeout/retry, token limit).
7. **server.py** — FastMCP tool `product_analyze` orchestrate [1]→[5].
8. **schemas.py** đồng bộ `shared_case_state.schema.json`.
9. **tests** theo §8.
10. **deploy** `start.sh` + systemd, bind VPS IPv6 :2204, SSH tunnel từ orchestrator.
11. **Integrate** orchestrator gọi MCP client thay vì in-process ProductAgent (giữ backward compat: fallback in-process nếu MCP down).

## 11. Rủi ro còn lại

- `gemma-4-31b-it` model name/endpoint chưa xác nhận trên Google AI Studio → cần verify key + model availability trước bước 6.
- Chưa có persistent vector index → retrieval quality giới hạn ở hash embedding cho tới khi cài sentence-transformers + FAISS trên VPS.
- underthesea nặng → VPS cần đủ RAM; fallback regex VIE nếu thiếu.
- MCP transport (stdio vs streamable HTTP) chưa chốt — đề xuất streamable HTTP qua SSH tunnel IPv6.
- Dữ liệu thật (catalog/legal) cần Product/Risk sign-off trước pilot — hiện là synthetic.

## 12. Câu hỏi cần bạn confirm

1. MCP transport: **streamable HTTP** (khuyên) hay stdio qua SSH?
2. Gemma key đã active? Model `gemma-4-31b-it` có trên AI Studio chưa?
3. Orchestrator gọi MCP client — giữ in-process fallback không?
4. Vector index thật (FAISS+e5) làm luôn hay để phase 2?
