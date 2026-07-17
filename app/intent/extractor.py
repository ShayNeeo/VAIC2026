"""Intent extraction with optional LLM and deterministic fail-safe fallback."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.config import settings
from app.intent.fallback import DeterministicIntentExtractor
from app.intent.normalizer import normalize_text
from app.intent.prompt import build_intent_system_prompt
from app.intent.validator import validate_intent_result
from app.schemas.v2.context_snapshot import ContextSnapshot
from app.schemas.v2.intent_result import IntentResult

logger = logging.getLogger(__name__)


class IntentExtractionError(ValueError):
    pass


class IntentExtractor:
    def __init__(
        self,
        *,
        client: Any | None = None,
        prefer_llm: Optional[bool] = None,
        fallback: DeterministicIntentExtractor | None = None,
    ) -> None:
        self.prefer_llm = settings.INTENT_USE_LLM if prefer_llm is None else prefer_llm
        self.model = settings.GOOGLE_MODEL if settings.DEFAULT_LLM == "google" else settings.OPENAI_MODEL
        self.client = client
        if self.client is None and self.prefer_llm:
            if settings.DEFAULT_LLM == "google" and settings.GOOGLE_API_KEY:
                # Google AI Studio exposes an OpenAI-compatible endpoint, so the
                # openai SDK can call gemma-4-31b-it directly with the AI Studio
                # key. OpenAI remains a selectable fallback via DEFAULT_LLM=openai.
                self.client = AsyncOpenAI(
                    api_key=settings.GOOGLE_API_KEY,
                    base_url=settings.GOOGLE_ENDPOINT,
                )
                self.model = settings.GOOGLE_MODEL
            elif settings.DEFAULT_LLM == "openai" and settings.OPENAI_API_KEY:
                self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                self.model = settings.OPENAI_MODEL
        self.fallback = fallback or DeterministicIntentExtractor()
        self.last_run = {
            "mode": "not_started",
            "model": self.model,
            "prompt_version": "intent-schema-v2.1",
            "token_usage": {"input": 0, "output": 0, "total": 0},
        }

    async def extract_intent(
        self,
        message: str,
        message_id: str,
        context: Optional[ContextSnapshot] = None,
    ) -> IntentResult:
        normalized = normalize_text(message)
        if not normalized:
            raise IntentExtractionError("message must not be empty")
        if self.client is None:
            self.last_run = {
                "mode": "deterministic_fallback",
                "model": "deterministic-intent-v2",
                "prompt_version": "intent-schema-v2.1",
                "token_usage": {"input": 0, "output": 0, "total": 0},
                "fallback_reason": "llm_disabled_or_api_key_missing",
            }
            return self._fallback(normalized, message_id, context)
        try:
            result = await asyncio.wait_for(
                self._extract_llm(normalized, message_id, context),
                timeout=settings.MODEL_TIMEOUT_SECONDS,
            )
            return validate_intent_result(result, message=normalized, message_id=message_id)
        except Exception as exc:
            logger.warning(
                "intent_llm_fallback",
                extra={"error_type": type(exc).__name__, "message_id": message_id},
            )
            self.last_run = {
                "mode": "deterministic_fallback",
                "model": "deterministic-intent-v2",
                "prompt_version": "intent-schema-v2.1",
                "token_usage": {"input": 0, "output": 0, "total": 0},
                "fallback_reason": type(exc).__name__,
            }
            return self._fallback(normalized, message_id, context)

    def _fallback(
        self,
        message: str,
        message_id: str,
        context: Optional[ContextSnapshot],
    ) -> IntentResult:
        return validate_intent_result(
            self.fallback.extract(message, message_id, context),
            message=message,
            message_id=message_id,
        )

    async def _extract_llm(
        self,
        message: str,
        message_id: str,
        context: Optional[ContextSnapshot],
    ) -> IntentResult:
        schema_json = json.dumps(IntentResult.model_json_schema(), ensure_ascii=False)
        prompt = build_intent_system_prompt(context) + (
            "\n\nJSON SCHEMA BẮT BUỘC:\n"
            + schema_json
            + f"\nSchema version là 2.0.0; evidence_spans dùng message_id={message_id!r}."
        )
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            raise IntentExtractionError("model returned empty output")
        try:
            result = IntentResult.model_validate_json(content)
        except ValidationError as exc:
            raise IntentExtractionError(f"model output violates IntentResult: {exc}") from exc
        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        self.last_run = {
            "mode": "llm_structured_output",
            "model": self.model,
            "prompt_version": "intent-schema-v2.1",
            "token_usage": {
                "input": input_tokens,
                "output": output_tokens,
                "total": int(getattr(usage, "total_tokens", input_tokens + output_tokens) or 0),
            },
        }
        return result
