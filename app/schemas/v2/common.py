"""Shared enums and cross-cutting models mirroring plan_v2/contracts.

Each enum's members are copied verbatim from the corresponding "enum" list in
the JSON Schema contracts so Pydantic rejects exactly the values JSON Schema
would reject (plan_v2/03_SHARED_CONTRACTS.md - "Unknown enum bi reject").
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "2.0.0"

T = TypeVar("T")


def ensure_unique(items: List[T]) -> List[T]:
    """Mirror JSON Schema's "uniqueItems": true used across several contract arrays."""
    seen = set()
    for item in items:
        if item in seen:
            raise ValueError(f"duplicate item not allowed: {item!r}")
        seen.add(item)
    return items


class SourceType(str, Enum):
    """intent_result.schema.json#/$defs/resolvedValue/properties/source_type"""

    USER_EXPLICIT = "user_explicit"
    WORKSPACE = "workspace"
    SSO = "sso"
    IAM = "iam"
    CRM = "crm"
    DOCUMENT = "document"
    WORKFLOW = "workflow"
    CONVERSATION_CONFIRMED = "conversation_confirmed"
    CACHE = "cache"
    LLM_INFERENCE = "llm_inference"


class DecisionImpact(str, Enum):
    """Used by intent ambiguities and context conflicts."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ResolvedValue(BaseModel):
    """intent_result.schema.json#/$defs/resolvedValue

    Every auto-filled or inferred field in the system must be wrapped in this
    envelope so downstream consumers can see provenance and confidence
    instead of a bare value (plan_v2/03_SHARED_CONTRACTS.md section 3).
    """

    model_config = ConfigDict(extra="forbid")

    value: Any
    source_type: SourceType
    source_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    confirmed: bool
    observed_at: datetime
    expires_at: Optional[datetime] = None
