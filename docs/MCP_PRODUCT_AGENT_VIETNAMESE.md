# MCP Product Agent - Tài Liệu Kỹ Thuật (Vietnamese)

> **Mục đích**: Hướng dẫn cho AI/LLM sử dụng MCP Product Agent Server - mô tả endpoints, khả năng, và cách tích hợp.

---

## 1. Tổng Quan

**MCP Product Agent** là một MCP Server triển khai theo chuẩn **V3 Data Blueprint** của SHB Corporate Sales Expert Workspace. Server cung cấp pipeline **RAG → Guardrails → Verify** để tìm sản phẩm ngân hàng phù hợp cho khách hàng doanh nghiệp.

- **Transport**: Streamable HTTP (FastMCP)
- **Host**: IPv6 dual-stack (`::`) - chạy trên VPS `sgp1.w9.nu:8004`
- **Protocol**: MCP (Model Context Protocol) - FastMCP implementation
- **Model LLM**: `gemma-4-31b-it` qua Google AI Studio (`https://generativelanguage.googleapis.com`)

---

## 2. Các Tools (Endpoints) MCP

Server expose **3 MCP tools** mà AI client có thể gọi:

### 2.1 `product_analyze` - Pipeline đầy đủ RAG → Guardrails → Match → Verify

**Input**:
```json
{
  "request_text": "string",           // Yêu cầu khách hàng (VD: "chi lương 500 nhân viên, dòng tiền phân tán")
  "company_profile": {                // Hồ sơ doanh nghiệp
    "employees_count": "int",         // Số nhân viên (VD: 500)
    "annual_revenue": "float",        // Doanh thu năm (VNĐ, VD: 100_000_000_000)
    "cash_flow_status": "string",     // Trạng thái dòng tiền (VD: "phân tán")
    "industry": "string"              // Ngành nghề (tùy chọn)
  },
  "documents": [                      // Danh sách hồ sơ upload (tùy chọn)
    {"type": "business_registration", "text": "..."},
    {"type": "financial_statement", "text": "..."}
  ],
  "trace_id": "string",               // Correlation ID (tự sinh nếu không có)
  "context_snapshot": {}              // Context từ workspace (tùy chọn)
}
```

**Output**:
```json
{
  "allowed": true,
  "result": {
    "recommended_bundle": {
      "bundle_name": "Gói giải pháp doanh nghiệp tổng hợp",
      "products": [
        {
          "product_id": "PROD-PAYROLL",
          "name": "SHB Payroll",
          "match_score": {
            "intent_fit": 0.8,
            "segment_fit": 0.9,
            "size_revenue_fit": 0.85,
            "workflow_signal": 0.7,
            "missing_prerequisites": 0.0,
            "legal_blocking": 0.0,
            "total": 0.9
          },
          "matching_reason": "Quy mô 500 nhân sự phù hợp dịch vụ chi lương.",
          "prerequisites": [
            {"document_type": "Giấy đăng ký kinh doanh", "required": true},
            {"document_type": "Danh sách nhân viên", "required": true},
            {"document_type": "Quyết định ủy quyền", "required": true}
          ],
          "retrieval_score": 0.95
        }
      ],
      "bundle_reason": "Dựa trên nhu cầu: SHB Payroll, SHB Cash Management"
    },
    "recommended_products": ["PROD-PAYROLL", "PROD-CASH-MGMT"],
    "missing_parameters": [],
    "retrieval_query": "chi lương 500 nhân viên dòng tiền phân tán",
    "citations": [
      {
        "claim_id": "EVID-PROD-PAYROLL-xxxx",
        "agent": "Product",
        "claim": "SHB Payroll có điều kiện: Doanh nghiệp từ 10 nhân sự...",
        "source_document_id": "Product_Catalog_v3.pdf",
        "source_version": "2026-01-01",
        "section_or_page": "Payroll",
        "quote": "Doanh nghiệp từ 10 nhân sự, có tài khoản SHB...",
        "validation_method": "exact_match",
        "is_valid": true,
        "validation_score": 1.0
      }
    ],
    "guardrail_verdict": {
      "input_allowed": true,
      "input_flags": [],
      "output_allowed": true,
      "output_reason": "ok",
      "evidence_valid": true,
      "evidence_valid_count": 2,
      "evidence_invalid_count": 0
    }
  },
  "trace_id": "abc123"
}
```

