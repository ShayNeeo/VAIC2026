param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Missing .venv. Run: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}

$EnvFile = if (Test-Path -LiteralPath (Join-Path $Root ".env")) { ".env" } else { ".env.v2.example" }

Write-Host "Corporate Expert Workspace V2 - SYNTHETIC MOCK DATA"
Write-Host "UI:      http://127.0.0.1:$Port"
Write-Host "OpenAPI: http://127.0.0.1:$Port/docs"
Write-Host "Health:  http://127.0.0.1:$Port/api/v2/health"
Write-Host "Env:     $EnvFile"
Write-Host "Press Ctrl+C to stop the server."

& $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port --env-file $EnvFile
