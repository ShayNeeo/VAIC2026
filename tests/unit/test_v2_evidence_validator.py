"""Tests for the real evidence validator (app.safety.evidence_validator),
which replaced the previous live-path check `is_valid=bool(quote)`.

Covers the deterministic-only path (no embedding provider / API key
required) plus the live wiring into V2WorkflowEngine._product_evidence, so a
tampered/fabricated quote is provably caught rather than trusted."""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

import pytest

from app.knowledge.models import KnowledgeChunk
from app.safety.evidence_validator import (
    ClaimInput,
    EvidenceValidator,
    ValidationStatus,
    detect_conflicts,
    validate_claim,
)


def _chunk(
    *,
    chunk_id: str = "C-1",
    document_id: str = "DOC-1",
    document_version: str = "v1",
    text: str = "Sản phẩm PROD-PAYROLL hỗ trợ chi lương cho doanh nghiệp trên 10 nhân sự.",
    effective_from: date = date(2020, 1, 1),
    effective_to: Optional[date] = None,
) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=chunk_id, document_id=document_id, document_version=document_version,
        product_id="PROD-PAYROLL", section_path="section-1", chunk_type="product_overview",
        text=text, effective_from=effective_from, effective_to=effective_to, active=True,
        segments=[], access_scope={"branches": ["*"]}, content_hash="deadbeef",
    )


class FakeIndex:
    """Minimal stand-in for PersistentHybridIndex.get_chunks_for_document."""

    def __init__(self, chunks: List[KnowledgeChunk]) -> None:
        self._chunks = chunks

    def get_chunks_for_document(self, document_id: str, document_version: Optional[str] = None) -> List[KnowledgeChunk]:
        return [
            c for c in self._chunks
            if c.document_id == document_id and (document_version is None or c.document_version == document_version)
        ]


# --------------------------------------------------------------------------
# 1: correct quote -> valid
# --------------------------------------------------------------------------


def test_exact_quote_is_valid():
    chunk = _chunk(text="Sản phẩm PROD-PAYROLL hỗ trợ chi lương cho 500 nhân viên.")
    index = FakeIndex([chunk])
    result = validate_claim(
        claim_id="C1", source_document_id="DOC-1", source_version="v1",
        quote="Sản phẩm PROD-PAYROLL hỗ trợ chi lương cho 500 nhân viên.", index=index,
    )
    assert result.status == ValidationStatus.VALID
    assert result.is_valid is True
    assert result.exact_match is True


def test_quote_as_substring_of_a_longer_chunk_is_valid():
    chunk = _chunk(text="Trước | Sản phẩm PROD-PAYROLL hỗ trợ chi lương cho 500 nhân viên. | Sau")
    index = FakeIndex([chunk])
    result = validate_claim(
        claim_id="C1", source_document_id="DOC-1", source_version="v1",
        quote="Sản phẩm PROD-PAYROLL hỗ trợ chi lương cho 500 nhân viên.", index=index,
    )
    assert result.is_valid is True


# --------------------------------------------------------------------------
# 2: quote altered by one word -> invalid
# --------------------------------------------------------------------------


def test_altered_quote_is_invalid():
    chunk = _chunk(text="Sản phẩm PROD-PAYROLL hỗ trợ chi lương cho 500 nhân viên.")
    index = FakeIndex([chunk])
    result = validate_claim(
        claim_id="C1", source_document_id="DOC-1", source_version="v1",
        # "500" changed to "5000" -- a single-token fabrication.
        quote="Sản phẩm PROD-PAYROLL hỗ trợ chi lương cho 5000 nhân viên.", index=index,
    )
    assert result.status == ValidationStatus.INVALID
    assert result.is_valid is False
    assert result.reason == "quote_not_found_in_source"


# --------------------------------------------------------------------------
# 3: quote that never existed -> invalid
# --------------------------------------------------------------------------


def test_fabricated_quote_not_present_anywhere_is_invalid():
    index = FakeIndex([_chunk(text="Nội dung hoàn toàn khác không liên quan.")])
    result = validate_claim(
        claim_id="C1", source_document_id="DOC-1", source_version="v1",
        quote="Câu này chưa từng xuất hiện trong tài liệu nguồn.", index=index,
    )
    assert result.is_valid is False
    assert result.status == ValidationStatus.INVALID


