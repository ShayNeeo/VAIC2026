"""FastAPI application for the SHB Corporate Expert Workspace MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.v2.router import router as v2_router

app = FastAPI(
    title="SHB Corporate Expert Workspace",
    version="2.0.0",
    description="Context-aware controlled workflow MVP using SYNTHETIC DEMO DATA.",
)
app.include_router(v2_router)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "data_mode": "SHB_ENTERPRISE_DATA"}

@app.get("/", response_class=HTMLResponse)
def workspace() -> str:
    path = Path(__file__).parent / "static" / "index.html"
    return path.read_text(encoding="utf-8")
