"""Typed models shared by ingestion, indexing and retrieval."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


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
