"""V2-001 contract tests.

Implements exactly the 8 required categories from
plan_v2/03_SHARED_CONTRACTS.md section 7, applied to the shared_case_state,
context_snapshot and intent_result contracts, plus the tool_contracts
actionInput/actionOutput fragment and the data_source_card contract added in
module 18. Every test asserts BOTH the Pydantic model and the raw JSON Schema
(plan_v2/contracts/*.json, the source of truth) agree on the same payload,
which is what "Done when: JSON/Pydantic/API examples dong nhat" requires.
"""

from __future__ import annotations

import copy
from typing import Any, Dict

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError
from pydantic import ValidationError as PydanticValidationError

from app.schemas.v2 import examples as ex
from app.schemas.v2.context_snapshot import ContextSnapshot
from app.schemas.v2.data_source_card import DataSourceCard
from app.schemas.v2.intent_result import IntentResult
from app.schemas.v2.json_schema_loader import action_input_schema, validate_instance
from app.schemas.v2.shared_case_state import SharedCaseState
from app.schemas.v2.tool_contracts import ActionInput, load_tool_registry

MODEL_CASES = [
    pytest.param(ContextSnapshot, ex.MINIMAL_CONTEXT_SNAPSHOT, "context_snapshot.schema.json", id="context-minimal"),
    pytest.param(ContextSnapshot, ex.FULL_CONTEXT_SNAPSHOT, "context_snapshot.schema.json", id="context-full"),
    pytest.param(IntentResult, ex.MINIMAL_INTENT_RESULT, "intent_result.schema.json", id="intent-minimal"),
    pytest.param(IntentResult, ex.FULL_INTENT_RESULT, "intent_result.schema.json", id="intent-full"),
    pytest.param(SharedCaseState, ex.MINIMAL_SHARED_CASE_STATE, "shared_case_state.schema.json", id="case-minimal"),
    pytest.param(SharedCaseState, ex.FULL_SHARED_CASE_STATE, "shared_case_state.schema.json", id="case-full"),
]


def _dump(instance) -> Dict[str, Any]:
    return instance.model_dump(mode="json")


# --- 1 & 2: valid minimal payload / valid full payload -----------------------


@pytest.mark.parametrize("model, payload, schema_file", MODEL_CASES)
def test_examples_are_valid_pydantic_and_json_schema(model, payload, schema_file):
    """Pydantic parses the example AND the raw JSON Schema accepts it as-is."""
    instance = model.model_validate(payload)
    validate_instance(copy.deepcopy(payload), schema_file)

    # The Pydantic-serialized form must also satisfy the same JSON Schema, so
    # a real API response built from these models stays contract-valid.
    validate_instance(_dump(instance), schema_file)


# --- 3: unknown enum rejected -------------------------------------------------


def test_unknown_status_enum_rejected_by_both():
    bad = copy.deepcopy(ex.MINIMAL_SHARED_CASE_STATE)
    bad["status"] = "not_a_real_status"

    with pytest.raises(PydanticValidationError):
        SharedCaseState.model_validate(bad)
    with pytest.raises(JSONSchemaValidationError):
        validate_instance(bad, "shared_case_state.schema.json")


def test_unknown_recommended_action_enum_rejected_by_both():
    bad = copy.deepcopy(ex.MINIMAL_INTENT_RESULT)
    bad["recommended_action"] = "do_whatever_it_wants"

    with pytest.raises(PydanticValidationError):
        IntentResult.model_validate(bad)
    with pytest.raises(JSONSchemaValidationError):
        validate_instance(bad, "intent_result.schema.json")


# --- 4: missing required ID rejected -----------------------------------------


@pytest.mark.parametrize("field", ["case_id", "trace_id"])
def test_missing_required_id_rejected_by_both(field):
    bad = copy.deepcopy(ex.MINIMAL_SHARED_CASE_STATE)
    del bad[field]

    with pytest.raises(PydanticValidationError):
        SharedCaseState.model_validate(bad)
    with pytest.raises(JSONSchemaValidationError):
        validate_instance(bad, "shared_case_state.schema.json")


def test_missing_employee_id_rejected_by_both():
    bad = copy.deepcopy(ex.MINIMAL_CONTEXT_SNAPSHOT)
    del bad["employee"]["employee_id"]

    with pytest.raises(PydanticValidationError):
        ContextSnapshot.model_validate(bad)
    with pytest.raises(JSONSchemaValidationError):
        validate_instance(bad, "context_snapshot.schema.json")


# --- 5: confidence outside [0,1] rejected ------------------------------------


@pytest.mark.parametrize("confidence", [-0.01, 1.01, 5.0])
def test_confidence_out_of_bounds_rejected_by_both(confidence):
    bad = copy.deepcopy(ex.FULL_INTENT_RESULT)
    bad["resolved_slots"]["customer_id"]["confidence"] = confidence

    with pytest.raises(PydanticValidationError):
        IntentResult.model_validate(bad)
    with pytest.raises(JSONSchemaValidationError):
        validate_instance(bad, "intent_result.schema.json")


