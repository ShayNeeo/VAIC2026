@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv.
  echo Run: python -m venv .venv
  echo Then: .venv\Scripts\python.exe -m pip install -r requirements.txt
  exit /b 1
)

set "DEMO_PORT=%~1"
if "%DEMO_PORT%"=="" set "DEMO_PORT=8000"

set "ENV_FILE=.env.v2.example"
if exist ".env" set "ENV_FILE=.env"

echo Corporate Expert Workspace V2 - SYNTHETIC MOCK DATA
echo UI:      http://127.0.0.1:%DEMO_PORT%
echo OpenAPI: http://127.0.0.1:%DEMO_PORT%/docs
echo Health:  http://127.0.0.1:%DEMO_PORT%/api/v2/health
echo Env:     %ENV_FILE%
echo Press Ctrl+C to stop the server.

".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port %DEMO_PORT% --env-file "%ENV_FILE%"
