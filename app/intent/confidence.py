"""Deterministic field confidence and decision policy."""

from __future__ import annotations

from app.schemas.v2.common import DecisionImpact, ResolvedValue, SourceType

BASE_CONFIDENCE = {
    SourceType.SSO: 1.0,
    SourceType.IAM: 1.0,
    SourceType.WORKSPACE: 1.0,
    SourceType.CRM: 0.98,
    SourceType.USER_EXPLICIT: 0.95,
    SourceType.WORKFLOW: 0.95,
    SourceType.DOCUMENT: 0.92,
    SourceType.CONVERSATION_CONFIRMED: 0.90,
    SourceType.CACHE: 0.85,
    SourceType.LLM_INFERENCE: 0.70,
}


def calibrated_confidence(value: ResolvedValue, *, stale: bool = False, conflict: bool = False) -> float:
    score = min(value.confidence, BASE_CONFIDENCE.get(value.source_type, value.confidence))
    if stale:
        score -= 0.25
    if conflict:
        score -= 0.30
    return round(max(0.0, min(score, 1.0)), 4)


def field_action(confidence: float, *, impact: DecisionImpact, required_now: bool, external_write: bool = False) -> str:
    if external_write:
        return "preview_and_approve"
    if confidence >= 0.90 and impact in {DecisionImpact.NONE, DecisionImpact.LOW}:
        return "continue"
    if confidence >= 0.70 and impact in {DecisionImpact.NONE, DecisionImpact.LOW}:
        return "continue_visible_assumption"
    if not required_now:
        return "defer"
    return "clarify"

