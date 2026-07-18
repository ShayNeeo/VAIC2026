"""Metadata Plane Foundation - Core Models (P0.1)

Provides a unified metadata structure for all entities across the E2E lifecycle,
from raw artifacts to underwriting decisions. 
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MetadataRef(BaseModel):
    """Pointer to another object in the system."""
    meta_id: str
    meta_type: str
    object_version: str


class MetadataRelation(BaseModel):
    """Relation between this object and another (e.g. DERIVED_FROM, RENEWS)."""
    relation_type: str
    target: MetadataRef


class MetadataEvent(BaseModel):
    """Audit log of something that happened to this object."""
    event_id: str
    event_type: str
    timestamp: str
    actor_id: str
    details: Dict[str, Any] = Field(default_factory=dict)


class MetadataEnvelope(BaseModel):
    """The central unified metadata plane struct.
    
    Every core object in the system (RawArtifact, Document, ExtractedFact, 
    Evidence, GroundingPack, AgentRun, RMSubmissionApproval, 
    UnderwritingSubmission, UnderwritingDecision, ActionExecution) MUST 
    embed this envelope.
    """
    model_config = ConfigDict(extra="ignore")
    
    meta_id: str
    meta_type: str
    schema_version: str = "1.0.0"
    object_version: str
    case_id: str
    customer_id: str
    
    source_refs: List[MetadataRef] = Field(default_factory=list)
    parent_refs: List[MetadataRef] = Field(default_factory=list)
    relations: List[MetadataRelation] = Field(default_factory=list)
    
    content_hash: str
    created_by: str
    created_at: str
    validation_status: str
    security_scope: str
    
    events: List[MetadataEvent] = Field(default_factory=list)
