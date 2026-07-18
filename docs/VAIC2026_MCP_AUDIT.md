# Audit phần MCP của ShayNeeo/VAIC2026

Phạm vi audit chỉ gồm `servers/*`, `mcp_common/*`, `app/services/mcp_clients.py`, MCP tests và cấu hình deploy. Không đánh giá UI, Agent workflow hoặc các module khác.

## Kết luận

Phần MCP của VAIC2026 **dùng được làm prototype/hackathon**, nhưng **chưa nên dùng nguyên trạng làm RAG MCP server kiểu ngân hàng**.

Điểm tham khảo:

- Prototype/hackathon: **7/10**.
- RAG service có kiểm soát kiểu ngân hàng: **3,5/10**.

## Những phần có thể tái sử dụng về ý tưởng

- Có MCP tools `product_search`, `product_analyze`, `health_check`.
- Có HTTP MCP client hub và fallback khi server lỗi.
- Có query normalization, dense/sparse fusion, sparse gate và heuristic reranking.
- Có citation, trace ID, input guardrail và nguyên tắc Product tool không được gọi CRM write.
- Có cấu hình port riêng và systemd/deploy draft.

## Gap cần cải tiến

| Hạng mục | Bằng chứng trong VAIC2026 | Đánh giá |
|---|---|---|
| MCP SDK | `servers/product_agent/requirements.txt` dùng `fastmcp>=0.1.0` không pin upper bound | Có nguy cơ lệch API/version; chưa dùng SDK `mcp` chính thức ổn định |
| Transport test | `tests/v3_product_agent/test_server_tools.py` gọi thẳng hàm Python | Chưa chứng minh initialize/list_tools/call_tool qua HTTP hoạt động end-to-end |
| RAG ownership | Catalog nằm trong `servers/v3_product_agent/product/catalog.py` | Data và logic Agent còn gắn cùng process |
| Persistence | Retriever dựng document/vector in-memory; SQLite chỉ cache embedding | Restart phải dựng lại; chưa có persistent chunk/index manifest |
| Ingestion | Không có pipeline publish source → parse → chunk → validate → index | Data team chưa thể thay corpus độc lập an toàn |
| Chunk contract | `product_search` trả một `context` string và sources | LLM/client không có `chunk_id`, content hash, score components, effective date đầy đủ |
| ACL | Security test ghi ACL “not applicable in synthetic MVP” | Không thể dùng với phân quyền chi nhánh/tài liệu nội bộ |
| Effective/version filter | Metadata có effective date nhưng retrieval không loại version hết hiệu lực đầy đủ | Có rủi ro trích chính sách cũ |
| Service authentication | MCP URL local không có bearer/OAuth gate | Caller chưa được xác thực ở server boundary |
| Audit | Có trace/log ở một số module | Chưa có persistent retrieval audit đã sanitize |
| Tool boundary | `product_analyze` trộn RAG, matcher, guardrail và Product Agent | Không phải một RAG server dùng chung cho nhiều assistant |

## Quyết định áp dụng trong repo hiện tại

Không copy toàn bộ MCP Product Agent. Chỉ giữ các nguyên tắc tốt: hybrid retrieval, sparse gate, citation, trace và read-only tool boundary.

Server mới cải tiến:

- Dùng official `mcp` Python SDK `1.x`, Streamable HTTP stateless + JSON structured output.
- Tách hoàn toàn dưới `services/rag_mcp/`; không import Agent/Workflow code.
- Persistent SQLite source/chunk/vector/audit index.
- Source Card approval, SHA-256 lineage, active/effective/version filter.
- ACL theo branch + permission trước khi trả chunk.
- Tool `rag_search`, `rag_get_chunk`, `rag_list_sources`, `rag_health`.
- Bearer service authentication nằm ở HTTP boundary, không đưa secret vào tool arguments.
- Audit chỉ lưu caller hash, query hash, filter, latency, result count và error code; không lưu raw query/chunk text.
- Transport E2E test dùng official MCP client.

Không lấy UI, Product Agent, Legal Agent, Operations Agent, Approval Agent hoặc Orchestrator từ VAIC2026 theo đúng phạm vi yêu cầu.
