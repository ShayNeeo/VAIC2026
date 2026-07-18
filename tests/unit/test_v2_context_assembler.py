"""V2-003 Context Assembler tests (plan_v2/14_BUILD_ORDER.md: isolation/stale tests).

Scope matches plan_v2/PROGRESS.md V2-003 notes: merge/precedence, conflict
detection for sources this assembler actually has (workspace vs previously
confirmed conversation fact), minimization, and cross-case isolation. Intent-
driven conflicts (user explicitly names a different customer in the new
message) are out of scope until V2-004 exists.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.context.assembler import ContextAssembler, minimize_for_llm, resolve_precedence
from app.context.conversation_state import ConversationStateService, ConversationStateStore
from app.context.customer_service import CustomerContextService
from app.context.employee_service import EmployeeContextService
from app.context.workspace_service import WorkspaceContextService, WorkspaceSessionStore
from app.integrations.enterprise import SQLiteCRMAdapter
from app.integrations.errors import ContextAccessDeniedError
from app.integrations.enterprise import SQLiteIAMAdapter
from app.integrations.enterprise import SQLiteSSOAdapter
from app.schemas.v2.common import ResolvedValue, SourceType
from app.schemas.v2.json_schema_loader import validate_instance

CORRELATION_ID = "trace-assembler-1"


def _resolved(value, source_type: SourceType, *, expires_at=None) -> ResolvedValue:
    return ResolvedValue(
        value=value,
        source_type=source_type,
        source_id="test",
        confidence=1.0,
        confirmed=True,
        observed_at=datetime.now(timezone.utc),
        expires_at=expires_at,
    )


def _new_assembler(workspace_store=None, conversation_store=None, crm_fail_for=None):
    workspace_store = workspace_store or WorkspaceSessionStore()
    conversation_store = conversation_store or ConversationStateStore()
    return ContextAssembler(
        employee_service=EmployeeContextService(SQLiteSSOAdapter(), SQLiteIAMAdapter()),
        workspace_service=WorkspaceContextService(workspace_store),
        customer_service=CustomerContextService(SQLiteCRMAdapter(fail_for=crm_fail_for)),
        conversation_service=ConversationStateService(conversation_store),
    ), workspace_store, conversation_store


# --- Happy path / contract validity ------------------------------------------


def test_assemble_produces_contract_valid_snapshot():
    assembler, workspace_store, _ = _new_assembler()
    workspace_store.set_session("SESS-1", current_screen="case_detail", selected_customer_id="COMP-ABC", active_case_id="CASE-1")

    snapshot = assembler.assemble(employee_id="RM-999", session_id="SESS-1", correlation_id=CORRELATION_ID)

    assert snapshot.customer.customer_id == "COMP-ABC"
    assert snapshot.customer.stale is False
    validate_instance(snapshot.model_dump(mode="json"), "context_snapshot.schema.json")


def test_assemble_with_documents_parses_them_into_snapshot():
    assembler, workspace_store, _ = _new_assembler()
    workspace_store.set_session("SESS-1", current_screen="case_detail", selected_customer_id="COMP-ABC")

    snapshot = assembler.assemble(
        employee_id="RM-999",
        session_id="SESS-1",
        documents=[
            {
                "document_id": "DOC-1",
                "document_type": "business_registration",
                "version": "1",
                "status": "verified",
                "access_scope": {},
            }
        ],
        correlation_id=CORRELATION_ID,
    )

    assert len(snapshot.documents) == 1
    assert snapshot.documents[0].document_id == "DOC-1"


# --- RBAC end-to-end -----------------------------------------------------------


def test_assemble_denies_unauthorized_customer_no_fallback():
    assembler, workspace_store, _ = _new_assembler()
    workspace_store.set_session("SESS-1", current_screen="case_detail", selected_customer_id="COMP-ABC")

    with pytest.raises(ContextAccessDeniedError):
        assembler.assemble(employee_id="RM-001", session_id="SESS-1", correlation_id=CORRELATION_ID)


# --- Stale propagation -----------------------------------------------------------


def test_assemble_marks_customer_stale_when_crm_down_and_no_cache():
    assembler, workspace_store, _ = _new_assembler(crm_fail_for={"COMP-ABC"})
    workspace_store.set_session("SESS-1", current_screen="case_detail", selected_customer_id="COMP-ABC")

    snapshot = assembler.assemble(employee_id="RM-999", session_id="SESS-1", correlation_id=CORRELATION_ID)

    assert snapshot.customer.stale is True
    validate_instance(snapshot.model_dump(mode="json"), "context_snapshot.schema.json")


# --- Conflict detection ----------------------------------------------------------


def test_assemble_detects_conflict_between_workspace_and_confirmed_fact():
    assembler, workspace_store, conversation_store = _new_assembler()
    workspace_store.set_session("SESS-1", current_screen="case_detail", selected_customer_id="COMP-ABC", active_case_id="CASE-1")
    conversation_store.set_raw(
        "CASE-1",
        {
            "current_goal": None,
            "confirmed_facts": {
                "customer_id": {
                    "value": "COMP-XYZ",
                    "source_type": "conversation_confirmed",
                    "source_id": "prior_turn",
                    "confidence": 1.0,
                    "confirmed": True,
                    "observed_at": "2026-07-17T09:00:00Z",
                }
            },
            "rejected_assumptions": [],
            "open_questions": [],
        },
    )

    snapshot = assembler.assemble(employee_id="RM-999", session_id="SESS-1", correlation_id=CORRELATION_ID)

    assert len(snapshot.conflicts) == 1
    conflict = snapshot.conflicts[0]
    assert conflict.field == "customer_id"
    assert conflict.decision_impact == "high"
    assert conflict.requires_confirmation is True
    assert {c.value for c in conflict.candidate_values} == {"COMP-ABC", "COMP-XYZ"}


def test_assemble_no_conflict_when_workspace_and_confirmed_fact_agree():
    assembler, workspace_store, conversation_store = _new_assembler()
    workspace_store.set_session("SESS-1", current_screen="case_detail", selected_customer_id="COMP-ABC", active_case_id="CASE-1")
    conversation_store.set_raw(
        "CASE-1",
        {
            "current_goal": None,
            "confirmed_facts": {
                "customer_id": {
                    "value": "COMP-ABC",
                    "source_type": "conversation_confirmed",
                    "source_id": "prior_turn",
                    "confidence": 1.0,
                    "confirmed": True,
                    "observed_at": "2026-07-17T09:00:00Z",
                }
            },
            "rejected_assumptions": [],
            "open_questions": [],
        },
    )

    snapshot = assembler.assemble(employee_id="RM-999", session_id="SESS-1", correlation_id=CORRELATION_ID)
    assert snapshot.conflicts == []


# --- Cross-case isolation (the V2-003 "Done when": no cross-case leakage) ------


def test_no_cross_case_leakage_across_sequential_assembles():
    assembler, workspace_store, conversation_store = _new_assembler()

    workspace_store.set_session("SESS-A", current_screen="case_detail", selected_customer_id="COMP-ABC", active_case_id="CASE-A")
    conversation_store.set_raw(
        "CASE-A",
        {"current_goal": "payroll for ABC", "confirmed_facts": {}, "rejected_assumptions": [], "open_questions": ["ubo?"]},
    )
    snapshot_a = assembler.assemble(employee_id="RM-999", session_id="SESS-A", correlation_id=CORRELATION_ID)

    workspace_store.set_session("SESS-B", current_screen="case_detail", selected_customer_id="COMP-XYZ", active_case_id="CASE-B")
    conversation_store.set_raw(
        "CASE-B",
        {"current_goal": "cash management for XYZ", "confirmed_facts": {}, "rejected_assumptions": [], "open_questions": []},
    )
    snapshot_b = assembler.assemble(employee_id="RM-999", session_id="SESS-B", correlation_id=CORRELATION_ID)

    assert snapshot_a.customer.customer_id == "COMP-ABC"
    assert snapshot_b.customer.customer_id == "COMP-XYZ"
    assert snapshot_a.conversation.current_goal == "payroll for ABC"
    assert snapshot_b.conversation.current_goal == "cash management for XYZ"
    assert "ubo?" not in snapshot_b.conversation.open_questions
    assert snapshot_a.customer.attributes != snapshot_b.customer.attributes
    # Re-fetching case A after assembling case B must still return case A's own data.
    snapshot_a_again = assembler.assemble(employee_id="RM-999", session_id="SESS-A", correlation_id=CORRELATION_ID)
    assert snapshot_a_again.conversation.current_goal == "payroll for ABC"
    assert snapshot_a_again.customer.customer_id == "COMP-ABC"


# --- Precedence resolver (pure function) ----------------------------------------


def test_resolve_precedence_empty_returns_none():
    assert resolve_precedence([]) is None


def test_resolve_precedence_workspace_beats_conversation_confirmed():
    winner = resolve_precedence(
        [_resolved("COMP-XYZ", SourceType.CONVERSATION_CONFIRMED), _resolved("COMP-ABC", SourceType.WORKSPACE)]
    )
    assert winner.value == "COMP-ABC"


def test_resolve_precedence_user_explicit_beats_everything():
    winner = resolve_precedence(
        [
            _resolved("COMP-XYZ", SourceType.WORKSPACE),
            _resolved("COMP-CACHE", SourceType.CACHE),
            _resolved("COMP-EXPLICIT", SourceType.USER_EXPLICIT),
        ]
    )
    assert winner.value == "COMP-EXPLICIT"


def test_resolve_precedence_expired_crm_falls_through_to_conversation_confirmed():
    now = datetime.now(timezone.utc)
    winner = resolve_precedence(
        [
            _resolved("FROM-CRM-EXPIRED", SourceType.CRM, expires_at=now - timedelta(minutes=1)),
            _resolved("FROM-CONVERSATION", SourceType.CONVERSATION_CONFIRMED),
        ],
        now=now,
    )
    assert winner.value == "FROM-CONVERSATION"


def test_resolve_precedence_fresh_crm_wins_over_conversation_confirmed():
    now = datetime.now(timezone.utc)
    winner = resolve_precedence(
        [
            _resolved("FROM-CRM-FRESH", SourceType.CRM, expires_at=now + timedelta(minutes=5)),
            _resolved("FROM-CONVERSATION", SourceType.CONVERSATION_CONFIRMED),
        ],
        now=now,
    )
    assert winner.value == "FROM-CRM-FRESH"


# --- Minimization -----------------------------------------------------------------


def test_minimize_for_llm_excludes_forbidden_fields_and_keeps_needed_ones():
    assembler, workspace_store, _ = _new_assembler()
    workspace_store.set_session("SESS-1", current_screen="case_detail", selected_customer_id="COMP-ABC")
    snapshot = assembler.assemble(employee_id="RM-999", session_id="SESS-1", correlation_id=CORRELATION_ID)

    minimized = minimize_for_llm(snapshot)

    assert "access_scope" not in minimized["employee"]
    assert "permissions" not in minimized["employee"]
    assert minimized["employee"]["employee_id"] == "RM-999"
    assert minimized["customer"]["customer_id"] == "COMP-ABC"
    assert minimized["workspace"]["selected_customer_id"] == "COMP-ABC"
