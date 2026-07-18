"""Phase 4 section 39: forbidden overclaim phrases in Agent output text."""

from __future__ import annotations

from app.safety.output_language_guardrail import check_output_language, suggest_safe_rewrite_markers


def test_safe_hedged_output_passes():
    result = check_output_language("Day la de xuat so bo, can xac minh them truoc khi trinh RM.")
    assert result.is_safe is True
    assert result.forbidden_phrases_found == []


def test_overclaim_phrase_is_flagged():
    result = check_output_language("Khach hang chac chan du dieu kien vay von.")
    assert result.is_safe is False
    assert "chắc chắn" in result.forbidden_phrases_found


def test_approval_language_is_flagged():
    result = check_output_language("Ho so da duoc phe duyet, han muc duoc duyet la 5 ty.")
    assert result.is_safe is False


def test_multiple_forbidden_phrases_are_all_reported():
    result = check_output_language("Chac chan du dieu kien va da duoc phe duyet.")
    assert len(result.forbidden_phrases_found) >= 2


def test_safe_markers_list_is_non_empty():
    assert len(suggest_safe_rewrite_markers()) > 0
