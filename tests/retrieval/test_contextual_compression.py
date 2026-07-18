"""Phase 3 section 29: extractive compression preserves exact offsets into
the ORIGINAL chunk text (never re-indexes into compressed text)."""

from __future__ import annotations

from app.knowledge.compression import compress_chunk_text


def test_compressed_spans_are_substrings_of_the_original_text_at_their_offsets():
    text = (
        "Doanh nghiep can co giay phep kinh doanh hop le. | "
        "Tru truong hop da co UBO xac minh truoc ngay 2026. | "
        "Ho tro tu van mien phi cho khach hang moi."
    )
    spans = compress_chunk_text("C1", text, max_sentences=2)
    for span in spans:
        assert text[span.start_offset:span.end_offset] == span.compressed_text
        assert span.original_chunk_id == "C1"


def test_sentence_with_exception_marker_and_date_is_kept_over_generic_marketing_text():
    text = (
        "Ho tro tu van mien phi cho khach hang moi. | "
        "Tru truong hop da co UBO xac minh truoc ngay 2026."
    )
    spans = compress_chunk_text("C1", text, max_sentences=1)
    assert len(spans) == 1
    assert "Tru truong hop" in spans[0].compressed_text


def test_spans_preserve_original_order_not_score_order():
    text = "Cau mot khong quan trong. | Cau hai co so 2026 quan trong hon. | Cau ba cung co so 5."
    spans = compress_chunk_text("C1", text, max_sentences=2)
    offsets = [s.start_offset for s in spans]
    assert offsets == sorted(offsets)


def test_empty_text_returns_no_spans():
    assert compress_chunk_text("C1", "") == []
