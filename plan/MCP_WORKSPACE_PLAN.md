# Kế hoạch MCP — Toàn bộ Workspace "Chỗ ngồi" (SHB Corporate Expert Workspace)

> **Phạm vi:** Thiết kế MCP layer cho **toàn bộ** hệ thống multi-agent. Nhưng **backend code bạn viết = Product Agent MCP server** (các agent khác để team khác/POC sau).
> **Mục tiêu:** Mỗi agent = 1 MCP server độc lập. Orchestrator (Planner) = MCP client điều phối. Chuẩn hóa contract qua `SharedCaseState`.

---

## 1. Mục tiêu hiểu được

Biến kiến trúc in-process FastAPI hiện tại (`app/services/orchestrator.py` gọi `ProductAgent`/`LegalAgent`/`OperationsAgent` trực tiếp) thành **mesh của MCP server**. Lợi ích:
- Mỗi agent deploy/scale/restart độc lập (VPS khác nhau hoặc process riêng).
- Chuẩn tool-call, trace, auth qua MCP protocol.
- Oracle/team khác implement Legal/Ops server mà không động vào code bạn.

**Bạn làm:** `product-agent-mcp` (backend đầy đủ) + **design contract** cho toàn bộ mesh剩余 server (legal/ops/planner/approval) để team khác fill.

## 2. Giả định

- MCP transport = **Streamable HTTP** (khuyên) qua SSH tunnel IPv6 từ orchestrator → mỗi agent server.
- Orchestrator giữ nguyên FastAPI + `CaseOrchestrator`, nhưng thay in-process call bằng **MCP client** (giữ in-process fallback nếu MCP down).
- Mọi agent server shared `contracts/shared_case_state.schema.json` làm ngôn ngữ chung.
- Model `gemma-4-31b-it` (Google endpoint) dùng chung qua 1 util `llm_client` (mỗi server import).
- Dữ liệu synthetic demo (như MVP).

## 3. Bản đồ bài toán → kỹ thuật

| Nhu cầu | Kỹ thuật | Vì sao | Artifact |
|---|---|---|---|
| Tách agent thành service | FastMCP server per agent | Độc lập deploy, chuẩn tool-call | `servers/*/server.py` |
| Orchestrator gọi agent | MCP client (FastMCP Client / streamablehttp) | Protocol chuẩn, trace native | `app/services/mcp_clients.py` |
| Contract chung | Pydantic schema đồng bộ JSON contract | Không lệch state giữa server | `mcp_common/schemas.py` |
| Auth/VPS | SSH tunnel IPv6 + header token | Bảo mật, NAT IPv4 | `deploy/` |
| RM duyệt | Approval service độc lập (MCP hoặc in-process) | Separation of duties | `servers/approval/` |

## 4. Kiến trúc MCP Mesh

```
                         ┌─────────────────────────────┐
   RM Workspace (FastAPI)│  CaseOrchestrator           │
        │                │  - MCP client hub           │
        │                │  - complexity router        │
        │                │  - shared_case_state store  │
        └────────────────┤  - approval gate           │
                         └────────────┬────────────────┘
                                      │ MCP (streamable HTTP, SSH tunnel)
            ┌─────────────┬───────────┴───────────┬──────────────┐
            ▼             ▼                       ▼              ▼
   ┌──────────────┐ ┌──────────────┐    ┌──────────────┐ ┌──────────────┐
   │ product-agent│ │  legal-agent │    │ operations-  │ │  approval-   │
   │   MCP (BẠN)  │ │   MCP (POC)  │    │   agent MCP  │ │   agent MCP  │
   │ RAG→Guard→   │ │ KYC/UBO/     │    │ checklist/   │ │ HMAC token/  │
   │  verify      │ │ eligibility  │    │ draft/task   │ │ executor     │
   └──────────────┘ └──────────────┘    └──────────────┘ └──────────────┘
        VPS :2204         (team khác)        (team khác)      (shared/you)
```

**Luồng 1 case:**
```
RM tạo case → Orchestrator
  → router: simple → product-agent MCP (RAG→Guard→verify)
            complex → planner MCP → fan-out product/legal/ops MCP song song
  → mỗi agent trả result + evidences vào SharedCaseState (section riêng)
  → approval-agent MCP issue token → RM approve → executor (mock CRM)
```

## 5. Contract chuẩn (mọi MCP tool trả về)

Tất cả tool tuân thủ `SharedCaseState` mutation rules (plan_v2 §03):
- Product server chỉ viết `product_result` + `evidences` (agent="Product").
- Legal server chỉ viết `legal_result` + `evidences` (agent="Legal").
- Operations server chỉ viết `operations_result`.
- Tool error chuẩn: `{error_code, message, retryable, safe_to_retry, correlation_id}`.
- Mọi response có `schema_version`, `trace_id`.

### Tool surface proposal (toàn mesh)

| Server | Tool | Input | Output |
|---|---|---|---|
| product-agent | `product_analyze` | `{request, company_profile, documents}` | `ProductResult + citations + guardrail_verdict` |
| product-agent | `product_search` | `{q, top_k}` | raw RAG context (debug) |
| legal-agent | `legal_check` | `{company_profile, product_proposal, documents}` | `EligibilityResult + issues + evidence` |
| legal-agent | `kyc_ubo_screen` | `{company_profile}` | mock watchlist/PEP status |
| operations-agent | `ops_plan` | `{product_result, legal_result, sop}` | `checklist + case/task draft + email draft` |
| approval-agent | `issue_token` | `{case_id, rm_id, permissions, payload_hash}` | `approval_token` |
| approval-agent | `verify_token` | `{token, case_id, rm_id, payload_hash}` | bool + reason |
| planner (orchestrator nội bộ) | `plan` | `{intent, context}` | DAG task list |