def test_overall_confidence_out_of_bounds_rejected_by_both():
    bad = copy.deepcopy(ex.MINIMAL_INTENT_RESULT)
    bad["overall_confidence"] = 1.5

    with pytest.raises(PydanticValidationError):
        IntentResult.model_validate(bad)
    with pytest.raises(JSONSchemaValidationError):
        validate_instance(bad, "intent_result.schema.json")


# --- 6: external action missing idempotency/approval rejected ----------------


def test_action_input_missing_approval_token_rejected_by_both():
    with pytest.raises(PydanticValidationError):
        ActionInput.model_validate(ex.ACTION_INPUT_MISSING_APPROVAL)
    with pytest.raises(JSONSchemaValidationError):
        Draft202012Validator(action_input_schema()).validate(ex.ACTION_INPUT_MISSING_APPROVAL)


def test_action_input_missing_idempotency_key_rejected_by_both():
    bad = copy.deepcopy(ex.VALID_ACTION_INPUT)
    del bad["idempotency_key"]

    with pytest.raises(PydanticValidationError):
        ActionInput.model_validate(bad)
    with pytest.raises(JSONSchemaValidationError):
        Draft202012Validator(action_input_schema()).validate(bad)


def test_action_input_with_approval_and_idempotency_is_accepted():
    ActionInput.model_validate(ex.VALID_ACTION_INPUT)
    Draft202012Validator(action_input_schema()).validate(ex.VALID_ACTION_INPUT)


# --- 7: old compatible version / additive-optional-field migration test -----


def test_payload_predating_optional_additive_fields_still_validates():
    """schema_version 2.0.0 is the first V2 contract release, so there is no
    real prior version to replay. This test instead proves the forward/
    backward-compatibility mechanism the contract relies on: a payload that
    only sets the *required* fields (as an older minor version without the
    later-added optional fields would have produced) must still validate
    under both Pydantic (fields fall back to their declared defaults) and the
    raw JSON Schema (the fields are optional, not required).
    """
    old_shaped = copy.deepcopy(ex.MINIMAL_SHARED_CASE_STATE)
    # workflow.resume_from_nodes has a JSON Schema "default" and is not in
    # "required" -- simulate a payload from before that field existed.
    assert "resume_from_nodes" not in old_shaped["workflow"]

    instance = SharedCaseState.model_validate(old_shaped)
    assert instance.workflow.resume_from_nodes == []
    validate_instance(old_shaped, "shared_case_state.schema.json")

    old_employee = copy.deepcopy(ex.MINIMAL_CONTEXT_SNAPSHOT)
    assert "preferences" not in old_employee["employee"]
    context = ContextSnapshot.model_validate(old_employee)
    assert context.employee.preferences == {}
    validate_instance(old_employee, "context_snapshot.schema.json")


# --- 8: API response validates against the same schema -----------------------


def test_example_api_response_validates_against_shared_case_state_schema():
    """FULL_SHARED_CASE_STATE stands in for a future `/api/v2` GET case
    response (V2-013 has not started yet, see plan_v2/PROGRESS.md V2-013).
    It is asserted here so the same fixture can be reused verbatim as the
    OpenAPI response example once the endpoint exists, without risking drift.
    """
    instance = SharedCaseState.model_validate(ex.FULL_SHARED_CASE_STATE)
    api_response = _dump(instance)
    validate_instance(api_response, "shared_case_state.schema.json")
    assert api_response["case_id"] == ex.FULL_SHARED_CASE_STATE["case_id"]


# --- additional coverage: data_source_card (module 18) and tool registry -----


VALID_DATA_SOURCE_CARD: Dict[str, Any] = {
    "schema_version": "2.0.0",
    "source_id": "product-catalog-internal",
    "name": "SHB Product Catalog (synthetic)",
    "domain": "product",
    "tier": "E_SYNTHETIC",
    "owner": {"business_owner": "Product Team", "data_steward": "Product Team"},
    "purpose": {"allowed_uses": ["product_rag_serving"], "prohibited_uses": ["credit_decisioning"]},
    "decision_role": "AUTHORITATIVE",
    "access": {"method": "FILE", "authentication": "none", "sandbox_available": True},
    "governance": {
        "legal_basis_or_license": "internal synthetic demo data",
        "sensitivity": "INTERNAL",
        "retention": "hackathon-only",
        "residency": "VN",
        "approved": True,
    },
    "freshness": {"update_cadence": "manual", "max_age_seconds": 86400, "stale_behavior": "ALLOW_WITH_WARNING"},
    "identifiers": {"primary_key": "product_id", "join_keys": []},
    "quality": {"required_checks": ["schema_valid", "no_duplicates"], "publish_gate": "manual_review"},
    "lineage": {"ingestion_job": "n/a", "raw_location": "app/tools/product_tools.py", "consumer_artifacts": ["ProductRAGService"]},
    "lifecycle_status": "ACTIVE",
}


