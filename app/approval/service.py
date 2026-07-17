"""Signed approvals bound to case, approver, permissions and exact payload hash."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
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
            "token_id": str(uuid.uuid4()),
            "case_id": case_id,
            "approver_id": approver_id,
            "permissions": sorted(set(permissions)),
            "payload_hash": payload_hash(payload),
            "issued_at": issued_at,
            "expires_at": issued_at + self.ttl_seconds,
            "nonce": secrets.token_urlsafe(16),
            "one_time_use": True,
        }
        token = self._encode(claims)
        self.repository.register_approval(
            claims["token_id"], case_id, approver_id, claims["payload_hash"], claims["expires_at"]
        )
        return {"token": token, "claims": claims}

    def verify_and_consume(self, token: str, *, case_id: str, approver_id: str, payload: Dict[str, Any], permission: str) -> Dict[str, Any]:
        claims = self._decode(token)
        if claims.get("case_id") != case_id or claims.get("approver_id") != approver_id:
            raise ApprovalError("approval does not belong to this case/approver")
        if permission not in claims.get("permissions", []):
            raise ApprovalError("approval does not grant the requested action")
        if int(claims.get("expires_at", 0)) < int(time.time()):
            raise ApprovalError("approval expired")
        if claims.get("payload_hash") != payload_hash(payload):
            raise ApprovalError("payload changed after approval")
        record = self.repository.approval(str(claims.get("token_id")))
        if not record or record["status"] != "issued" or record["payload_hash"] != claims["payload_hash"]:
            raise ApprovalError("approval is invalid or already consumed")
        if not self.repository.consume_approval(claims["token_id"]):
            raise ApprovalError("approval was already consumed")
        return claims

    def _encode(self, claims: Dict[str, Any]) -> str:
        body = base64.urlsafe_b64encode(json.dumps(claims, separators=(",", ":")).encode()).decode().rstrip("=")
        signature = hmac.new(self.secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        return f"{body}.{signature}"

    def _decode(self, token: str) -> Dict[str, Any]:
        try:
            body, signature = token.split(".", 1)
            expected = hmac.new(self.secret.encode(), body.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise ApprovalError("invalid approval signature")
            return json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)).decode())
        except ApprovalError:
            raise
        except Exception as exc:
            raise ApprovalError("malformed approval token") from exc