**Khi nào dùng**: AI cần phân tích nhu cầu khách hàng → đề xuất bundle sản phẩm có citation.

> **Cập nhật v3-hardening**: Output bổ sung trường `provenance` (F-04) chứa
> `source_document_id`, `source_section`, `source_version`, `owner` và `evidence_ids`
> cho mỗi sản phẩm — đáp ứng blueprint §8.2 / Form F-04 (mọi output có schema_version,
> provenance, validation_status). Product Agent **không** bao giờ tự đặt `eligible`
> (thuộc thẩm quyền Legal Agent).

---

### 2.2 `product_search` - Tìm kiếm RAG thô (debug / RM trực tiếp)

**Input**:
```json
{
  "q": "payroll",
  "top_k": 5
}
```

**Output**:
```json
{
  "query": "payroll",
  "context": "[Source 1] Product_Catalog_v3.pdf — Payroll\nPROD-PAYROLL SHB Payroll...\nScore: 1.0000",
  "sources": [
    {"source_doc": "Product_Catalog_v3.pdf", "page_or_section": "Payroll", "product_id": "PROD-PAYROLL"}
  ],
  "grounded": true
}
```

**Khi nào dùng**: RM muốn tra cứu nhanh catalog, debug retrieval, không cần guardrails/verify.

---

### 2.3 `health_check` - Kiểm tra trạng thái server

**Input**: `{}`

**Output**:
```json
{
  "status": "ok",
  "service": "v3-product-agent",
  "version": "3.0.0",
  "config": {
    "rag_threshold": 0.35,
    "rag_top_k": 5,
    "dense_weight": 0.6,
    "sparse_weight": 0.4,
    "use_real_embedding": false,
    "evidence_semantic_threshold": 0.6
  }
}
```

---

## 3. Danh Sách Sản Phẩm (Catalog) - Tier A (Internal Authoritative)

| Product ID | Tên | Phân khúc | Loại | Điều kiện chính |
|------------|-----|-----------|------|----------------|
| `PROD-PAYROLL` | SHB Payroll | Corporate | Payroll | ≥10 nhân sự, tài khoản SHB, đăng ký eBanking |
| `PROD-CASH-MGMT` | SHB Cash Management | Corporate | Cash Management | Doanh thu ≥50 tỷ VNĐ/năm, dòng tiền phân tán |
| `PROD-COLLECTION` | SHB Collection | Corporate | Collection | Cần thu/chi hộ định kỳ, nhiều đối tác, dùng Virtual Account |
| `PROD-WORKING-CAPITAL` | SHB Working Capital | Corporate | Credit | Hoạt động ≥2 năm, BCTC kiểm toán, không nợ xấu, có TSDĐ |

Mỗi sản phẩm có: `fees_limits` (phí/giới hạn có đơn vị), `prerequisites` (hồ sơ bắt buộc), `eligibility_rules` (điều kiện văn bản).

---

## 4. Pipeline Xử Lý (RAG → Guardrails → Verify)

```
request_text + company_profile + documents
         │
         ▼
┌─────────────────────────────────────┐
│ ProductPipeline.run()                │  servers/v3_product_agent/product/pipeline.py
│  (orchestration only; no MCP wire)   │
└─────────────┬───────────────────────┘
              ▼
   [1 INPUT GUARDRAILS] → blocked: {allowed:false, error:"INPUT_BLOCKED"}
              ▼
   [2 RAG RETRIEVAL]  (catalog = single source of truth)
              ▼
   [3 MATCHER]  select_needs (ProductNeed enum) → score → reason → gaps
              ▼
   [4 EVIDENCE VERIFY]  EvidenceItem built once, passed by ref
              │   NUMERIC_EXACT (fee/limit) | SEMANTIC_SUPPORT (qualitative)
              ▼
   [5 OUTPUT GUARDRAILS]  legal_result passed through; default pending_review
              ▼
   ProductResult + provenance(F-04) + guardrail_verdict
```