# --------------------------------------------------------------------------
# 4: source document not found
# --------------------------------------------------------------------------


def test_unknown_source_document_is_source_not_found():
    index = FakeIndex([_chunk(document_id="DOC-1")])
    result = validate_claim(
        claim_id="C1", source_document_id="DOC-DOES-NOT-EXIST", source_version="v1",
        quote="bất kỳ nội dung nào", index=index,
    )
    assert result.status == ValidationStatus.SOURCE_NOT_FOUND


# --------------------------------------------------------------------------
# 5: version mismatch
# --------------------------------------------------------------------------


def test_known_document_wrong_version_is_version_mismatch():
    index = FakeIndex([_chunk(document_id="DOC-1", document_version="v1", text="nội dung v1")])
    result = validate_claim(
        claim_id="C1", source_document_id="DOC-1", source_version="v2",
        quote="nội dung v1", index=index,
    )
    assert result.status == ValidationStatus.VERSION_MISMATCH


# --------------------------------------------------------------------------
# 6: whitespace/line-break differences but same content -> valid
# --------------------------------------------------------------------------


def test_whitespace_and_linebreak_differences_still_match():
    chunk = _chunk(text="Sản phẩm PROD-PAYROLL   hỗ trợ chi lương\ncho 500 nhân viên.")
    index = FakeIndex([chunk])
    result = validate_claim(
        claim_id="C1", source_document_id="DOC-1", source_version="v1",
        quote="Sản phẩm PROD-PAYROLL hỗ trợ chi lương cho 500 nhân viên.", index=index,
    )
    assert result.is_valid is True
    assert result.exact_match is True


# --------------------------------------------------------------------------
# Expired source
# --------------------------------------------------------------------------


def test_expired_source_is_flagged_even_though_quote_matches():
    chunk = _chunk(text="nội dung hết hạn", effective_to=date(2020, 1, 1))
    index = FakeIndex([chunk])
    result = validate_claim(
        claim_id="C1", source_document_id="DOC-1", source_version="v1",
        quote="nội dung hết hạn", index=index, as_of=date(2026, 1, 1),
    )
    assert result.status == ValidationStatus.EXPIRED_SOURCE


# --------------------------------------------------------------------------
# Empty quote
# --------------------------------------------------------------------------


def test_empty_quote_is_insufficient_evidence():
    result = validate_claim(
        claim_id="C1", source_document_id="DOC-1", source_version="v1",
        quote="   ", index=FakeIndex([]),
    )
    assert result.status == ValidationStatus.INSUFFICIENT_EVIDENCE
    assert result.is_valid is False


# --------------------------------------------------------------------------
# System-authored sources (not drawn from the RAG index)
# --------------------------------------------------------------------------


def test_system_tool_contract_source_is_exempt_from_index_lookup():
    result = validate_claim(
        claim_id="C1", source_document_id="SYSTEM-TOOL-CONTRACT", source_version="2.0.0",
        quote="Khi nguồn kiểm tra tín dụng lỗi, hệ thống không được tự kết luận đạt.",
        index=FakeIndex([]),  # deliberately empty -- must not be consulted
    )
    assert result.is_valid is True


# --------------------------------------------------------------------------
# 7: conflicting evidence (same claim_id, different quotes)
# --------------------------------------------------------------------------


def test_detect_conflicts_flags_same_claim_id_with_different_quotes():
    claims = [
        ClaimInput("C1", "DOC-1", "v1", "nội dung A"),
        ClaimInput("C1", "DOC-1", "v1", "nội dung B"),
        ClaimInput("C2", "DOC-1", "v1", "nội dung C"),
    ]
    conflicts = detect_conflicts(claims)
    assert "C1" in conflicts
    assert "C2" not in conflicts


