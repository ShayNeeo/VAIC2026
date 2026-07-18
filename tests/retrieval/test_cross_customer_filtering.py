"""Phase 1 section 10 "Cross-customer" hard gate test.

Honest scope note: app/knowledge/models.py's KnowledgeChunk has no
customer_id field at all -- it indexes PRODUCT/POLICY/SOP knowledge shared
across customers, not per-customer evidence, so there is no literal
"CUSTOMER-A vs CUSTOMER-B" scope to leak between here. The real boundary
this system enforces at the KnowledgeChunk layer is branch scope
(access_scope.branches). This file proves that boundary with the exact
structure the prompt's cross-customer test asks for (a highly relevant,
high-scoring candidate that must NOT enter the ranked result set because
it belongs to a scope the requester is not in) -- substituting the real
scope dimension this system has instead of inventing a customer_id field
that doesn't exist. Per-customer evidence scoping (a genuine
cross-customer leak surface) lives in app/schemas/v2/shared_case_state.py
Evidence + app/api/v2/router.py's owned()/case-scope checks, which are
outside app/knowledge/'s retrieval layer and already covered by
tests/unit/test_v2_specialist_review.py's cross-employee scope tests.
"""

from __future__ import annotations

from datetime import date

from app.knowledge.index import PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk


def test_high_scoring_out_of_branch_chunk_never_enters_the_ranked_result_set(tmp_path):
    """A chunk that would score highest by relevance (exact product_id
    match in the query text -> triggers exact_bonus) must still never
    reach the caller if it belongs to a branch the requester is not
    scoped to -- security filtering must run before/during scoring, not
    as a post-hoc top-k cleanup."""
    index = PersistentHybridIndex(tmp_path / "cross_scope.sqlite3")
    restricted = KnowledgeChunk(
        chunk_id="RESTRICTED-HIGH-SCORE", document_id="DOC-R", document_version="1",
        product_id="SYNTH-PROD-WORKING-CAPITAL", section_path="1.1",
        text="SYNTH-PROD-WORKING-CAPITAL vốn lưu động điều kiện hồ sơ UBO báo cáo tài chính",
        effective_from=date(2026, 1, 1), effective_to=None, active=True,
        segments=[], access_scope={"branches": ["BRANCH-RESTRICTED-ONLY"]}, content_hash="hash-r",
    )
    allowed = KnowledgeChunk(
        chunk_id="ALLOWED-LOW-SCORE", document_id="DOC-A", document_version="1",
        product_id="SYNTH-PROD-WORKING-CAPITAL", section_path="1.1",
        text="thông tin chung về sản phẩm",
        effective_from=date(2026, 1, 1), effective_to=None, active=True,
        segments=[], access_scope={"branches": ["*"]}, content_hash="hash-a",
    )
    index.upsert([restricted, allowed], source_hash="s1", dataset_version="v1")

    hits, diagnostics = index.search_with_diagnostics(
        "SYNTH-PROD-WORKING-CAPITAL vốn lưu động điều kiện", branch="BRANCH-REQUESTER", threshold=0.01,
    )

    assert "RESTRICTED-HIGH-SCORE" not in {h.chunk.chunk_id for h in hits}
    assert diagnostics.filtered_reasons.get("SOURCE_SCOPE_MISMATCH") == 1


def test_exact_lookup_by_product_id_also_respects_branch_scope_not_just_semantic_search(tmp_path):
    """The exact-lookup path (Phase 1 section 4) is a second, independent
    code path from search_with_diagnostics() -- it must enforce the same
    boundary, not just the scored path."""
    index = PersistentHybridIndex(tmp_path / "cross_scope_exact.sqlite3")
    restricted = KnowledgeChunk(
        chunk_id="RESTRICTED", document_id="DOC-R", document_version="1",
        product_id="SYNTH-PROD-WORKING-CAPITAL", section_path="1.1", text="nội dung",
        effective_from=date(2026, 1, 1), effective_to=None, active=True,
        segments=[], access_scope={"branches": ["BRANCH-RESTRICTED-ONLY"]}, content_hash="hash-r2",
    )
    index.upsert([restricted], source_hash="s2", dataset_version="v1")
    assert index.exact_lookup_by_product_id("SYNTH-PROD-WORKING-CAPITAL", branch="BRANCH-REQUESTER") == []
