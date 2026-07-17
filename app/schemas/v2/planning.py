"""Deterministic Planner, Next Best Question and Next Best Action contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PlanStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    title: str
    owner: str
    status: str
    dependencies: List[str] = Field(default_factory=list)
    reason: str
    stop_condition: Optional[str] = None


class ExecutionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_version: int = Field(ge=1)
    goals: List[str]
    steps: List[PlanStep]
    changed_because: Optional[str] = None
    created_at: datetime


class NextBestQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    question: str
    reason: str
    target_field: str
    source_gap: str
    decision_impact: str
    priority: int = Field(ge=1, le=5)
    answer_type: str
    options: List[str] = Field(default_factory=list)
    blocking_steps: List[str] = Field(default_factory=list)
    status: str = "open"
    answered_value: Any = None
    answered_by: Optional[str] = None
    answered_at: Optional[datetime] = None


class NextBestAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str
    action_type: str
    title: str
    rationale: str
    owner_role: str
    sla_hours: int = Field(ge=1)
    dependencies: List[str] = Field(default_factory=list)
    risk_level: str
    requires_approval: bool
    payload_preview: Dict[str, Any] = Field(default_factory=dict)
    status: str = "proposed"

