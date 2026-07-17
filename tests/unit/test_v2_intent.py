"""Acceptance tests for V2 intent extraction and context-aware slot resolution."""

from __future__ import annotations

import asyncio

import pytest

from app.intent.clarification import select_clarification
from app.intent.extractor import IntentExtractor
from app.intent.fallback import DeterministicIntentExtractor
from app.intent.normalizer import extract_amount, extract_tenor_months, normalize_entity, normalize_text
from app.intent.slot_registry import WorkflowStage
from app.intent.slot_resolver import SlotResolver
from app.intent.validator import IntentSemanticError, validate_intent_result
from app.schemas.v2.context_snapshot import ContextSnapshot
from app.schemas.v2.examples import FULL_CONTEXT_SNAPSHOT, MINIMAL_CONTEXT_SNAPSHOT
from app.schemas.v2.intent_result import RecommendedAction


def context(full: bool = True) -> ContextSnapshot:
    payload = FULL_CONTEXT_SNAPSHOT if full else MINIMAL_CONTEXT_SNAPSHOT
    return ContextSnapshot.model_validate(payload)


def test_normalize_text_and_controlled_entities():
    assert normalize_text("  Xin chào   các bạn  ") == "Xin chào các bạn"
    assert normalize_entity("product", "khách muốn vay HMTD gấp") == "PROD-WORKING-CAPITAL"
    assert normalize_entity("product", "dịch vụ chi lương online") == "PROD-PAYROLL"
    assert normalize_entity("product", "quản lý dòng tiền doanh nghiệp") == "PROD-CASH-MGMT"
    assert normalize_entity("urgency", "cần gấp") == "urgent"
    assert normalize_entity("urgency", "bình thường") == "normal"


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Cần hạn mức 5 tỷ", 5_000_000_000),
        ("Nhu cầu 750 triệu", 750_000_000),
        ("Khoảng 125000000 đồng", 125_000_000),
    ],
)
def test_amount_normalization(message: str, expected: int):
    assert extract_amount(message)["amount"] == expected


def test_tenor_normalization():
    assert extract_tenor_months("vay trong 18 tháng")["months"] == 18
    assert extract_tenor_months("kỳ hạn 2 năm")["months"] == 24


def test_deterministic_extractor_supports_multi_intent_and_evidence():
    message = "Tìm gói trả lương, kiểm tra điều kiện và chuẩn bị email cho khách"
    result = DeterministicIntentExtractor().extract(message, "MSG-1", context())

    assert result.primary_intent == "find_product"
    assert "check_eligibility" in result.sub_intents
    assert "prepare_customer_response" in result.sub_intents
    assert result.entities["product_ids"] == ["PROD-PAYROLL"]
    assert result.resolved_slots["customer_id"].value == "COMP-ABC"
    assert all(span.message_id == "MSG-1" and span.text in message for span in result.evidence_spans)


def test_slot_resolver_uses_workspace_and_asks_only_one_high_value_question():
    result = DeterministicIntentExtractor().extract(
        "Kiểm tra điều kiện sản phẩm", "MSG-2", context(False)
    )
    resolved = SlotResolver().resolve(result, context(False), stage=WorkflowStage.ELIGIBILITY)
    clarification = select_clarification(resolved, context(False))

    assert "customer_id" in resolved.missing_information
    assert resolved.recommended_action == RecommendedAction.ASK_CLARIFICATION
    assert clarification is not None
    assert clarification.field == "customer_id"


def test_context_conflict_forces_confirmation_instead_of_silent_assumption():
    result = DeterministicIntentExtractor().extract("Kiểm tra điều kiện payroll", "MSG-3", context())
    resolved = SlotResolver().resolve(result, context(), stage=WorkflowStage.ELIGIBILITY)
    clarification = select_clarification(resolved, context())

    assert resolved.recommended_action == RecommendedAction.REQUEST_CONFIRMATION
    assert clarification is not None
    assert clarification.field == "annual_revenue"


def test_semantic_validator_rejects_fabricated_evidence_span():
    result = DeterministicIntentExtractor().extract("Tìm gói payroll", "MSG-4", context())
    invalid = result.model_copy(
        update={"evidence_spans": [result.evidence_spans[0].model_copy(update={"text": "không có"})]}
    )
    with pytest.raises(IntentSemanticError):
        validate_intent_result(invalid, message="Tìm gói payroll", message_id="MSG-4")


class _BrokenCompletions:
    async def create(self, **_kwargs):
        raise TimeoutError("simulated model timeout")


class _BrokenChat:
    completions = _BrokenCompletions()


class _BrokenClient:
    chat = _BrokenChat()


def test_llm_failure_falls_back_to_deterministic_extraction():
    extractor = IntentExtractor(client=_BrokenClient(), prefer_llm=True)
    result = asyncio.run(extractor.extract_intent("Tìm gói payroll", "MSG-5", context()))

    assert result.primary_intent == "find_product"
    assert result.entities["product_ids"] == ["PROD-PAYROLL"]
