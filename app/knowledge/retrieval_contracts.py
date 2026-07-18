"""Canonical retrieval contracts -- RAG & Guardrail Implementation Plan
Phase 1 (docs/RAG_GUARDRAIL_IMPLEMENTATION_PLAN.md), sections 2-3 of the
Phase 1 spec ("Canonical Retrieval Models", "Error Taxonomy").

Status: INTERFACE_ONLY / NOT_RUNTIME_WIRED. These are typed contracts a
future Controlled Retrieval Plane (Phase 2+) will use to pass structured
requests/candidates between Query Understanding, Routing, and the
Product/Legal/Operations retrieval policies. No production code path
constructs a RetrievalRequest or RetrievalCandidate yet -- today's real
callers (ProductKnowledgeService.search(), LegalKnowledgeService.search(),
PersistentHybridIndex.search_with_diagnostics()) still take plain keyword
arguments and return List[RetrievalHit] + the index-level
app.knowledge.index.RetrievalDiagnostics dataclass. That index-level
dataclass is deliberately NOT replaced by RetrievalDiagnostics here -- it
answers a narrower question ("why did this one PersistentHybridIndex.search
call return what it returned") that Phase 0 already wired into real code
with real tests; this module answers the broader pipeline-level question
("what happened across query understanding, routing, filtering and
ranking for this one retrieval run") that nothing calls yet.

tenant_id is present because the prompt's canonical schema names it, but
this repository has no multi-tenant concept today (single deployment,
IAM/branch scope only) -- see
docs/RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md section 12. It is typed as an
optional field with no enforced meaning yet; do not build tenant isolation
logic on top of it without first confirming a real multi-tenant model
exists.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentType(str, Enum):
    PRODUCT = "product"
    LEGAL_POLICY = "legal_policy"
    OPERATIONS = "operations"
    UNDERWRITING_COMPILER = "underwriting_compiler"


class AuthorityTier(str, Enum):
    """Mirrors docs/RAG_GUARDRAIL_REQUIREMENT_EXTRACTION.md section 4 (Doc B
    mục 30.2's 5-tier source authority hierarchy)."""

    TIER_1_AUTHORITATIVE = "TIER_1_AUTHORITATIVE"
    TIER_2_VERIFIED_INTERNAL = "TIER_2_VERIFIED_INTERNAL"
    TIER_3_CUSTOMER_PROVIDED_UNVERIFIED = "TIER_3_CUSTOMER_PROVIDED_UNVERIFIED"
    TIER_4_MODEL_INFERENCE = "TIER_4_MODEL_INFERENCE"
    TIER_5_UNSUPPORTED = "TIER_5_UNSUPPORTED"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PENDING = "pending"
    REJECTED = "rejected"


class RetrievalChannel(str, Enum):
    EXACT = "exact"
    SPARSE = "sparse"
    DENSE = "dense"
    HYBRID = "hybrid"


class RetrievalStatus(str, Enum):
    OK = "ok"
    ERROR = "error"


class RetrievalErrorCode(str, Enum):
    """Extends -- does not replace -- the Phase 0 codes on
    app.knowledge.index.RetrievalOutcomeCode (INDEX_NOT_READY/EMPTY_QUERY/
    NO_RELEVANT_RESULT/OK), which stay the source of truth for
    PersistentHybridIndex itself. These additional codes describe failure
    modes above the index layer (authorization, provider availability,
    embedding failures) that no runtime code raises yet -- see the
    implementation report's Phase 1 "Error Taxonomy" section for exactly
    which of these are VERIFIED_BY_EXECUTION vs INTERFACE_ONLY."""

    NO_RELEVANT_RESULT = "no_relevant_result"
    INDEX_NOT_READY = "index_not_ready"
    EMPTY_QUERY = "empty_query"
    AUTHORIZATION_DENIED = "authorization_denied"
    SOURCE_SCOPE_EMPTY = "source_scope_empty"
    QUERY_INVALID = "query_invalid"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_TIMEOUT = "provider_timeout"
    EMBEDDING_FAILURE = "embedding_failure"
    INDEX_VERSION_MISMATCH = "index_version_mismatch"
    FILTER_CONFIGURATION_INVALID = "filter_configuration_invalid"
    EXACT_ENTITY_NOT_FOUND = "exact_entity_not_found"


class MetadataRef(BaseModel):
    """Minimal typed pointer to an entity elsewhere in the system --
    replaces passing bare (entity_type, entity_id) string pairs."""

    model_config = ConfigDict(extra="forbid")

    entity_type: str
    entity_id: str
    version: Optional[str] = None


class RetrievalRequest(BaseModel):
    """INTERFACE_ONLY -- see module docstring. Field set matches the
    prompt's canonical schema; fields this repo genuinely has no source
    for yet (tenant_id/team_id) are optional and unenforced rather than
    invented."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    trace_id: str

    actor_id: str
    actor_role: str

    tenant_id: Optional[str] = None
    branch_id: Optional[str] = None
    team_id: Optional[str] = None

    customer_id: Optional[str] = None
    case_id: Optional[str] = None

    agent_type: AgentType
    task_type: str

    raw_query: str
    normalized_query: str

    allowed_security_classifications: Optional[List[str]] = None

    exact_entity_refs: List[MetadataRef] = Field(default_factory=list)
    product_ids: List[str] = Field(default_factory=list)
    policy_ids: List[str] = Field(default_factory=list)
    process_ids: List[str] = Field(default_factory=list)
    requirement_codes: List[str] = Field(default_factory=list)

    effective_at: datetime
    retrieval_policy_id: str


class RetrievalCandidate(BaseModel):
    """INTERFACE_ONLY -- see module docstring."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str

    source_id: str
    source_version: str
    chunk_id: str

    entity_type: str
    entity_id: Optional[str] = None

    content: str
    content_hash: str

    source_type: str
    authority_tier: AuthorityTier
    verification_status: VerificationStatus

    tenant_id: Optional[str] = None
    customer_id: Optional[str] = None
    case_id: Optional[str] = None

    product_ids: List[str] = Field(default_factory=list)
    policy_ids: List[str] = Field(default_factory=list)
    process_ids: List[str] = Field(default_factory=list)
    requirement_codes: List[str] = Field(default_factory=list)

    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None

    is_superseded: bool = False
    is_quarantined: bool = False

    retrieval_channel: RetrievalChannel
    representation_type: str

    raw_score: float
    rank: int


class RetrievalPolicy(BaseModel):
    """Per-agent retrieval policy -- Phase 1 section 8. Concrete instances
    for product/legal_policy/operations live in
    app/knowledge/agent_retrieval_policies.py. Status: INTERFACE_ONLY for
    the *runtime enforcement* of this policy (nothing calls
    PersistentHybridIndex.search() with a RetrievalPolicy yet -- Product
    and Legal still pass their own hardcoded threshold, see
    docs/RAG_GUARDRAIL_CURRENT_STATE_AUDIT.md). The *data* (allowed source
    types, fail_closed, exact_lookup_first per agent) is real and asserted
    by tests -- see tests/retrieval/test_agent_retrieval_policy.py."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str
    version: str
    agent_type: AgentType

    allowed_source_types: List[str]
    minimum_authority_tier: AuthorityTier
    minimum_verification_status: VerificationStatus

    exact_lookup_first: bool
    fail_closed: bool

    allow_customer_unverified_data: bool
    allow_model_inference_sources: bool

    required_filters: List[str] = Field(default_factory=list)
    maximum_candidates: int = 30

    # Phase 2 section 9 (RRF fusion) -- per-agent weight bias. Initial
    # defaults only, not benchmark-tuned: see docs/RAG_ABLATION_REPORT.md
    # for whether these actually help vs. rrf_k=60/1.0/1.0 uniform
    # weighting on this repo's synthetic corpus before treating them as
    # optimal.
    sparse_weight: float = 1.0
    dense_weight: float = 1.0


class RetrievalDiagnostics(BaseModel):
    """Pipeline-level diagnostics -- INTERFACE_ONLY, see module docstring
    for how this differs from app.knowledge.index.RetrievalDiagnostics."""

    model_config = ConfigDict(extra="forbid")

    status: RetrievalStatus
    error_code: Optional[RetrievalErrorCode] = None

    strategy: str
    channels_executed: List[RetrievalChannel] = Field(default_factory=list)

    candidate_count_before_filter: int
    candidate_count_after_filter: int

    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    blocked_candidate_reason_counts: Dict[str, int] = Field(default_factory=dict)

    index_version: Optional[str] = None
    representation_types: List[str] = Field(default_factory=list)

    latency_ms: int


# --- Phase 2: GroundingPack / conflict / result ------------------------
#
# Named RetrievalGroundingPack (not GroundingPack) deliberately: this repo
# already has a `GroundingPack` in app/knowledge/rag_provider.py that a
# CONCURRENT agent (see AI_LOG.md) is actively coupling to its own
# MetadataEnvelope (app/metadata/models.py) as part of an unrelated
# Underwriting-Handoff workflow -- both files were uncommitted and being
# edited in real time during this Phase. Reusing/extending that class
# risked either overwriting the other agent's in-progress work or silently
# forking its meaning depending on which edit landed last. A distinctly
# named class in this module (which only the retrieval pipeline touches)
# avoids that collision entirely while remaining structurally comparable.


class SourceLocatorType(str, Enum):
    DOCUMENT_SPAN = "document_span"
    STRUCTURED_FIELD = "structured_field"


class SourceLocator(BaseModel):
    """Where inside the source a GroundingItem's content came from. Never
    fabricates a page number: a KnowledgeChunk has no page/bounding_box
    field in this repo (see app/knowledge/models.py), so document-derived
    items use section (section_path) and structured/DB-derived items use
    field_path -- both honestly reflect what is actually known."""

    model_config = ConfigDict(extra="forbid")

    type: SourceLocatorType
    section: Optional[str] = None
    field_path: Optional[str] = None


class GroundingItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grounding_item_id: str
    chunk_id: str
    source_id: str
    source_version: str
    content: str
    authority_tier: Optional[AuthorityTier] = None
    verification_status: Optional[VerificationStatus] = None
    retrieval_channel: RetrievalChannel
    fused_score: float
    source_locator: SourceLocator


class RetrievalConflict(BaseModel):
    """Phase 2 section 14 MVP: detects two currently-eligible chunks that
    share an identity key (same product_id + section_path, i.e. the same
    logical slot in the corpus) but disagree in content -- NOT the full
    structured-fact conflict detection the prompt describes (e.g. "CRM
    employee_count=500 vs Document employee_count=430"), which needs a
    structured fact store (subject/field_name/value) this repo does not
    have. See app/knowledge/conflict_detection.py module docstring."""

    model_config = ConfigDict(extra="forbid")

    conflict_id: str
    chunk_id_a: str
    chunk_id_b: str
    reason: str
    requires_human_review: bool = True


class MissingInformation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    requested_filters: Dict[str, Any] = Field(default_factory=dict)


class UnavailableSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    reason: str


class RetrievalGroundingPack(BaseModel):
    """Immutable (by convention -- Pydantic does not enforce immutability
    at the Python level, callers must not mutate a pack after construction)
    record of exactly what evidence a retrieval run produced, pinned by
    content_hash so a downstream claim/citation validator can detect if it
    is being checked against a pack that was tampered with or regenerated."""

    model_config = ConfigDict(extra="forbid")

    grounding_pack_id: str
    retrieval_run_id: str
    agent_type: AgentType
    request_ref: MetadataRef

    items: List[GroundingItem] = Field(default_factory=list)
    conflicts: List[RetrievalConflict] = Field(default_factory=list)
    missing_information: List[MissingInformation] = Field(default_factory=list)
    unavailable_sources: List[UnavailableSource] = Field(default_factory=list)

    content_hash: str
    created_at: datetime


class ControlledRetrievalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagnostics: RetrievalDiagnostics
    grounding_pack: Optional[RetrievalGroundingPack] = None
