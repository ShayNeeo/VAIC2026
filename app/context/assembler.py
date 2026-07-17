"""Context Assembler: merge, minimize, provenance (V2-003).

plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md section 3 (collection sequence),
section 4 (precedence rules), section 5 (conflict model), section 6
(minimization). Depends on the V2-002 per-source services; does not talk to
app/integrations directly.

Scope note: precedence tier 1 ("user_explicit in the new message") requires
parsed entities that only the Intent Extractor (V2-004) produces, which runs
*after* this assembler. `resolve_precedence()` still implements the full
ladder and honors user_explicit candidates when a caller supplies them (see
`user_explicit` param on `assemble()`), but no caller does yet -- this is a
forward-compatible hook, not a completed integration. See plan_v2/PROGRESS.md
V2-003 notes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional

from app.context.conflicts import build_conflict
from app.context.conversation_state import ConversationStateService
from app.context.customer_service import CustomerContextService
from app.context.employee_service import EmployeeContextService
from app.context.workspace_service import WorkspaceContextService
from app.schemas.v2.common import ResolvedValue, SourceType
from app.schemas.v2.context_snapshot import Conflict, Conversation, ContextSnapshot, WorkspaceDocument

# plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md section 4, tiers 1-6. The IAM/permission
# exception in that section does not apply here: access_scope/permissions never
# flow through this resolver, they come straight from EmployeeContextService.
_PRECEDENCE_ORDER: List[SourceType] = [
    SourceType.USER_EXPLICIT,
    SourceType.WORKSPACE,
    SourceType.CRM,
    SourceType.DOCUMENT,
    SourceType.WORKFLOW,
    SourceType.CONVERSATION_CONFIRMED,
    SourceType.CACHE,
    SourceType.LLM_INFERENCE,
]
_FRESHNESS_GATED_TIERS = {SourceType.CRM, SourceType.DOCUMENT, SourceType.WORKFLOW}


def _is_expired(candidate: ResolvedValue, *, now: datetime) -> bool:
    return candidate.expires_at is not None and candidate.expires_at <= now


def resolve_precedence(candidates: Iterable[ResolvedValue], *, now: Optional[datetime] = None) -> Optional[ResolvedValue]:
    """Pick the winning value for one field out of same-field candidates.

    Tiers CRM/DOCUMENT/WORKFLOW are only eligible while unexpired ("con
    fresh"); an expired candidate at that tier is skipped, falling through to
    the next tier rather than being returned stale.
    """
    reference = now or datetime.now(timezone.utc)
    pool = list(candidates)
    if not pool:
        return None
    for tier in _PRECEDENCE_ORDER:
        tier_candidates = [c for c in pool if c.source_type == tier]
        if not tier_candidates:
            continue
        if tier in _FRESHNESS_GATED_TIERS:
            tier_candidates = [c for c in tier_candidates if not _is_expired(c, now=reference)]
            if not tier_candidates:
                continue
        return tier_candidates[0]
    return pool[0]


def _clean_conversation() -> Conversation:
    return Conversation(current_goal=None, confirmed_facts={}, rejected_assumptions=[], open_questions=[])


class ContextAssembler:
    def __init__(
        self,
        employee_service: EmployeeContextService,
        workspace_service: WorkspaceContextService,
        customer_service: CustomerContextService,
        conversation_service: ConversationStateService,
    ) -> None:
        self._employee = employee_service
        self._workspace = workspace_service
        self._customer = customer_service
        self._conversation = conversation_service

    def assemble(
        self,
        *,
        employee_id: str,
        session_id: str,
        documents: Iterable[Mapping[str, Any]] = (),
        user_explicit: Optional[Mapping[str, ResolvedValue]] = None,
        correlation_id: str,
    ) -> ContextSnapshot:
        """plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md section 3 sequence.

        Raises app.integrations.errors.ContextAccessDeniedError (propagated
        from CustomerContextService, no fallback) if the workspace-selected
        customer is outside the employee's scope.
        """
        employee = self._employee.get(employee_id, correlation_id=correlation_id)
        workspace = self._workspace.get(session_id, correlation_id=correlation_id)
        customer = self._customer.get(
            workspace.selected_customer_id, employee=employee, correlation_id=correlation_id
        )
        conversation = (
            self._conversation.get(workspace.active_case_id, correlation_id=correlation_id)
            if workspace.active_case_id
            else _clean_conversation()
        )
        parsed_documents = [WorkspaceDocument.model_validate(doc) for doc in documents]
        conflicts = self._detect_conflicts(workspace_customer_id=workspace.selected_customer_id, conversation=conversation, user_explicit=user_explicit or {})

        return ContextSnapshot(
            employee=employee,
            workspace=workspace,
            customer=customer,
            conversation=conversation,
            documents=parsed_documents,
            conflicts=conflicts,
            assembled_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _detect_conflicts(
        *,
        workspace_customer_id: Optional[str],
        conversation: Conversation,
        user_explicit: Mapping[str, ResolvedValue],
    ) -> List[Conflict]:
        conflicts: List[Conflict] = []

        candidates: List[ResolvedValue] = []
        if workspace_customer_id is not None:
            candidates.append(
                ResolvedValue(
                    value=workspace_customer_id,
                    source_type=SourceType.WORKSPACE,
                    source_id="selected_customer_id",
                    confidence=1.0,
                    confirmed=True,
                    observed_at=datetime.now(timezone.utc),
                )
            )
        confirmed_customer = conversation.confirmed_facts.get("customer_id")
        if confirmed_customer is not None:
            candidates.append(confirmed_customer)
        explicit_customer = user_explicit.get("customer_id")
        if explicit_customer is not None:
            candidates.append(explicit_customer)

        conflict = build_conflict("customer_id", candidates)
        if conflict is not None:
            conflicts.append(conflict)
        return conflicts


def minimize_for_llm(snapshot: ContextSnapshot) -> Dict[str, Any]:
    """plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md section 6: structured summary
    only. Excludes the RM's full managed-customer list, permissions/raw
    identity, and anything not needed for the current intent taxonomy.
    """
    return {
        "employee": {
            "employee_id": snapshot.employee.employee_id,
            "role": snapshot.employee.role,
            "organization_unit": snapshot.employee.organization_unit,
        },
        "workspace": {
            "current_screen": snapshot.workspace.current_screen,
            "selected_customer_id": snapshot.workspace.selected_customer_id,
            "active_case_id": snapshot.workspace.active_case_id,
            "active_task_id": snapshot.workspace.active_task_id,
            "selected_product_ids": list(snapshot.workspace.selected_product_ids),
        },
        "customer": {
            "customer_id": snapshot.customer.customer_id,
            "profile_version": snapshot.customer.profile_version,
            "stale": snapshot.customer.stale,
            "attributes": dict(snapshot.customer.attributes),
        },
        "conversation": {
            "current_goal": snapshot.conversation.current_goal,
            "confirmed_facts": {key: value.value for key, value in snapshot.conversation.confirmed_facts.items()},
            "open_questions": list(snapshot.conversation.open_questions),
        },
        "documents": [
            {"document_id": doc.document_id, "document_type": doc.document_type, "status": doc.status.value}
            for doc in snapshot.documents
        ],
        "conflicts": [
            {"field": c.field, "decision_impact": c.decision_impact.value, "requires_confirmation": c.requires_confirmation}
            for c in snapshot.conflicts
        ],
    }
