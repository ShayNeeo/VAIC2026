"""Phase 3 section 21: deterministic query understanding -- entity
detection, task_type heuristic, ambiguity flags. No LLM call."""

from __future__ import annotations

from app.knowledge.query_understanding import understand_query


def test_known_product_id_is_detected_as_an_entity():
    result = understand_query("cho toi biet ve SYNTH-PROD-PAYROLL")
    assert "SYNTH-PROD-PAYROLL" in result.product_ids
    assert result.exact_lookup_required is True


def test_free_text_query_has_no_entities_and_needs_semantic_lookup():
    result = understand_query("dich vu chi luong cho doanh nghiep nho")
    assert result.entities == []
    assert result.exact_lookup_required is False
    assert result.semantic_lookup_required is True


def test_empty_query_is_flagged_ambiguous():
    result = understand_query("   ")
    assert "empty_query" in result.ambiguity


def test_eligibility_task_type_detected_from_keyword():
    result = understand_query("dieu kien vay von luu dong la gi")
    assert result.task_type == "eligibility_check"


def test_process_task_type_detected_from_keyword():
    result = understand_query("buoc tiep theo trong quy trinh la gi")
    assert result.task_type == "process_lookup"


def test_multi_hop_flagged_when_multiple_products_and_conjunction_present():
    result = understand_query("SYNTH-PROD-PAYROLL va SYNTH-PROD-CASH-MGMT can gi")
    assert result.multi_hop is True
    assert len(result.product_ids) == 2
