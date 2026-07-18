"""Small signed session-token layer for the local demo.

This is intentionally not a replacement for the bank's SSO/IAM. It gives the
local dashboard a real login boundary while keeping role/permission lookup in
the existing SQLite SSO/IAM adapters.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from app.config import settings


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_session_token(employee_id: str, *, ttl_seconds: int = 8 * 60 * 60) -> str:
    payload = {
        "sub": employee_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl_seconds,
        "jti": secrets.token_urlsafe(12),
    }
    encoded = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(settings.AUTH_SECRET.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
    return f"shb.{encoded}.{_b64(signature)}"


def verify_session_token(token: str) -> dict[str, Any] | None:
    try:
        prefix, encoded, signature = token.split(".", 2)
        if prefix != "shb":
            return None
        expected = hmac.new(settings.AUTH_SECRET.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(signature)):
            return None
        payload = json.loads(_unb64(encoded).decode("utf-8"))
        if not isinstance(payload, dict) or not payload.get("sub") or int(payload.get("exp", 0)) <= int(time.time()):
            return None
        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError):
        return None