Thiết kế "Linux-kernel style": mỗi module một trách nhiệm; catalog là nguồn
duy nhất; matcher/verify đọc catalog, không nhân bản facts; Gemma là **reasoner
tùy chọn** — pipeline vẫn valid với 0 cuộc gọi LLM (deterministic by default).

---

```
request_text + company_profile + documents
         │
         ▼
┌─────────────────────────────────────┐
│ 1. INPUT GUARDRAILS                 │
│  - Regex injection (VI/EN)          │
│  - PII mask (CMND, PIN, email, SĐT) │
│  - Gemma semantic injection judge   │
└─────────────┬───────────────────────┘
              │ blocked → return {allowed: false, error: "INPUT_BLOCKED"}
              ▼
┌─────────────────────────────────────┐
│ 2. RAG RETRIEVAL                    │
│  - Normalize query (NFC, lowercase) │
│  - Tokenize (underthesea / regex)   │
│  - Dense (e5/hash) + Sparse (BM25)  │
│  - Fusion 0.6/0.4                   │
│  - Heuristic rerank (+keyword,      │
│    +legal_article, +exact_code)     │
│  - Threshold 0.35                   │
│  - Top-k citations                  │
└─────────────┬───────────────────────┘
              ▼
┌─────────────────────────────────────┐
│ 3. MATCHER (Deterministic + LLM)    │
│  - Rules: payroll (≥100 nhân sự),   │
│    cash_mgmt (doanh thu ≥50B + phân tán), │
│    collection (thu/chi hộ),         │
│    working_capital (thấu chi/vốn)   │
│  - Score components (V3):           │
│    intent_fit, segment_fit,         │
│    size_revenue_fit, workflow_signal│
│  - LLM reason (gemma-4-31b-it)      │
└─────────────┬───────────────────────┘
              ▼
┌─────────────────────────────────────┐
│ 4. EVIDENCE VERIFICATION            │
│  - Fee/limit/rate → exact match     │
│  - Qualitative → semantic score ≥0.6│
│  - Hallucination flag nếu fail      │
└─────────────┬───────────────────────┘
              ▼
┌─────────────────────────────────────┐
│ 5. OUTPUT GUARDRAILS                │
│  - All claims must have valid evidence     │
│  - Fee/limit claims must exact match      │
│  - Legal blocking blocks credit products  │
└─────────────┬───────────────────────┘
              ▼
        ProductResult + Guardrail Verdict
```

---

## 5. Guardrails & Seguridad

### 5.1 Input Guardrails
- **Injection patterns**: `ignore previous instructions`, `bỏ qua chỉ dẫn`, `system prompt`, `call create_case api`, `bypass approval`, `chèn lệnh`
- **PII masking**: CMND/CCCD (12-19 digits), PIN (4-6 digits), email, phone VN
- **Semantic judge**: Gemma-4-31b-it phân loại injection ngữ nghĩa (optional, default OFF)

### 5.2 Output Guardrails
- Tất cả claim quan trọng phải có `EvidenceItem.is_valid = true`
- Claim fee/limit/rate → bắt buộc exact match
- Legal blocking (UBO missing, BCTC missing) → chặn credit product
- Fee/limit hallucination → block output

### 5.3 Tool Privilege
- **Product Agent KHÔNG được gọi**: `create_crm_case`, `send_email`, bất kỳ write tool nào
- Vi phạm → `TOOL_PERMISSION_DENIED` + audit high-severity
- Chỉ Orchestrator + Approval Agent mới được execute external action