def test_data_source_card_valid_example_accepted_by_both():
    card = DataSourceCard.model_validate(VALID_DATA_SOURCE_CARD)
    assert card.is_usable_for_serving() is True
    validate_instance(copy.deepcopy(VALID_DATA_SOURCE_CARD), "data_source_card.schema.json")
    # exclude_none: dataset_version/effective_from are optional-and-omittable
    # in the JSON schema (type: "string", not nullable) -- Pydantic's default
    # None must not round-trip as a literal null.
    validate_instance(card.model_dump(mode="json", exclude_none=True), "data_source_card.schema.json")


def test_data_source_card_missing_owner_rejected_by_both():
    bad = copy.deepcopy(VALID_DATA_SOURCE_CARD)
    del bad["owner"]

    with pytest.raises(PydanticValidationError):
        DataSourceCard.model_validate(bad)
    with pytest.raises(JSONSchemaValidationError):
        validate_instance(bad, "data_source_card.schema.json")


def test_data_source_card_not_approved_is_not_usable_for_serving():
    not_approved = copy.deepcopy(VALID_DATA_SOURCE_CARD)
    not_approved["governance"]["approved"] = False
    card = DataSourceCard.model_validate(not_approved)
    assert card.is_usable_for_serving() is False


def test_tool_registry_loads_all_declared_tools_with_valid_risk_and_approval():
    registry = load_tool_registry()
    names = {tool.name for tool in registry.tools}
    assert names == {
        "get_employee_context",
        "get_workspace_context",
        "get_customer_profile",
        "search_product_knowledge",
        "search_legal_knowledge",
        "create_crm_case",
        "create_followup_task",
        "send_customer_message",
    }
    # plan_v2/00_AI_BUILD_PROTOCOL.md: "Moi write action can idempotency key" ->
    # every write_high/external_communication tool must require approval.
    for tool in registry.tools:
        if tool.risk.value in {"write_high", "external_communication"}:
            assert tool.approval_required is True, tool.name


def test_tool_registry_allowed_caller_check():
    registry = load_tool_registry()
    assert registry.is_caller_allowed("create_crm_case", "ActionExecutor") is True
    assert registry.is_caller_allowed("create_crm_case", "ProductAgent") is False


def test_expert_findings_and_synthesis_result_validate_against_agent_collaboration_schema(tmp_path):
    """agent_collaboration.schema.json (ExpertFinding/SynthesisResult/etc, used
    by app/agents/contracts.py) had zero contract-test coverage before this --
    the same blind spot that let data_source_card.schema.json silently drift
    from its Pydantic mirror (dataset_version/effective_from/effective_to were
    valid JSON Schema properties Pydantic rejected as extra_forbidden) go
    undetected until it was hit by accident. Runs one real case end-to-end
    (not hand-built fixtures -- ExpertFinding has too many nested required
    objects to safely hand-author without missing something) and validates
    every emitted ExpertFinding plus the SynthesisResult against the JSON
    schema, the same way test_data_source_card_valid_example_accepted_by_both
    does for DataSourceCard."""
    import asyncio
    from copy import deepcopy

    from app.schemas.v2.context_snapshot import ContextSnapshot
    from app.schemas.v2.shared_case_state import SharedCaseState
    from app.workflow.engine import V2WorkflowEngine

    payload = deepcopy(ex.MINIMAL_SHARED_CASE_STATE)
    context = deepcopy(ex.FULL_CONTEXT_SNAPSHOT)
    context["conflicts"] = []
    context["customer"]["attributes"].update(
        {"operating_years": 8, "has_bad_debt_12m": False, "ubo_status": "verified", "account_or_unit_count": 4}
    )
    context["documents"].append(
        {
            "document_id": "DOC-FS", "document_type": "financial_statements", "version": "1",
            "status": "verified", "access_scope": {"branch": "HN01"},
        }
    )
    payload["context"] = ContextSnapshot.model_validate(context).model_dump(mode="json")
    payload["request"]["text"] = "Tìm vốn lưu động"
    payload["request"]["message_id"] = "MSG-CONTRACT-PROBE"
    state = SharedCaseState.model_validate(payload)

    engine = V2WorkflowEngine(index_path=str(tmp_path / "index.sqlite3"))
    state = asyncio.run(engine.run(state))

    assert state.expert_findings, "expected at least one ExpertFinding from a full engine run"
    for finding in state.expert_findings:
        validate_instance(finding.model_dump(mode="json"), "agent_collaboration.schema.json")

    assert state.synthesis_result is not None
    validate_instance(state.synthesis_result.model_dump(mode="json"), "agent_collaboration.schema.json")
