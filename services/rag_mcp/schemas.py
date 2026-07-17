"""Strict wire contracts returned by MCP tools."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


KnowledgeDomain = Literal["product", "legal", "operations", "all"]
ExpertAgentType = Literal[
    "ProductExpert",
    "LegalExpert",
    "OperationsExpert",
    "EvidenceExpert",
    "KnowledgeAdmin",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CallerPrincipal(StrictModel):
    employee_id: str = Field(min_length=2, max_length=128)
    branch: str = Field(min_length=2, max_length=32)
    agent_type: ExpertAgentType
    agent_instance_id: str = Field(min_length=4, max_length=128)
    roles: List[str] = Field(default_factory=list, max_length=20)
    permissions: List[str] = Field(default_factory=list, max_length=50)


class SearchFilters(StrictModel):
    domain: KnowledgeDomain = "all"
    product_ids: List[str] = Field(default_factory=list, max_length=20)
    document_ids: List[str] = Field(default_factory=list, max_length=20)
    segments: List[str] = Field(default_factory=list, max_length=20)
    chunk_types: List[str] = Field(default_factory=list, max_length=20)
    document_version: Optional[str] = Field(default=None, max_length=64)
    as_of: Optional[date] = None


class SearchKnowledgeRequest(StrictModel):
    query: str = Field(min_length=2, max_length=2000)
    principal: CallerPrincipal
    filters: SearchFilters = Field(default_factory=SearchFilters)
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.30, ge=0.0, le=1.0)
    max_context_chars: int = Field(default=8000, ge=500, le=30000)
    trace_id: str = Field(min_length=4, max_length=128)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        return " ".join(value.split())


class ScopedSearchFilters(StrictModel):
    """Search filters exposed to an Expert Agent; domain is fixed by its MCP endpoint."""

    product_ids: List[str] = Field(default_factory=list, max_length=20)
    document_ids: List[str] = Field(default_factory=list, max_length=20)
    segments: List[str] = Field(default_factory=list, max_length=20)
    chunk_types: List[str] = Field(default_factory=list, max_length=20)
    document_version: Optional[str] = Field(default=None, max_length=64)
    as_of: Optional[date] = None


class ExpertSearchRequest(StrictModel):
    query: str = Field(min_length=2, max_length=2000)
    principal: CallerPrincipal
    filters: ScopedSearchFilters = Field(default_factory=ScopedSearchFilters)
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.30, ge=0.0, le=1.0)
    max_context_chars: int = Field(default=8000, ge=500, le=30000)
    trace_id: str = Field(min_length=4, max_length=128)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        return " ".join(value.split())


class GetChunkRequest(StrictModel):
    chunk_id: str = Field(min_length=4, max_length=256)
    principal: CallerPrincipal
    as_of: Optional[date] = None
    trace_id: str = Field(min_length=4, max_length=128)


class ListSourcesRequest(StrictModel):
    principal: CallerPrincipal
    domain: KnowledgeDomain = "all"
    trace_id: str = Field(min_length=4, max_length=128)


class ExpertListSourcesRequest(StrictModel):
    principal: CallerPrincipal
    trace_id: str = Field(min_length=4, max_length=128)


class CitationVerificationRequest(StrictModel):
    chunk_id: str = Field(min_length=4, max_length=256)
    expected_content_hash: str = Field(min_length=64, max_length=64)
    expected_document_id: Optional[str] = Field(default=None, max_length=256)
    expected_document_version: Optional[str] = Field(default=None, max_length=64)
    principal: CallerPrincipal
    trace_id: str = Field(min_length=4, max_length=128)


class ChunkCitation(StrictModel):
    document_id: str
    document_version: str
    section_path: str
    source_id: str
    content_hash: str


class RetrievedChunk(StrictModel):
    chunk_id: str
    domain: Literal["product", "legal", "operations"]
    chunk_type: str
    text: str
    product_id: Optional[str] = None
    score: float = Field(ge=0.0, le=1.0)
    dense_score: float = Field(ge=0.0, le=1.0)
    sparse_score: float = Field(ge=0.0, le=1.0)
    effective_from: date
    effective_to: Optional[date] = None
    segments: List[str] = Field(default_factory=list)
    citation: ChunkCitation
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchKnowledgeResponse(StrictModel):
    query_id: str
    trace_id: str
    grounded: bool
    retrieval_mode: str
    embedding_provider: str
    filters_applied: Dict[str, Any]
    chunks: List[RetrievedChunk]
    context_text: str
    latency_ms: int = Field(ge=0)
    audit_event_id: str
    safety: Dict[str, bool]


class GetChunkResponse(StrictModel):
    trace_id: str
    chunk: RetrievedChunk
    audit_event_id: str


class KnowledgeSource(StrictModel):
    source_id: str
    name: str
    domain: Literal["product", "legal", "operations"]
    tier: str
    sensitivity: str
    owner: Dict[str, Any]
    dataset_version: str
    source_hash: str
    active: bool
    chunk_count: int
    indexed_at: datetime


class ListSourcesResponse(StrictModel):
    trace_id: str
    sources: List[KnowledgeSource]
    audit_event_id: str


class CitationVerificationResponse(StrictModel):
    trace_id: str
    valid: bool
    chunk_id: str
    actual_citation: Optional[ChunkCitation] = None
    mismatches: List[str] = Field(default_factory=list)
    audit_event_id: str


class ToolCapability(StrictModel):
    name: str
    purpose: str
    domain: KnowledgeDomain
    read_only: bool = True


class AgentCapabilityResponse(StrictModel):
    agent_type: ExpertAgentType
    policy_version: str
    tools: List[ToolCapability]


class HealthResponse(StrictModel):
    status: Literal["ok", "degraded"]
    service: str
    version: str
    protocol: str
    schema_version: int
    embedding_provider: str
    source_count: int
    chunk_count: int
    chunks_by_domain: Dict[str, int]
    db_quick_check: str
    auth_required: bool
    data_mode: str
    corpus_version: str
    last_ingestion_status: str
    last_ingestion_run_id: Optional[str] = None
    tool_policy_version: str
    agent_profiles: List[str]


class IngestSummary(StrictModel):
    run_id: str
    status: Literal["passed", "failed"]
    corpus_version: str
    source_count: int
    chunk_count: int
    chunks_by_domain: Dict[str, int]
    source_hashes: Dict[str, str]
    quality_checks: Dict[str, int] = Field(default_factory=dict)
    rejected_chunk_count: int = 0
    warnings: List[str] = Field(default_factory=list)
