"""Phase 3 section 23: versioned synonym expansion with provenance."""

from __future__ import annotations

from app.knowledge.query_expansion import EXPANSION_REGISTRY_VERSION, expand_query, expanded_query_text


def test_known_acronym_is_expanded_with_provenance():
    expansions = expand_query("can bo sung BCTC cho ho so")
    assert len(expansions) == 1
    assert expansions[0].original_term == "bctc"
    assert expansions[0].expanded_term == "báo cáo tài chính"
    assert expansions[0].registry_version == EXPANSION_REGISTRY_VERSION


def test_query_with_no_known_terms_expands_to_nothing():
    assert expand_query("mot cau hoi hoan toan khong lien quan") == []


def test_expanded_query_text_appends_synonyms():
    text = expanded_query_text("UBO can xac minh")
    assert "chủ sở hữu hưởng lợi" in text
    assert text.startswith("UBO can xac minh")


def test_expanded_query_text_is_unchanged_when_no_match():
    original = "mot cau hoi khong co tu khoa nao"
    assert expanded_query_text(original) == original
