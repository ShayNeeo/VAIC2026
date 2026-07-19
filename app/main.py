"""FastAPI application for the SHB Corporate Expert Workspace MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.v2.router import router as v2_router
from app.api.v2.auth_router import router as auth_router
from app.api.v2.credit_request_router import router as credit_request_router
from app.api.v2.employee_router import case_action_router
from app.api.v2.employee_router import knowledge_router
from app.api.v2.employee_router import recommendation_router
from app.api.v2.employee_router import router as employee_router

app = FastAPI(
    title="SHB Corporate Expert Workspace",
    version="2.0.0",
    description="Context-aware controlled workflow MVP using SYNTHETIC DEMO DATA.",
)

# Allow the deployed Flutter web frontend (vaic.w9.nu) to call this API.
# Origins are read from CORS_ALLOW_ORIGINS (comma-separated) so preview
# domains can be added without a code change.
import os

_cors_origins = [
    o.strip()
    for o in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "https://vaic.w9.nu,https://vaic-api.w9.nu,https://rm-workspace.pages.dev,https://vaic-frontend.pages.dev",
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(v2_router)
app.include_router(auth_router, prefix="/api/v2")
app.include_router(credit_request_router, prefix="/api/v2")
app.include_router(employee_router, prefix="/api/v2")
app.include_router(recommendation_router, prefix="/api/v2")
app.include_router(case_action_router, prefix="/api/v2")
app.include_router(knowledge_router, prefix="/api/v2")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "data_mode": "SHB_ENTERPRISE_DATA"}

@app.get("/", response_class=HTMLResponse)
def workspace() -> str:
    path = Path(__file__).parent / "static" / "index.html"
    return path.read_text(encoding="utf-8")
