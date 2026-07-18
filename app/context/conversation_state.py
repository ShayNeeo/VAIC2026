"""Conversation context: confirmed facts / rejected assumptions / open questions.

plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md section 9: "Conversation state
corrupt -> Start clean conversation state, preserve case state." Only this
service's own state resets on corruption; it never touches the rest of
SharedCaseState.
"""

from __future__ import annotations

import logging
from threading import RLock
from typing import Any, Dict, Optional

from pydantic import ValidationError as PydanticValidationError

from app.schemas.v2.context_snapshot import Conversation

logger = logging.getLogger("app.context.conversation_state")


class ConversationStateStore:
    """SYNTHETIC in-memory store standing in for the real conversation State DB."""

    def __init__(self) -> None:
        self._by_case: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def set_raw(self, case_id: str, raw: Dict[str, Any]) -> None:
        """Accepts a raw dict (including a deliberately malformed one, for
        corruption-recovery tests) instead of a validated Conversation."""
        with self._lock:
            self._by_case[case_id] = raw

    def get_raw(self, case_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return dict(self._by_case[case_id]) if case_id in self._by_case else None


def _clean_state() -> Conversation:
    return Conversation(current_goal=None, confirmed_facts={}, rejected_assumptions=[], open_questions=[])


class ConversationStateService:
    def __init__(self, store: ConversationStateStore) -> None:
        self._store = store

    def get(self, case_id: str, *, correlation_id: str) -> Conversation:
        raw = self._store.get_raw(case_id)
        if raw is None:
            return _clean_state()
        try:
            return Conversation.model_validate(raw)
        except PydanticValidationError:
            logger.warning(
                "conversation_state_corrupt",
                extra={"case_id": case_id, "correlation_id": correlation_id},
            )
            return _clean_state()
