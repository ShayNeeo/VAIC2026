"""Approval Agent MCP Server — HMAC token issue/verify."""

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import hashlib
import hmac
import json
import time
import uuid
import base64

from mcp_common.config import settings


mcp = FastMCP("approval-agent")

_token_store: Dict[str, Dict[str, Any]] = {}


class IssueTokenRequest(BaseModel):
    case_id: str
    rm_id: str
    permissions: List[str]
    payload: Dict[str, Any]


class VerifyTokenRequest(BaseModel):
    token: str
    case_id: str
    rm_id: str
    payload: Dict[str, Any]


def _sign_payload(payload: Dict[str, Any]) -> str:
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    secret = settings.APPROVAL_SECRET.encode()
    return hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()


@mcp.tool()
async def issue_token(request: IssueTokenRequest) -> Dict[str, Any]:
    token_id = str(uuid.uuid4())
    now = int(time.time())
    expires = now + settings.APPROVAL_TOKEN_TTL_SECONDS

    payload_hash = _sign_payload(request.payload)

    token_data = {
        "token_id": token_id,
        "case_id": request.case_id,
        "approver_id": request.rm_id,
        "permissions": request.permissions,
        "payload_hash": payload_hash,
        "issued_at": now,
        "expires_at": expires,
        "nonce": uuid.uuid4().hex[:16],
        "one_time_use": True,
        "consumed": False,
    }

    token_bytes = json.dumps(token_data, sort_keys=True).encode()
    signature = hmac.new(settings.APPROVAL_SECRET.encode(), token_bytes, hashlib.sha256).hexdigest()
    token_data["signature"] = signature

    _token_store[token_id] = token_data

    compact = base64.urlsafe_b64encode(json.dumps(token_data).encode()).decode()
    return {"token": compact, "expires_in": settings.APPROVAL_TOKEN_TTL_SECONDS}


@mcp.tool()
async def verify_token(request: VerifyTokenRequest) -> Dict[str, Any]:
    try:
        token_data = json.loads(base64.urlsafe_b64decode(request.token.encode()).decode())
    except Exception:
        return {"valid": False, "reason": "INVALID_TOKEN_FORMAT"}

    signature = token_data.pop("signature", "")
    token_bytes = json.dumps(token_data, sort_keys=True).encode()
    expected_sig = hmac.new(settings.APPROVAL_SECRET.encode(), token_bytes, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        return {"valid": False, "reason": "INVALID_SIGNATURE"}

    if time.time() > token_data["expires_at"]:
        return {"valid": False, "reason": "TOKEN_EXPIRED"}

    if token_data["case_id"] != request.case_id:
        return {"valid": False, "reason": "CASE_ID_MISMATCH"}

    if token_data["approver_id"] != request.rm_id:
        return {"valid": False, "reason": "APPROVER_MISMATCH"}

    if _sign_payload(request.payload) != token_data["payload_hash"]:
        return {"valid": False, "reason": "PAYLOAD_MISMATCH"}

    if token_data["one_time_use"]:
        stored = _token_store.get(token_data["token_id"])
        if stored and stored.get("consumed"):
            return {"valid": False, "reason": "TOKEN_ALREADY_USED"}

    token_data["consumed"] = True
    _token_store[token_data["token_id"]] = token_data

    return {"valid": True, "token_id": token_data["token_id"], "permissions": token_data["permissions"]}


@mcp.tool()
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "approval-agent", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.http_app(), host=settings.BIND_HOST, port=settings.APPROVAL_AGENT_PORT)