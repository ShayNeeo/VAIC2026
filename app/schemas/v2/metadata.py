"""Unified Metadata Plane schemas.

Implements Phase 1 of the SHB Corporate Sales Copilot End-to-End Workflow.
Provides banking-grade provenance, immutability, and auditing through Metadata Objects, Versions, Relations, and Events.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from .common import SCHEMA_VERSION


class MetadataType(str, Enum):
    """Core domain entities in the Unified Metadata Plane."""
    CUSTOMER_PROFILE = "customer_profile"
    EVIDENCE_INVENTORY = "evidence_inventory"
    DOCUMENT = "document"
    DOCUMENT_ASSESSMENT = "document_assessment"
    EXTRACTED_FACT = "extracted_fact"
    EVIDENCE_RECORD = "evidence_record"
    CASE_CHECKLIST = "case_checklist"
    CHECKLIST_ITEM = "checklist_item"
    AGENT_RUN = "agent_run"
    SUBMISSION_DRAFT = "submission_draft"
    SUBMISSION_FROZEN = "submission_frozen"
    UNDERWRITING_DECISION = "underwriting_decision"


class RelationType(str, Enum):
    """Relationships between metadata objects for graph lineage."""
    EXTRACTED_FROM = "extracted_from"
    SUPERSEDES = "supersedes"
    DEPENDS_ON = "depends_on"
    PART_OF = "part_of"
    VALIDATES = "validates"
    CONTRADICTS = "contradicts"


class EventType(str, Enum):
    """Audit events for metadata objects."""
    CREATED = "created"
    UPDATED = "updated"
    VERIFIED = "verified"
    REJECTED = "rejected"
    FROZEN = "frozen"
    ACCESSED = "accessed"


class AccessControl(BaseModel):
    """Banking-grade access control for a metadata object/version."""
    model_config = ConfigDict(extra="forbid")

    allowed_roles: List[str] = Field(default_factory=lambda: ["RM", "UNDERWRITER", "SYSTEM"])
    tenant_id: str = "SHB-DEFAULT"
    confidentiality_level: str = "internal"  # public, internal, confidential, restricted


def generate_content_hash(payload: Dict[str, Any]) -> str:
    """Generates a deterministic SHA-256 hash of the JSON payload."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class MetadataVersion(BaseModel):
    """An immutable state snapshot of a MetadataObject."""
    model_config = ConfigDict(extra="forbid")

    version_id: str = Field(default_factory=lambda: str(uuid4()))
    object_id: str
    version_number: int = Field(ge=1)
    payload: Dict[str, Any]
    content_hash: str
    previous_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    source_system: str = "SHB_COPILOT"

    @classmethod
    def create(cls, object_id: str, version_number: int, payload: Dict[str, Any], created_by: str, previous_hash: Optional[str] = None) -> MetadataVersion:
        content_hash = generate_content_hash(payload)
        return cls(
            object_id=object_id,
            version_number=version_number,
            payload=payload,
            content_hash=content_hash,
            previous_hash=previous_hash,
            created_by=created_by
        )


class MetadataObject(BaseModel):
    """A logical entity in the system, composed of a chain of immutable versions."""
    model_config = ConfigDict(extra="forbid")

    object_id: str = Field(default_factory=lambda: str(uuid4()))
    type: MetadataType
    access_control: AccessControl = Field(default_factory=AccessControl)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    current_version_id: Optional[str] = None
    current_version_number: int = 0


class MetadataRelation(BaseModel):
    """A directed edge between two metadata objects for lineage tracking."""
    model_config = ConfigDict(extra="forbid")

    relation_id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    target_id: str
    relation_type: RelationType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetadataEvent(BaseModel):
    """Immutable audit log event for a metadata object."""
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    object_id: str
    version_id: Optional[str] = None
    event_type: EventType
    actor: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = Field(default_factory=dict)