def test_evidence_validator_marks_conflicting_claim_id_invalid():
    class E:
        def __init__(self, claim_id, quote):
            self.claim_id = claim_id
            self.module = "Product"
            self.source_document_id = "DOC-1"
            self.source_version = "v1"
            self.quote = quote

    index = FakeIndex([_chunk(text="nội dung A"), _chunk(chunk_id="C-2", text="nội dung B")])
    validator = EvidenceValidator(product_index=index, legal_index=FakeIndex([]))
    results = validator.validate_all([E("C1", "nội dung A"), E("C1", "nội dung B")])
    assert all(r.status == ValidationStatus.CONFLICTING_EVIDENCE for r in results)


# --------------------------------------------------------------------------
# 8/9: invalid evidence blocks approval / action executor (integration)
# --------------------------------------------------------------------------


def test_tampered_product_quote_is_caught_by_the_live_engine_wiring(tmp_path):
    """End-to-end proof that V2WorkflowEngine._product_evidence no longer
    accepts any non-empty string: feed it a product_result whose evidence
    quote does not match what is actually indexed, and confirm is_valid is
    False (previously this would have been True via bool(quote))."""
    from app.knowledge.service import ProductKnowledgeService
    from app.schemas.v2.shared_case_state import CaseStatus
    from app.workflow.engine import V2WorkflowEngine

    knowledge = ProductKnowledgeService(tmp_path / "products.sqlite3")
    knowledge.ingest()
    real_hit = knowledge.search("chi lương", branch="HN01")[0]
    real_evidence = knowledge.evidence(real_hit)

    engine = V2WorkflowEngine(index_path=tmp_path / "products.sqlite3")
    state = _minimal_state()
    state.product_result = {
        "status": "grounded",
        "recommendations": [
            {
                "product_id": real_evidence["product_id"],
                "evidences": [{**real_evidence, "quote": "Câu này bị chỉnh sửa và không tồn tại trong nguồn thật."}],
            }
        ],
    }
    engine._product_evidence(state)

    assert len(state.evidences) == 1
    assert state.evidences[0].is_valid is False


def _minimal_state():
    """Build the smallest SharedCaseState needed to call _product_evidence
    in isolation (context/request are required fields but not read by it)."""
    from datetime import datetime, timezone

    from app.schemas.v2.context_snapshot import ContextSnapshot
    from app.schemas.v2 import examples as ex
    from app.schemas.v2.shared_case_state import Approval, ApprovalStatus, CaseStatus, Request, SharedCaseState, Workflow

    context = ContextSnapshot.model_validate(ex.MINIMAL_CONTEXT_SNAPSHOT)
    now = datetime.now(timezone.utc)
    return SharedCaseState(
        case_id="CASE-TEST-0001", trace_id="TRACE-TEST-0001", status=CaseStatus.IN_ANALYSIS,
        context=context, request=Request(message_id="MSG-1", text="test", received_at=now),
        workflow=Workflow(workflow_version="test", current_node=None, tasks=[], loop_count=0),
        evidences=[], approval=Approval(status=ApprovalStatus.NOT_REQUIRED), audit_events=[],
        created_at=now, updated_at=now,
    )


def test_action_executor_denies_execution_when_any_evidence_is_invalid():
    from app.actions.executor import ActionExecutorV2, ExecutionDenied
    from app.schemas.v2.shared_case_state import CaseStatus, Evidence

    state = _minimal_state()
    state.status = CaseStatus.PENDING_APPROVAL
    state.eligibility_result = {"overall_status": "passed"}
    state.evidences = [
        Evidence(
            claim_id="C1", module="Product", claim="x", source_document_id="DOC-1",
            source_version="v1", location="loc", quote="q", is_valid=False, validation_score=0.0,
        )
    ]
    state.operations_result = {"action_payload": {"a": 1}}

    class FakeRepo:
        def get_idempotent_result(self, key):
            return None

    class FakeApproval:
        def verify_and_consume(self, *args, **kwargs):
            raise AssertionError("must not reach token verification when evidence is invalid")

    executor = ActionExecutorV2(FakeRepo(), FakeApproval())
    with pytest.raises(ExecutionDenied, match="evidence validation failed"):
        executor.execute(
            state, approver_id="RM-1", token="tok", idempotency_key="idem-1", payload={"a": 1},
        )
