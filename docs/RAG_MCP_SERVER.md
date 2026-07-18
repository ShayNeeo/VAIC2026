# Governed RAG MCP Server

## 1. Mục tiêu

Đây là server độc lập để Data team sở hữu pipeline RAG, còn Agent/LLM chỉ gọi MCP để lấy các chunk đã được lọc quyền, hiệu lực và phiên bản.

```text
Approved source + Source Card
        ↓
Validate → structure-aware mapping → chunk → embed → persistent index
        ↓
MCP Streamable HTTP
        ↓
Service auth → permission/branch ACL → effective/version filter
        ↓
Hybrid retrieve → sparse gate → context packing → citation
        ↓
LLM/Agent nhận chunk; RAG server không sinh quyết định nghiệp vụ
```

Server chỉ expose read tools. Ingestion là administrative CLI, không để LLM tự ghi/chỉnh kho tri thức.

## 2. Dữ liệu mock hiện có

| Domain | Source | Active chunk | Nội dung |
|---|---|---:|---|
| Product | `SYNTHETIC-PRODUCT-REFERENCE-PACK-V1` | 77 | 8 sản phẩm doanh nghiệp (`PRD-*`): master record, biểu phí/hạn mức theo phân khúc, solution bundle và 6 tài liệu hướng dẫn/biểu phí đầy đủ (mỗi sản phẩm đều có ít nhất 1 tài liệu tham chiếu dạng văn xuôi, không chỉ dữ liệu CSV rời rạc) |
| Legal | `SYNTHETIC-LEGAL-REFERENCE-PACK-V1` | 42 | 23 rule điều kiện theo sản phẩm (`product_policies.csv`) + 3 tài liệu quy trình KYC/UBO, quy chế cho vay vốn lưu động, hướng dẫn bảo lãnh |
| Operations | `SYNTHETIC-OPERATIONS-REFERENCE-PACK-V1` | 59 | SOP workflow, checklist hồ sơ theo sản phẩm, SLA, email template và RACI |

Tổng: 3 source, **178 active chunk** (đã kiểm chứng bằng `services.rag_mcp.cli seed` thật, 2026-07-17 — số cũ "19 chunk" trong tài liệu trước đó đã lỗi thời do dữ liệu nguồn ở `data/raw_csv_json/` và `data/mock_documents/` được mở rộng). 1 sản phẩm (`PRD-WC-001` — hạn mức vốn lưu động) được gán `branches=HN01` để minh hoạ branch ACL thật đang hoạt động; các sản phẩm còn lại dùng `branches=*`. 1 dòng biểu phí cũ đã hết hiệu lực (`PRICE-002-VND-OLD`, effective_to 2025-12-31) được giữ lại có chủ đích để kiểm chứng chunk hết hạn không bao giờ lọt vào context LLM.

**Lưu ý namespace sản phẩm:** corpus này dùng `PRD-*` (vd. `PRD-PY-001`), khác với namespace `PROD-*` (vd. `PROD-PAYROLL`) mà `app/knowledge/`, `app/product/`, `app/eligibility/` (track V2 in-process) đang dùng. Đây là 2 catalog song song, chưa được hợp nhất — cần quyết định trước khi coi rag_mcp là nguồn duy nhất.

## 3. MCP tools

| Tool | Chức năng | Side effect |
|---|---|---|
| `rag_search` | Hybrid search và trả structured chunks + `context_text` cho LLM | Không |
| `rag_get_chunk` | Lấy chính xác một chunk theo ID sau ACL/effective check | Không |
| `rag_list_sources` | Liệt kê source/version/hash/owner đang active | Không |
| `rag_health` | Storage/index/embedding/corpus health | Không |

### Input chính của `rag_search`

```json
{
  "request": {
    "query": "dịch vụ chi lương cho 500 nhân viên",
    "principal": {
      "employee_id": "RM-999",
      "branch": "HN01",
      "roles": ["RM"],
      "permissions": ["knowledge:read"]
    },
    "filters": {
      "domain": "product",
      "product_ids": [],
      "document_ids": [],
      "segments": ["CORPORATE"]
    },
    "top_k": 5,
    "min_score": 0.12,
    "max_context_chars": 8000,
    "trace_id": "TRACE-EXAMPLE-001"
  }
}
```

Output gồm:

