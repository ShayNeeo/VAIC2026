"""ReferenceLibraryService ingests the mock credit-proposal memo as a
retrievable reference document, isolated from any Expert Agent's evidence
pipeline (see app/knowledge/reference_library_service.py's module docstring
and data/catalog/source_cards/synthetic_credit_proposal_reference.json's
prohibited_uses)."""

from pathlib import Path

from app.knowledge.index import LocalEmbedding
from app.knowledge.reference_library_service import ReferenceLibraryService
from app.knowledge.retrieval_contracts import AuthorityTier

MOCK_PROPOSAL_PATH = (
    Path(__file__).resolve().parents[2] / "mock tờ trinh đề xuất của khách hàng.docx"
)


def test_ingests_real_mock_proposal_and_is_searchable(tmp_path: Path):
    assert MOCK_PROPOSAL_PATH.exists(), f"missing fixture: {MOCK_PROPOSAL_PATH}"
    service = ReferenceLibraryService(tmp_path / "reference.sqlite3", provider=LocalEmbedding())

    count = service.ingest_docx(MOCK_PROPOSAL_PATH, document_id="REF-DOC-CREDIT-PROPOSAL-001")
    assert count > 0

    chunks = service.list_chunks()
    assert chunks
    assert all(chunk.authority_tier == AuthorityTier.TIER_5_UNSUPPORTED for chunk in chunks)

    hits = service.search("vốn lưu động nhập khẩu linh kiện điện tử", top_k=5)
    assert hits
    assert any("vốn lưu động" in hit.chunk.text.lower() or "nhập khẩu" in hit.chunk.text.lower() for hit in hits)


def test_ingestion_is_idempotent_via_upsert(tmp_path: Path):
    service = ReferenceLibraryService(tmp_path / "reference.sqlite3", provider=LocalEmbedding())
    first = service.ingest_docx(MOCK_PROPOSAL_PATH, document_id="REF-DOC-CREDIT-PROPOSAL-001")
    second = service.ingest_docx(MOCK_PROPOSAL_PATH, document_id="REF-DOC-CREDIT-PROPOSAL-001")
    assert first == second
    assert len(service.list_chunks()) == first
