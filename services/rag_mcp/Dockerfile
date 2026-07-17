FROM python:3.12-slim

WORKDIR /srv/rag-mcp
COPY services/rag_mcp/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services ./services
COPY data/catalog ./data/catalog
COPY data/synthetic/v2 ./data/synthetic/v2

ENV PYTHONUNBUFFERED=1 \
    RAG_MCP_HOST=0.0.0.0 \
    RAG_MCP_PORT=8100 \
    RAG_MCP_DB_PATH=/srv/rag-mcp/state/rag.sqlite3

EXPOSE 8100
CMD ["python", "-m", "services.rag_mcp.server"]
