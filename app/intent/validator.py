"""Semantic validation beyond the Pydantic/JSON contract."""

from __future__ import annotations

from app.intent.taxonomy import is_known_intent
from app.schemas.v2.intent_result import IntentResult


class IntentSemanticError(ValueError):
    pass


def validate_intent_result(result: IntentResult, *, message: str, message_id: str) -> IntentResult:
    unknown = [item for item in [result.primary_intent, *result.sub_intents] if not is_known_intent(item)]
    if unknown:
        raise IntentSemanticError(f"unknown intent ids: {unknown}")
    for span in result.evidence_spans:
        if span.message_id != message_id:
            raise IntentSemanticError("evidence span references another message")
        if span.text and span.text not in message:
            raise IntentSemanticError("evidence span is not present in the source message")
    for name, value in result.resolved_slots.items():
        if value.source_type.value == "llm_inference" and value.confirmed:
            raise IntentSemanticError(f"LLM inferred slot cannot be confirmed: {name}")
    return result