---

## 6. Citation & Evidence Format

Mọi recommendation đều kèm `citations` array:

```json
{
  "claim_id": "EVID-PROD-PAYROLL-xxxx",
  "agent": "Product",
  "claim": "SHB Payroll có điều kiện: Doanh nghiệp từ 10 nhân sự...",
  "source_document_id": "Product_Catalog_v3.pdf",
  "source_version": "2026-01-01",
  "section_or_page": "Payroll",
  "quote": "Doanh nghiệp từ 10 nhân sự, có tài khoản SHB...",
  "validation_method": "exact_match",
  "is_valid": true,
  "validation_score": 1.0
}
```

- `validation_method`: `exact_match` | `semantic_support` | `numeric_exact` | `hybrid`
- `is_valid`: boolean - đã verify chưa
- `validation_score`: 0.0-1.0 (semantic support score)

---

## 7. Cấu Hình Môi Trường (.env)

```bash
# LLM (Google AI Studio)
GOOGLE_API_KEY=your-google-ai-studio-api-key
GOOGLE_MODEL=gemma-4-31b-it
GOOGLE_ENDPOINT=https://generativelanguage.googleapis.com

# VPS / SSH
VPS_HOST=sgp1.w9.nu
VPS_PORT=2204
VPS_USER=root
VPS_SSH_PORT=2204

# MCP Ports
PRODUCT_AGENT_PORT=8004
LEGAL_AGENT_PORT=8005
OPERATIONS_AGENT_PORT=8006
APPROVAL_AGENT_PORT=8007

# Network
BIND_HOST=::

# Feature Flags (default false = safe offline)
USE_REAL_EMBEDDING=false
USE_GEMMA_FOR_GUARDRAILS=false
USE_GEMMA_FOR_VERIFY=false
USE_GEMMA_FOR_REASON=false
EVIDENCE_SEMANTIC_THRESHOLD=0.6

# Confidence Policy (V3 §6.3)
CONFIDENCE_AUTHENTICATED=1.00
CONFIDENCE_WORKSPACE=1.00
CONFIDENCE_FRESH_CRM=0.98
CONFIDENCE_USER_EXPLICIT=0.95
CONFIDENCE_WORKFLOW_STATE=0.95
CONFIDENCE_LLM_INFERENCE=0.70
```

---

## 8. Deploy & Vận Hành

### 8.1 Systemd Service
```ini
[Unit]
Description=SHB Product Agent MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/shb-workspace
Environment=PATH=/opt/shb-workspace/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
EnvironmentFile=-/opt/shb-workspace/.env
ExecStart=/opt/shb-workspace/.venv/bin/python -m servers.v3_product_agent.server
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 8.2 SSH Tunnel (IPv4 NAT → IPv6 VPS)
```bash
# Trên máy local/orchestrator
ssh -L 8004:[::1]:8004 -p 2204 root@sgp1.w9.nu
# MCP client connect đến http://localhost:8004
```

### 8.3 Deploy Script
```bash
./deploy/deploy_product_agent.sh
# - Rsync code + mcp_common
# - Scp .env
# - Install deps, pip install -e mcp_common
# - systemctl restart shb-product-agent
```

---

## 9. Khả Năng Của AI Khi Sử Dụng MCP Này

| Khả năng | Tool | Mô tả |
|----------|------|-------|
| **Phân tích nhu cầu KH** | `product_analyze` | Nhận request_text + profile → trả bundle sản phẩm + citation |
| **Tra cứu catalog** | `product_search` | Tra cứu nhanh thông tin sản phẩm/fee/điều kiện |
| **Kiểm tra guardrails** | Tự động trong `product_analyze` | Chặn injection, PII, hallucination, fee giả |
| **Verify evidence** | Tự động | Exact match fee/limit, semantic support qualitative |
| **Traceability** | `trace_id` | Mọi request có trace_id để audit end-to-end |

**Lưu ý quan trọng**:
- AI **KHÔNG** được tự approve credit - Legal Agent + RM approve
- AI **KHÔNG** gọi CRM/email trực tiếp - chỉ trả recommendation
- Mọi fee/limit phải có exact citation từ catalog
- Legal blocking (thiếu UBO/BCTC) → credit product bị chặn, non-credit vẫn tiếp tục

---

## 10. Kiến Trúc Tổng Thể (MCP Mesh)

```
                    ┌─────────────────────┐
                    │  Orchestrator       │
                    │  (FastAPI + MCP     │
                    │   Client Hub)       │
                    └──────────┬──────────┘
                               │ MCP (Streamable HTTP)
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  Product Agent   │ │   Legal Agent    │ │ Operations Agent │
│  (v3-product)    │ │   (stub)         │ │   (stub)         │
│  Port 8004       │ │  Port 8005       │ │  Port 8006       │
└──────────────────┘ └──────────────────┘ └──────────────────┘
         ▲                     ▲                     ▲
         └─────────────────────┼─────────────────────┘
                               ▼
                    ┌──────────────────┐
                    │  Approval Agent  │
                    │  (HMAC token)    │
                    │  Port 8007       │
                    └──────────────────┘