**Bạn implement:** `product_analyze` + `product_search` đầy đủ. Các tool còn lại = **contract + stub** (trả `not_implemented` hoặc mock) để team khác fill.

## 6. Thành phần bạn tạo

| File | Loại | Mục đích |
|---|---|---|
| `mcp_common/schemas.py` | code | Pydantic mirror của `shared_case_state.schema.json` + EvidenceItem + ErrorContract. Dùng chung mọi server. |
| `mcp_common/llm_client.py` | code | Wrap `gemma-4-31b-it` Google endpoint (httpx, timeout, retry, token limit). |
| `mcp_common/config.py` | code | Env: GOOGLE_API_KEY, GOOGLE_MODEL, GOOGLE_ENDPOINT, MCP_HOST/PORT. |
| `servers/product-agent/server.py` | code | **FastMCP server**, tool `product_analyze` + `product_search`. |
| `servers/product-agent/rag/retriever.py` | code | Hybrid RAG port từ `app/rag/product_retriever.py` + underthesea + e5 option. |
| `servers/product-agent/product/matcher.py` | code | Deterministic matcher port từ `app/agents/product_agent.py`. |
| `servers/product-agent/safety/input_guardrails.py` | code | Injection regex + PII mask + gemma semantic judge. |
| `servers/product-agent/safety/verify.py` | code | Evidence exact+semantic validate. |
| `servers/legal-agent/server.py` | stub | Contract + mock response (team khác fill). |
| `servers/operations-agent/server.py` | stub | Contract + mock response. |
| `servers/approval-agent/server.py` | stub/partial | Issue/verify token (dựa `app/services/approval.py`). |
| `app/services/mcp_clients.py` | code | Orchestrator MCP client hub — gọi agent servers, fallback in-process. |
| `deploy/start_*.sh` + `*.service` | deploy | systemd mỗi server, bind IPv6. |
| `tests/test_mcp_*.py` | test | Theo `15_ACCEPTANCE_TRACEABILITY.md`. |

## 7. Tiêu chí an toàn (áp dụng toàn mesh)

- **Input guardrails** (bạn implement đầy đủ, export hàm cho server khác reuse): injection regex VI/EN + gemma semantic judge; PII mask trước model/log.
- **Tool privilege:** Product/Legal/Planner không gọi write tool (CRM/create_case). Violation → `TOOL_PERMISSION_DENIED` + audit high-sev.
- **Verify:** 100% claim quan trọng có EvidenceItem hợp lệ. Fee/limit exact match.
- **Approval:** không agent tự approve. RM duyệt qua approval-agent.
- **HITL:** mọi external action do orchestrator + RM, không tại agent server.
- **PII log:** chỉ hash/redacted. Token không log.

## 8. Đánh giá

- Product: Payroll/CashMgmt/WorkingCapital retrieval đúng (Hit@5 ≥ 95%).
- Injection trong document → blocked.
- Unsupported product = 0. Mọi recommendation có valid evidence.
- Cross-agent: orchestrator gọi product MCP → nhận `ProductResult` đúng schema → merge vào SharedCaseState không lệch field.
- Fallback: product MCP down → orchestrator in-process ProductAgent vẫn chạy.
- PII absent từ logs toàn mesh.

## 9. Vận hành

- Trace: mọi MCP call có `trace_id` lan truyền (MCP protocol header / param).
- Latency: RAG hash < 200ms; gemma < 3s (timeout 5s, 1 retry).
- Reliability: agent server crash → orchestrator `agent_unavailable` → manual/path.
- Cost: gemma chỉ reason/semantic/injection, `maxOutputTokens` ~ 256.
- Deploy: mỗi server 1 systemd unit, bind VPS IPv6 :2204 (product), :2205 (legal), :2206 (ops), :2207 (approval). SSH tunnel IPv4 NAT từ orchestrator.

## 10. Kế hoạch triển khai

1. `mcp_common/` (schemas, llm_client, config) — nền tảng.
2. `servers/product-agent/` — **backend đầy đủ** (RAG→Guard→verify) theo plan trước.
3. `servers/legal-agent/`, `operations-agent/`, `approval-agent/` — **stub + contract** (mock trả schema đúng).
4. `app/services/mcp_clients.py` — orchestrator hub, gọi MCP, fallback in-process.
5. `deploy/` — systemd + tunnel scripts.
6. `tests/` — product đầy đủ + integration orchestrator↔product MCP.
7. (Team khác) fill legal/ops backend theo contract.

## 11. Rủi ro

- `gemma-4-31b-it` cần verify key + availability.
- underthesea nặng trên VPS → fallback regex VIE.
- Persistent vector index (FAISS+e5) phase 2.
- MCP transport chốt streamable HTTP (không stdio vì跨进程/网络).
- Dữ liệu thật cần sign-off trước pilot.

## 12. Cần confirm

1. Transport **streamable HTTP** ok?
2. Gemma key + model name verify?
3. Port range VPS (:2204–2207) ok cho 4 server?
4. In-process fallback giữ không (an toàn deploy)?
5. approval-agent bạn làm luôn hay để team khác?
