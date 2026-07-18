"""Pydantic mirror of plan_v2/contracts/data_source_card.schema.json.

plan_v2/INDEX.md section 7: "Khong source nao vao serving/RAG/rules neu thieu
valid Data Source Card, owner, license/purpose, quality gate va lineage." This
model is what a source must satisfy before ingestion/retrieval code may use it.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import SCHEMA_VERSION


class DataDomain(str, Enum):
    EMPLOYEE = "employee"
    WORKSPACE = "workspace"
    CUSTOMER = "customer"
    DOCUMENT = "document"
    PRODUCT = "product"
    LEGAL = "legal"
    CREDIT = "credit"
    INSURANCE = "insurance"
    KYC_AML = "kyc_aml"
    MARKET = "market"
    OPERATIONS = "operations"
    EVALUATION = "evaluation"


class DataTier(str, Enum):
    A_INTERNAL = "A_INTERNAL"
    A_OFFICIAL = "A_OFFICIAL"
    B_LICENSED = "B_LICENSED"
    C_OPEN = "C_OPEN"
    D_DERIVED = "D_DERIVED"
    E_SYNTHETIC = "E_SYNTHETIC"


class DecisionRole(str, Enum):
    AUTHORITATIVE = "AUTHORITATIVE"
    VERIFICATION = "VERIFICATION"
    ENRICHMENT = "ENRICHMENT"
    DISCOVERY = "DISCOVERY"
    EVALUATION_ONLY = "EVALUATION_ONLY"


class AccessMethod(str, Enum):
    API = "API"
    FILE = "FILE"
    DATABASE = "DATABASE"
    EVENT = "EVENT"
    WEB_UI = "WEB_UI"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    MANUAL = "MANUAL"


class Sensitivity(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    PII = "PII"
    SENSITIVE_PII = "SENSITIVE_PII"
    RESTRICTED = "RESTRICTED"


class StaleBehavior(str, Enum):
    ALLOW_WITH_WARNING = "ALLOW_WITH_WARNING"
    BLOCK_DECISION = "BLOCK_DECISION"
    FAIL_CLOSED = "FAIL_CLOSED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class LifecycleStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ASSESSED = "ASSESSED"
    APPROVED = "APPROVED"
    SHADOW = "SHADOW"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    DEPRECATED = "DEPRECATED"
    DELETED = "DELETED"


class Owner(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_owner: str
    data_steward: str
    technical_owner: Optional[str] = None
    contact: Optional[str] = None


class Purpose(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed_uses: List[str] = Field(min_length=1)
    prohibited_uses: List[str] = Field(default_factory=list)


class Access(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: AccessMethod
    endpoint_or_location: Optional[str] = None
    authentication: str
    sandbox_available: bool
    quota: Optional[str] = None
    sla: Optional[str] = None


class Governance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    legal_basis_or_license: str
    terms_url: Optional[str] = None
    sensitivity: Sensitivity
    retention: str
    residency: str
    cross_border: bool = False
    approved: bool
    approval_reference: Optional[str] = None


class Freshness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    update_cadence: str
    max_age_seconds: int = Field(ge=0)
    stale_behavior: StaleBehavior


class Identifiers(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_key: str
    join_keys: List[str] = Field(default_factory=list)
    canonical_internal_id: Optional[str] = None


class Quality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_checks: List[str] = Field(min_length=1)
    publish_gate: str
    last_report_reference: Optional[str] = None


class Lineage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ingestion_job: str
    raw_location: str
    silver_location: Optional[str] = None
    gold_location: Optional[str] = None
    consumer_artifacts: List[str] = Field(default_factory=list)


class DataSourceCard(BaseModel):
    """contracts/data_source_card.schema.json"""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION, pattern=r"^2\.0\.0$")
    source_id: str = Field(min_length=3)
    name: str = Field(min_length=1)
    domain: DataDomain
    tier: DataTier
    provider: Optional[str] = None
    dataset_version: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    owner: Owner
    purpose: Purpose
    decision_role: DecisionRole
    access: Access
    governance: Governance
    freshness: Freshness
    identifiers: Identifiers
    quality: Quality
    lineage: Lineage
    lifecycle_status: LifecycleStatus
    risks_and_notes: List[str] = Field(default_factory=list)

    def is_usable_for_serving(self) -> bool:
        """plan_v2/INDEX.md section 7 gate: owner+purpose+quality+lineage+approval."""
        return bool(
            self.governance.approved
            and self.quality.required_checks
            and self.lineage.raw_location
            and self.lifecycle_status in {LifecycleStatus.ACTIVE, LifecycleStatus.SHADOW}
        )
