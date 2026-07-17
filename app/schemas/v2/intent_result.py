"""Pydantic mirror of plan_v2/contracts/intent_result.schema.json."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import SCHEMA_VERSION, DecisionImpact, ResolvedValue, ensure_unique

Confidence = Annotated[float, Field(ge=0.0, le=1.0)]


class RecommendedAction(str, Enum):
    CONTINUE_WORKFLOW = "continue_workflow"
    CALL_CONTEXT_TOOL = "call_context_tool"
    DEFER_MISSING_FIELD = "defer_missing_field"
    ASK_CLARIFICATION = "ask_clarification"
    REQUEST_CONFIRMATION = "request_confirmation"
    REJECT_OUT_OF_SCOPE = "reject_out_of_scope"
    ESCALATE_HUMAN = "escalate_human"


class Ambiguity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    hypotheses: List[str] = Field(min_length=2)
    decision_impact: DecisionImpact


class EvidenceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    text: str
    message_id: str


class IntentResult(BaseModel):
    """contracts/intent_result.schema.json"""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION, pattern=r"^2\.0\.0$")
    primary_intent: str = Field(min_length=1)
    sub_intents: List[str]
    user_goal: str = Field(min_length=1)
    entities: Dict[str, Any]
    resolved_slots: Dict[str, ResolvedValue]
    constraints: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    missing_information: List[str]
    ambiguities: List[Ambiguity]
    evidence_spans: List[EvidenceSpan]
    field_confidence: Dict[str, Confidence]
    overall_confidence: float = Field(ge=0.0, le=1.0)
    recommended_action: RecommendedAction

    _check_sub_intents_unique = field_validator("sub_intents")(ensure_unique)
    _check_missing_information_unique = field_validator("missing_information")(ensure_unique)
