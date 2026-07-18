"""Typed models shared by ingestion, indexing and retrieval."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.knowledge.retrieval_contracts import AuthorityTier, VerificationStatus


class ProductDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    name: str
    family: str
    segments: List[str]
    description: str
    benefits: List[str]
    required_documents: List[str]
    eligibility_summary: str
    effective_from: date
    effective_to: Optional[date] = None
    active: bool
    document_id: str
    document_version: str
    section: str
    access_scope: Dict[str, Any]


class KnowledgeChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    document_version: str
    product_id: str
    section_path: str
    chunk_type: str = "product_overview"
    text: str
    effective_from: date
    effective_to: Optional[date] = None
    active: bool
    segments: List[str]
    access_scope: Dict[str, Any]
    content_hash: str

    # Phase 2 lifecycle/security metadata (RAG & Guardrail Implementation
    # Plan, "KnowledgeChunk Schema Extension"). All optional/defaulted so
    # every pre-Phase-2 KnowledgeChunk(...) call site in this repo (product
    # ingestion, legal_service.py, all Phase 0/1 tests) keeps constructing
    # valid instances unchanged -- these fields describe UNKNOWN, not
    # authoritative/verified, when absent (see search_with_diagnostics()'s
    # honest-default filtering: a chunk with is_superseded=None is treated
    # as "unknown, not provably current" wherever a policy asks, never
    # silently promoted to "current").
    customer_id: Optional[str] = None
    case_id: Optional[str] = None
    source_type: Optional[str] = None
    authority_tier: Optional[AuthorityTier] = None
    verification_status: Optional[VerificationStatus] = None
    is_superseded: bool = False
    is_quarantined: bool = False
    allowed_roles: List[str] = Field(default_factory=list)
    # Phase 2 continuous-build addition (docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md
    # "## Phase 2 continuation"). Freeform label, not an enforced ordered
    # tier -- this repo has no per-actor "clearance level" concept to
    # compare against (RetrievalRequest.actor_role is a role name, not a
    # classification rank), so enforcement is allow-list based (a caller
    # passes the exact set of classifications it may see), not a
    # PUBLIC<INTERNAL<CONFIDENTIAL<RESTRICTED ordering comparison.
    security_classification: str = "INTERNAL"
    # Phase 3 (Hierarchical Parent-Child Retrieval) -- optional, None means
    # "this chunk has no parent" (the overwhelming majority of chunks in
    # this repo today: Legal rules and Product overviews are flat leaves).
    # See app/operations/sop_knowledge.py for the one real ingestion path
    # that sets this (SOP step chunks point at a per-workflow overview
    # parent chunk).
    parent_chunk_id: Optional[str] = None


class RetrievalHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk: KnowledgeChunk
    score: float = Field(ge=0.0, le=1.0)
    dense_score: float = Field(ge=0.0, le=1.0)
    sparse_score: float = Field(ge=0.0, le=1.0)


class IngestReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_version: str
    source_path: str
    source_hash: str
    accepted: int
    rejected: int
    indexed: int
    errors: List[str]
