@echo off
set PORT=%1
if "%PORT%"=="" set PORT=8100
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_rag_mcp.ps1" -Port %PORT%
