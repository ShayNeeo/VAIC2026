param(
  [int]$Port = 8100
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
  throw "Không tìm thấy .venv. Hãy cài requirements.txt trước."
}

$env:RAG_MCP_PORT = "$Port"
$env:RAG_MCP_URL = "http://127.0.0.1:$Port/mcp"
if (-not $env:RAG_MCP_SERVICE_TOKEN) {
  $env:RAG_MCP_SERVICE_TOKEN = "local-rag-mcp-change-me"
}

Push-Location $root
try {
  & $python -m services.rag_mcp.cli seed
  & $python -m services.rag_mcp.server
} finally {
  Pop-Location
}
