"""Workspace context: current screen / selected customer-case-task (realtime, UI session).

No caching, no TTL policy (see app/context/freshness.py docstring) -- every
call reads the live session store. A missing session raises rather than
guessing; module 04 section 9 assigns the "use explicit IDs from the
request, otherwise ask" fallback to the assembler (V2-003), not to this
service.
"""

from __future__ import annotations

from threading import RLock
from typing import Any, Dict, Optional

from app.integrations.errors import UpstreamUnavailableError
from app.schemas.v2.context_snapshot import Workspace


class WorkspaceSessionStore:
    """SYNTHETIC in-memory session store standing in for the real UI/session backend."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def set_session(self, session_id: str, **fields: Any) -> None:
        with self._lock:
            self._sessions[session_id] = {"session_id": session_id, **fields}

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return dict(self._sessions[session_id]) if session_id in self._sessions else None


class WorkspaceContextService:
    def __init__(self, store: WorkspaceSessionStore) -> None:
        self._store = store

    def get(self, session_id: str, *, correlation_id: str) -> Workspace:
        raw = self._store.get(session_id)
        if raw is None:
            raise UpstreamUnavailableError(
                correlation_id, upstream="workspace", reason=f"unknown session_id {session_id}"
            )
        return Workspace.model_validate(raw)
