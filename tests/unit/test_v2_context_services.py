"""V2-002 unit/RBAC/context tests (plan_v2/14_BUILD_ORDER.md required tests column).

Covers the subset of plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md section 10 that
is actually in V2-002's scope (per-source services: RBAC, freshness,
failure/fallback). Cross-source merge/precedence/conflict/minimization tests
from that list belong to V2-003 (Context Assembler) and are not claimed here.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.context.conversation_state import ConversationStateService, ConversationStateStore
from app.context.customer_service import CustomerContextService
from app.context.employee_service import EmployeeContextService
from app.context.freshness import DEFAULT_POLICIES, get_policy
from app.context.workspace_service import WorkspaceContextService, WorkspaceSessionStore
from app.integrations.enterprise import SQLiteCRMAdapter
from app.integrations.errors import ContextAccessDeniedError, UpstreamTimeoutError, UpstreamUnavailableError
from app.integrations.enterprise import SQLiteIAMAdapter
from app.integrations.enterprise import SQLiteSSOAdapter
from app.schemas.v2.context_snapshot import ContextSnapshot, Employee
from app.schemas.v2.json_schema_loader import validate_instance

CORRELATION_ID = "trace-test-1"


# --- Employee context: identity + permissions, IAM fail-closed --------------


def test_employee_service_returns_identity_and_permissions():
    service = EmployeeContextService(SQLiteSSOAdapter(), SQLiteIAMAdapter())
    employee = service.get("RM-999", correlation_id=CORRELATION_ID)

    assert employee.employee_id == "RM-999"
    assert employee.role == "RM"
    assert "case:write" in employee.permissions
    assert "COMP-ABC" in employee.access_scope["managed_customer_ids"]


def test_employee_service_fails_closed_on_iam_timeout():
    service = EmployeeContextService(SQLiteSSOAdapter(), SQLiteIAMAdapter(fail_for={"RM-999"}))

    with pytest.raises(UpstreamTimeoutError) as exc_info:
        service.get("RM-999", correlation_id=CORRELATION_ID)
    assert exc_info.value.error_code == "IAM_TIMEOUT"
    assert exc_info.value.retryable is True


def test_employee_service_fails_closed_on_sso_timeout():
    service = EmployeeContextService(SQLiteSSOAdapter(fail_for={"RM-999"}), SQLiteIAMAdapter())

    with pytest.raises(UpstreamTimeoutError):
        service.get("RM-999", correlation_id=CORRELATION_ID)


def test_employee_service_unknown_employee_raises_unavailable():
    service = EmployeeContextService(SQLiteSSOAdapter(), SQLiteIAMAdapter())

    with pytest.raises(UpstreamUnavailableError):
        service.get("RM-DOES-NOT-EXIST", correlation_id=CORRELATION_ID)


# --- Workspace context: realtime session read --------------------------------


def test_workspace_service_round_trips_full_session():
    store = WorkspaceSessionStore()
    store.set_session(
        "SESS-1",
        current_screen="case_detail",
        selected_customer_id="COMP-ABC",
        active_case_id="CASE-1",
        active_task_id="T1",
        selected_product_ids=["PROD-PAYROLL"],
    )
    workspace = WorkspaceContextService(store).get("SESS-1", correlation_id=CORRELATION_ID)

    assert workspace.selected_customer_id == "COMP-ABC"
    assert workspace.selected_product_ids == ["PROD-PAYROLL"]


def test_workspace_service_minimal_session_uses_schema_defaults():
    store = WorkspaceSessionStore()
    store.set_session("SESS-2", current_screen="inbox")
    workspace = WorkspaceContextService(store).get("SESS-2", correlation_id=CORRELATION_ID)

    assert workspace.selected_customer_id is None
    assert workspace.selected_product_ids == []


def test_workspace_service_unknown_session_raises():
    with pytest.raises(UpstreamUnavailableError):
        WorkspaceContextService(WorkspaceSessionStore()).get("SESS-MISSING", correlation_id=CORRELATION_ID)


# --- Customer context: RBAC + stale/cache fallback (the V2-002 required tests) -


def _rm_999() -> Employee:
    return EmployeeContextService(SQLiteSSOAdapter(), SQLiteIAMAdapter()).get("RM-999", correlation_id=CORRELATION_ID)


def _rm_001() -> Employee:
    return EmployeeContextService(SQLiteSSOAdapter(), SQLiteIAMAdapter()).get("RM-001", correlation_id=CORRELATION_ID)


def test_customer_service_returns_fresh_profile_for_managed_customer():
    service = CustomerContextService(SQLiteCRMAdapter())
    customer = service.get("COMP-ABC", employee=_rm_999(), correlation_id=CORRELATION_ID)

    assert customer.customer_id == "COMP-ABC"
    assert customer.stale is False
    assert customer.attributes["employees_count"] == 500


def test_customer_service_unauthorized_customer_rejected():
    """plan_v2/04_EMPLOYEE_WORKSPACE_CONTEXT.md section 3: unauthorized
    selected customer stops with CONTEXT_ACCESS_DENIED, no fallback."""
    service = CustomerContextService(SQLiteCRMAdapter())

    with pytest.raises(ContextAccessDeniedError) as exc_info:
        service.get("COMP-ABC", employee=_rm_001(), correlation_id=CORRELATION_ID)
    assert exc_info.value.error_code == "CONTEXT_ACCESS_DENIED"
    assert exc_info.value.retryable is False


def test_customer_service_no_customer_selected_returns_stale_empty():
    service = CustomerContextService(SQLiteCRMAdapter())
    customer = service.get(None, employee=_rm_999(), correlation_id=CORRELATION_ID)

    assert customer.customer_id is None
    assert customer.stale is True


def test_customer_service_uses_fresh_cache_on_crm_timeout():
    crm = SQLiteCRMAdapter()
    service = CustomerContextService(crm)
    employee = _rm_999()

    warm = service.get("COMP-ABC", employee=employee, correlation_id=CORRELATION_ID)
    assert warm.stale is False

    crm._fail_for.add("COMP-ABC")  # simulate CRM going down after the first successful call
    fallback = service.get("COMP-ABC", employee=employee, correlation_id=CORRELATION_ID)

    assert fallback.stale is False, "cache within TTL must be served as fresh"
    assert fallback.attributes == warm.attributes


def test_customer_service_marks_expired_cache_as_stale_on_crm_timeout():
    crm = SQLiteCRMAdapter()
    service = CustomerContextService(crm)
    employee = _rm_999()
    service.get("COMP-ABC", employee=employee, correlation_id=CORRELATION_ID)

    # Force the cached entry to look older than the customer freshness TTL (5m).
    profile, _ = service._cache["COMP-ABC"]
    service._cache["COMP-ABC"] = (profile, datetime.now(timezone.utc) - timedelta(hours=1))
    crm._fail_for.add("COMP-ABC")

    stale_result = service.get("COMP-ABC", employee=employee, correlation_id=CORRELATION_ID)
    assert stale_result.stale is True


def test_customer_service_no_cache_on_crm_timeout_marks_stale_and_empty():
    crm = SQLiteCRMAdapter(fail_for={"COMP-ABC"})
    service = CustomerContextService(crm)

    result = service.get("COMP-ABC", employee=_rm_999(), correlation_id=CORRELATION_ID)
    assert result.stale is True
    assert result.attributes == {}


# --- Conversation context: corrupt-state recovery -----------------------------


def test_conversation_service_returns_clean_state_when_absent():
    conversation = ConversationStateService(ConversationStateStore()).get("CASE-1", correlation_id=CORRELATION_ID)
    assert conversation.current_goal is None
    assert conversation.confirmed_facts == {}


def test_conversation_service_round_trips_valid_state():
    store = ConversationStateStore()
    store.set_raw(
        "CASE-1",
        {
            "current_goal": "open payroll",
            "confirmed_facts": {},
            "rejected_assumptions": [],
            "open_questions": ["BCTC?"],
        },
    )
    conversation = ConversationStateService(store).get("CASE-1", correlation_id=CORRELATION_ID)
    assert conversation.current_goal == "open payroll"
    assert conversation.open_questions == ["BCTC?"]


def test_conversation_service_recovers_from_corrupt_state(caplog):
    store = ConversationStateStore()
    store.set_raw("CASE-1", {"current_goal": 12345, "confirmed_facts": "not-a-dict"})  # wrong types

    with caplog.at_level("WARNING"):
        conversation = ConversationStateService(store).get("CASE-1", correlation_id=CORRELATION_ID)

    assert conversation.current_goal is None
    assert conversation.confirmed_facts == {}
    assert any("conversation_state_corrupt" in record.message for record in caplog.records)


# --- Freshness policy ----------------------------------------------------------


def test_freshness_policy_flags_stale_and_fresh_correctly():
    policy = DEFAULT_POLICIES["customer"]
    now = datetime.now(timezone.utc)

    assert policy.is_stale(now - timedelta(minutes=1), now=now) is False
    assert policy.is_stale(now - timedelta(minutes=10), now=now) is True


def test_freshness_policy_missing_for_realtime_layers():
    with pytest.raises(KeyError):
        get_policy("workspace")
    with pytest.raises(KeyError):
        get_policy("conversation")


# --- Composability with the V2-001 contract (integration with upstream port) --


def test_services_compose_into_a_contract_valid_context_snapshot():
    """Proves the four V2-002 services produce pieces that, once assembled
    by hand here, satisfy the V2-001 ContextSnapshot contract end to end.
    The real merge/precedence/minimization logic is V2-003's job; this test
    only checks the *shape* these services hand off is composable."""
    employee = _rm_999()

    workspace_store = WorkspaceSessionStore()
    workspace_store.set_session("SESS-1", current_screen="case_detail", selected_customer_id="COMP-ABC")
    workspace = WorkspaceContextService(workspace_store).get("SESS-1", correlation_id=CORRELATION_ID)

    customer = CustomerContextService(SQLiteCRMAdapter()).get(
        workspace.selected_customer_id, employee=employee, correlation_id=CORRELATION_ID
    )
    conversation = ConversationStateService(ConversationStateStore()).get("CASE-1", correlation_id=CORRELATION_ID)

    snapshot = ContextSnapshot(
        employee=employee,
        workspace=workspace,
        customer=customer,
        conversation=conversation,
        documents=[],
        conflicts=[],
        assembled_at=datetime.now(timezone.utc),
    )

    validate_instance(snapshot.model_dump(mode="json"), "context_snapshot.schema.json")