- `grounded`: có/không có đủ context.
- `chunks[]`: chunk ID, text, domain, product ID, dense/sparse/final score.
- `citation`: document ID/version/section/source ID/content hash.
- `effective_from/effective_to`.
- `context_text`: các chunk đã đóng gói sẵn để đưa vào LLM.
- `audit_event_id`.
- `safety`: xác nhận ACL/effective filter và không log raw query.

LLM phải trả lời chỉ từ `chunks/context_text`. Nếu `grounded=false`, không được bịa câu trả lời; chuyển manual lookup hoặc hỏi lại.

## 4. Chạy local

Cài dependency:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Khởi động:

```powershell
.\run_rag_mcp.cmd
```

Endpoint:

- MCP: `http://127.0.0.1:8100/mcp`
- Health: `http://127.0.0.1:8100/health`
- Ready: `http://127.0.0.1:8100/ready`

Chạy smoke test từ client chính thức:

```powershell
.\.venv\Scripts\python.exe -m tools.rag_mcp_smoke
```

## 5. Administrative ingestion

Seed/idempotent reindex:

```powershell
.\.venv\Scripts\python.exe -m services.rag_mcp.cli seed
```

Health/index inventory:

```powershell
.\.venv\Scripts\python.exe -m services.rag_mcp.cli health
```

Xem retrieval audit theo trace:

```powershell
.\.venv\Scripts\python.exe -m services.rag_mcp.cli audit --trace-id TRACE-EXAMPLE-001
```

Ingestion không phải MCP tool để tránh LLM tự thay đổi dữ liệu serving. Khi thêm nguồn thật, Data Steward phải thêm Source Card đã phê duyệt và adapter parser/chunker tương ứng.

## 6. Service authentication và ACL

MCP endpoint yêu cầu:

```text
Authorization: Bearer <RAG_MCP_SERVICE_TOKEN>
```

Token này xác thực Orchestrator/service caller. `principal` trong tool request phải được Orchestrator lấy từ SSO/session đã xác thực, không lấy trực tiếp từ text người dùng.

Mỗi request phải có `knowledge:read` hoặc permission domain tương ứng. Chunk được lọc theo branch trước khi trả về. `DataSteward`/`KnowledgeAdmin` có thể đọc cross-branch trong sandbox.

Local bearer token chỉ là sandbox control. Production phải thay bằng OAuth 2.1/mTLS/service identity và token verifier ở gateway/MCP server.

## 7. Audit/AI log

SQLite table `retrieval_audit` ghi:

- event ID, timestamp, trace ID.
- caller ID đã hash.
- tool name và query hash — không lưu raw query.
- domain và metadata filters.
- result count, latency, status/error code.

Không ghi raw prompt, raw PII, chunk text, bearer token hoặc nội dung trả lời LLM.

## 8. Docker

```powershell
docker compose up --build rag-mcp
```

Container dùng volume `rag_mcp_state` cho SQLite và chỉ mount/copy corpus thuộc RAG service.

## 9. Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest tests\rag_mcp -q
```

Test bao phủ persistent corpus, citation, expired data, branch ACL, get-chunk bypass, permission denial, prompt injection, OOS, source governance, bearer auth và initialize/list_tools/call_tool qua Streamable HTTP thật.

## 10. Giới hạn trước production

- Embedding đã chuyển sang OpenAI `text-embedding-3-small` thật (1536 chiều, cache local tại `data/rag_mcp/openai_vector_cache.json`), không còn deterministic hash. Fallback `deterministic_hash` (blake2b, 256 chiều) vẫn còn trong `services/rag_mcp/embedding.py` và có thể bật qua `RAG_MCP_EMBEDDING_PROVIDER=deterministic_hash` nếu chạy hoàn toàn offline không có `OPENAI_API_KEY`. Ngưỡng lọc `RAG_MCP_THRESHOLD` đã hiệu chỉnh lại theo 1536 chiều (hiện `0.35`, xem `services/rag_mcp/config.py`). Chưa benchmark model tiếng Việt chuyên biệt trước pilot.
- SQLite phù hợp local/sandbox; production có thể thay repository bằng pgvector/Milvus/OpenSearch mà giữ nguyên MCP contract.
- Chưa có OCR/parser arbitrary upload trong service này; corpus hiện lấy từ JSON đã quản trị.
- Chưa có OAuth/mTLS/KMS/central SIEM/OpenTelemetry, retention và DR.
- Dữ liệu hoàn toàn synthetic, không phải chính sách SHB thật.
