"""FastAPI application for the SHB Corporate Expert Workspace MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v2.router import router as v2_router
from app.api.v2.employee_router import case_action_router
from app.api.v2.employee_router import recommendation_router
from app.api.v2.employee_router import router as employee_router

app = FastAPI(
    title="SHB Corporate Expert Workspace",
    version="2.0.0",
    description="Context-aware controlled workflow MVP using SYNTHETIC DEMO DATA.",
)
app.include_router(v2_router)
app.include_router(employee_router, prefix="/api/v2")
app.include_router(recommendation_router, prefix="/api/v2")
app.include_router(case_action_router, prefix="/api/v2")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.exception_handler(HTTPException)
async def http_exception_response(_request: Request, exc: HTTPException) -> JSONResponse:
    """Keep employee API's documented error envelope at the response root.

    Legacy V2 endpoints still use FastAPI's conventional ``detail`` envelope,
    so only explicitly structured employee errors are unwrapped.
    """
    if isinstance(exc.detail, dict) and set(exc.detail) == {"error"}:
        # Keep both envelopes during the additive API migration: newer
        # clients read ``error`` while existing employee clients read
        # ``detail.error``.
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail["error"], "detail": exc.detail},
            headers=exc.headers,
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "data_mode": "SYNTHETIC_DEMO_DATA"}

@app.get("/", response_class=HTMLResponse)
def workspace() -> str:
    path = Path(__file__).parent / "static" / "index.html"
    return path.read_text(encoding="utf-8")
