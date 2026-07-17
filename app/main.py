"""FastAPI application for the SHB Corporate Expert Workspace MVP."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, Header, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from app.database import db
from app.config import settings
from app.rag import ProductRAGService
from app.schemas.state import ApproveCaseRequest, CreateCaseRequest, RejectCaseRequest, ResumeCaseRequest, SharedCaseState
from app.services.approval import ActionExecutor, ApprovalService, ApprovalTokenError
from app.services.mock_services import CoreBankingService
from app.services.orchestrator import CaseOrchestrator


app = FastAPI(
    title="SHB Corporate Expert Workspace",
    version="0.1.0",
    description="Controlled multi-agent MVP using SYNTHETIC DEMO DATA.",
)
orchestrator = CaseOrchestrator()
product_rag = ProductRAGService()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "data_mode": "SYNTHETIC_DEMO_DATA"}


@app.get("/", response_class=HTMLResponse)
def workspace() -> str:
    path = Path(__file__).parent / "static" / "index.html"
    return path.read_text(encoding="utf-8")


@app.post("/api/v1/cases", status_code=status.HTTP_201_CREATED)
def create_case(payload: CreateCaseRequest) -> Dict[str, Any]:
    profile = CoreBankingService.get_company_profile(payload.customer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng synthetic demo")
    case_id = f"CORP-{uuid.uuid4().hex[:8].upper()}"
    state = SharedCaseState(
        case_id=case_id,
        customer_id=payload.customer_id,
        rm_id=payload.rm_id,
        customer_request={"text": payload.request_text},
        company_profile=profile,
        documents=payload.documents,
    )
    state = orchestrator.run(state)
    db.save_case(state)
    return state.model_dump()


@app.get("/api/v1/cases")
def list_cases(rm_id: str | None = Query(default=None)) -> List[Dict[str, Any]]:
    cases = db.list_cases().values()
    if rm_id:
        cases = [case for case in cases if case.rm_id == rm_id]
    return [case.model_dump() for case in cases]


@app.get("/api/v1/cases/{case_id}")
def get_case(case_id: str) -> Dict[str, Any]:
    return _get_case(case_id).model_dump()


@app.post("/api/v1/cases/{case_id}/resume")
def resume_case(case_id: str, payload: ResumeCaseRequest) -> Dict[str, Any]:
    state = _get_case(case_id)
    _assert_rm(state, payload.rm_id)
    state.documents.extend(payload.documents)
    state.company_profile.update(payload.company_profile_updates)
    state.audit_log.append({"actor": payload.rm_id, "action": "resume_with_documents", "result": {"documents_added": len(payload.documents)}})
    state = orchestrator.run(state)
    db.save_case(state)
    return state.model_dump()


@app.post("/api/v1/cases/{case_id}/approval-token")
def issue_approval_token(case_id: str, payload: ApproveCaseRequest) -> Dict[str, Any]:
    state = _get_case(case_id)
    _assert_rm(state, payload.rm_id)
    if state.final_status != "pending_approval":
        raise HTTPException(status_code=409, detail="Case chưa sẵn sàng phê duyệt")
    token = ApprovalService.issue(case_id, payload.rm_id)
    return {"case_id": case_id, "approval_token": token, "expires_in": settings.APPROVAL_TOKEN_TTL_SECONDS}


@app.post("/api/v1/cases/{case_id}/approve")
def approve_case(case_id: str, payload: ApproveCaseRequest, x_approval_token: str = Header(...)) -> Dict[str, Any]:
    state = _get_case(case_id)
    _assert_rm(state, payload.rm_id)
    try:
        ApprovalService.verify(x_approval_token, case_id, payload.rm_id)
    except ApprovalTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    state.approval_status = "approved"
    state.audit_log.append({"actor": payload.rm_id, "action": "approve", "result": {"comments": payload.comments}})
    try:
        actions = ActionExecutor.execute(state)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.save_case(state)
    return {"case_id": case_id, "approval_status": state.approval_status, "final_status": state.final_status, "actions_executed": actions}


@app.post("/api/v1/cases/{case_id}/reject")
def reject_case(case_id: str, payload: RejectCaseRequest) -> Dict[str, Any]:
    state = _get_case(case_id)
    _assert_rm(state, payload.rm_id)
    state.approval_status = "rejected"
    state.final_status = "rejected"
    state.audit_log.append({"actor": payload.rm_id, "action": "reject", "result": {"reason": payload.reason}})
    db.save_case(state)
    return {"case_id": case_id, "approval_status": "rejected", "final_status": "rejected"}


@app.get("/api/v1/search/products")
def search_products(q: str, top_k: int = Query(default=5, ge=1, le=10)) -> Dict[str, Any]:
    return product_rag.build_context(q, top_k=top_k)


def _get_case(case_id: str) -> SharedCaseState:
    state = db.get_case(case_id)
    if not state:
        raise HTTPException(status_code=404, detail="Case không tồn tại")
    return state


def _assert_rm(state: SharedCaseState, rm_id: str) -> None:
    if state.rm_id != rm_id:
        raise HTTPException(status_code=403, detail="RM không có quyền truy cập case này")
