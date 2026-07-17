"""V2 domain models mirroring plan_v2/contracts/*.json (schema_version 2.0.0).

Contracts are the source of truth (plan_v2/03_SHARED_CONTRACTS.md). These
Pydantic models exist to give app code type-checked construction/validation
that stays consistent with the JSON Schema files under plan_v2/contracts/,
verified by tests/contract/test_v2_contracts.py.

This package is additive: app/schemas/state.py (V1) is untouched, and no V1
code imports from here yet (plan_v2/14_BUILD_ORDER.md section 7).
"""

from .common import SCHEMA_VERSION, DecisionImpact, ResolvedValue, SourceType
from .context_snapshot import (
    Conflict,
    ContextSnapshot,
    Conversation,
    Customer,
    DocumentStatus,
    Employee,
    Workspace,
    WorkspaceDocument,
)
from .data_source_card import DataSourceCard, LifecycleStatus as DataSourceLifecycleStatus
from .intent_result import Ambiguity, EvidenceSpan, IntentResult, RecommendedAction
from .intake import (
    CustomerBusinessSnapshot,
    DocumentJobStatus,
    ExtractedField,
    FieldConflict,
    FieldValidationStatus,
    IntakeDocument,
    IntakeSession,
    IntakeStatus,
    ProfileChange,
)
from .planning import ExecutionPlan, NextBestAction, NextBestQuestion, PlanStep
from .shared_case_state import (
    Approval,
    ApprovalStatus,
    CaseStatus,
    Evidence,
    Request,
    SharedCaseState,
    Task,
    TaskStatus,
    Workflow,
)
from .tool_contracts import ActionInput, ActionOutput, ToolRegistry, ToolRisk, ToolSpec, load_tool_registry

__all__ = [
    "SCHEMA_VERSION",
    "DecisionImpact",
    "ResolvedValue",
    "SourceType",
    "Conflict",
    "ContextSnapshot",
    "Conversation",
    "Customer",
    "DocumentStatus",
    "Employee",
    "Workspace",
    "WorkspaceDocument",
    "DataSourceCard",
    "DataSourceLifecycleStatus",
    "Ambiguity",
    "EvidenceSpan",
    "IntentResult",
    "RecommendedAction",
    "CustomerBusinessSnapshot",
    "DocumentJobStatus",
    "ExtractedField",
    "FieldConflict",
    "FieldValidationStatus",
    "IntakeDocument",
    "IntakeSession",
    "IntakeStatus",
    "ProfileChange",
    "ExecutionPlan",
    "NextBestAction",
    "NextBestQuestion",
    "PlanStep",
    "Approval",
    "ApprovalStatus",
    "CaseStatus",
    "Evidence",
    "Request",
    "SharedCaseState",
    "Task",
    "TaskStatus",
    "Workflow",
    "ActionInput",
    "ActionOutput",
    "ToolRegistry",
    "ToolRisk",
    "ToolSpec",
    "load_tool_registry",
]