```

---

## 11. File Quan Trọng

| File | Mục đích |
|------|----------|
| `servers/v3_product_agent/server.py` | FastMCP entrypoint, 3 tools |
| `servers/v3_product_agent/rag/retriever.py` | Hybrid RAG retriever |
| `servers/v3_product_agent/product/matcher.py` | Deterministic matcher + LLM reason |
| `servers/v3_product_agent/safety/guardrails.py` | Input/Output guardrails |
| `servers/v3_product_agent/safety/verify.py` | Evidence verification |
| `servers/v3_product_agent/product/catalog.py` | `ProductNeed` enum, `NEED_KEYWORDS`, `COMPATIBILITY_GRAPH`, 4 Tier-A products, lookups |
| `servers/v3_product_agent/product/matcher.py` | `select_needs` / `score` / `reason` / `detect_missing_parameters` (enum-driven) |
| `servers/v3_product_agent/product/pipeline.py` | `ProductPipeline.run()` — orchestration duy nhất |
| `servers/v3_product_agent/safety/verify.py` | `NUMERIC_EXACT` + `SEMANTIC_SUPPORT` evidence verify |
| `servers/v3_product_agent/rag/retriever.py` | Hybrid RAG; `RAG_SPARSE_GATE`, `EMBEDDING_CACHE_PATH` configurable |
| `mcp_common/schemas.py` | V3 Pydantic contracts (`ProductResult.provenance`) |
| `mcp_common/config.py` | Settings, feature flags, `RAG_SPARSE_GATE` |
| `mcp_common/llm_client.py` | Gemma client (timeout/retry/fallback) |
| `tests/product_agent/` + `tests/v3_product_agent/` | 157 tests toàn bộ (62 product) |

---

## 12. Checklist Trước Khi Dùng Production

- [ ] `GOOGLE_API_KEY` valid, model `gemma-4-31b-it` accessible
- [ ] SSH key copy lên VPS, port 2204 mở
- [ ] `.env` trên VPS với `GOOGLE_API_KEY`, `APPROVAL_SECRET` random
- [ ] Systemd service enabled + started
- [ ] Health check: `curl http://[::1]:8004/health` → `{"status":"ok"}`
- [ ] MCP client connect được qua SSH tunnel
- [ ] Test `product_analyze` với case ABC → trả Payroll + Cash Mgmt
- [ ] Test injection document → blocked
- [ ] Test fee hallucination → blocked by output guardrails

---

*Tài liệu này đồng bộ với code tại với V3 Data Blueprint (SHB Corporate Sales Expert Workspace MVP Data Blueprint V3). Cập nhật khi schema/endpoint thay đổi.*