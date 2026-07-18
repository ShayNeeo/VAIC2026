"""Typed models shared by ingestion, indexing and retrieval."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    name: str
    family: str = "uncategorized"
    segments: List[str] = Field(default_factory=list)
    description: str = ""
    benefits: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    eligibility_summary: str = ""
    effective_from: date
    effective_to: Optional[date] = None
    active: bool
    document_id: str
    document_version: str
    section: str
    access_scope: Dict[str, Any]
    # Optional governance fields (SHB product manual). All optional so the
    # existing synthetic catalog keeps validating unchanged.
    bank: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    risk_level: str = "unknown"
    source_label: List[str] = Field(default_factory=list)
    data_label: Optional[str] = None
    business_need: Optional[str] = None
    target_profile: Optional[str] = None
    public_features: List[str] = Field(default_factory=list)
    public_conditions: List[str] = Field(default_factory=list)
    internal_required: List[str] = Field(default_factory=list)
    sales_signals: List[str] = Field(default_factory=list)
    discovery_questions: List[str] = Field(default_factory=list)
    cross_sell: List[str] = Field(default_factory=list)
    branch_behavior: str = "READY_TO_PREPARE"
    source_date: Optional[date] = None


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
    # Governance fields preserved verbatim from the SHB product manual so the
    # matcher/enricher can enforce safe-answer rules without re-parsing text.
    risk_level: str = "unknown"
    source_label: List[str] = Field(default_factory=list)
    data_label: Optional[str] = None
    internal_required: List[str] = Field(default_factory=list)
    branch_behavior: str = "READY_TO_PREPARE"
    # Date the source document was captured/frozen. Two chunks for the same
    # product_id are reconciled by latest source_date (see index.upsert), so
    # the RAG only surfaces the most recent published version -- never a stale
    # promotion, fee or limit from an older corpus.
    source_date: Optional[date] = None


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
