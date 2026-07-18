"""Signed approvals bound to case, approver, permissions and exact payload hash."""

from __future__ import annotations

import jwt
import time
import uuid
import json
import hashlib
from typing import Any, Dict, Iterable

from app.config import settings
from app.storage.repository import V2Repository

class ApprovalError(ValueError):
    pass


def payload_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ApprovalServiceV2:
    def __init__(self, repository: V2Repository, *, secret: str | None = None, ttl_seconds: int | None = None) -> None:
        self.repository = repository
        self.secret = secret or settings.APPROVAL_SECRET
        self.ttl_seconds = ttl_seconds or settings.APPROVAL_TOKEN_TTL_SECONDS
        if settings.APP_ENV != "development" and self.secret == "demo-only-change-me":
            raise RuntimeError("APPROVAL_SECRET must be configured outside development")

    def issue(self, *, case_id: str, approver_id: str, permissions: Iterable[str], payload: Dict[str, Any]) -> Dict[str, Any]:
        issued_at = int(time.time())
        claims = {
            "iss": "shb_copilot",
            "aud": "underwriting_engine",
            "sub": approver_id,
            "role": "rm_approver",
            "case_id": case_id,
            "case_version": str(payload.get("version", "1")),
            "submission_id": payload.get("submission_id", ""),
            "submission_version": payload.get("submission_version", ""),
            "permissions": sorted(set(permissions)),
            "package_hash": payload_hash(payload),
            "iat": issued_at,
            "exp": issued_at + self.ttl_seconds,
            "jti": str(uuid.uuid4()),
            "one_time_use": True,
        }
        token = jwt.encode(claims, self.secret, algorithm="HS256")
        self.repository.register_approval(
            claims["jti"], case_id, approver_id, claims["package_hash"], claims["exp"]
        )
        return {"token": token, "claims": claims}

    def verify_and_consume(self, token: str, *, case_id: str, approver_id: str, payload: Dict[str, Any], permission: str) -> Dict[str, Any]:
        try:
            # Enforce allowlist of algorithms and explicitly forbid "none"
            claims = jwt.decode(
                token, 
                self.secret, 
                algorithms=["HS256"], 
                issuer="shb_copilot", 
                audience="underwriting_engine"
            )
        except jwt.ExpiredSignatureError:
            raise ApprovalError("approval expired")
        except jwt.InvalidTokenError as exc:
            raise ApprovalError(f"invalid or malformed approval token: {exc}")

        if claims.get("case_id") != case_id or claims.get("sub") != approver_id:
            raise ApprovalError("approval does not belong to this case/approver")
        if permission not in claims.get("permissions", []):
            raise ApprovalError("approval does not grant the requested action")
        if claims.get("package_hash") != payload_hash(payload):
            raise ApprovalError("payload changed after approval")
        
        jti = claims.get("jti")
        record = self.repository.approval(str(jti))
        if not record or record["status"] != "issued" or record["payload_hash"] != claims["package_hash"]:
            raise ApprovalError("approval is invalid or already consumed")
        
        if not self.repository.consume_approval(jti):
            raise ApprovalError("approval was already consumed")
        
        return claims
