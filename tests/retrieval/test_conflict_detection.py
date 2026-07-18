"""Phase 2 section 14 MVP -- see app/knowledge/conflict_detection.py
module docstring for the honest scope note (slot-identity proxy, not full
structured-fact conflict detection)."""

from __future__ import annotations

from datetime import date

from app.knowledge.conflict_detection import detect_slot_conflicts
from app.knowledge.models import KnowledgeChunk


def _chunk(chunk_id: str, product_id: str, section_path: str, content_hash: str) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=chunk_id, document_id=f"DOC-{chunk_id}", document_version="1", product_id=product_id,
        section_path=section_path, text="text", effective_from=date(2026, 1, 1), effective_to=None,
        active=True, segments=[], access_scope={"branches": ["*"]}, content_hash=content_hash,
    )


def test_two_chunks_same_slot_different_hash_is_a_conflict():
    chunks = [
        _chunk("C1", "PROD-X", "1.1", "hash-a"),
        _chunk("C2", "PROD-X", "1.1", "hash-b"),
    ]
    conflicts = detect_slot_conflicts(chunks)
    assert len(conflicts) == 1
    assert {conflicts[0].chunk_id_a, conflicts[0].chunk_id_b} == {"C1", "C2"}
    assert conflicts[0].requires_human_review is True


def test_two_chunks_same_slot_same_hash_is_not_a_conflict():
    chunks = [
        _chunk("C1", "PROD-X", "1.1", "hash-a"),
        _chunk("C2", "PROD-X", "1.1", "hash-a"),
    ]
    assert detect_slot_conflicts(chunks) == []


def test_different_slots_never_conflict():
    chunks = [
        _chunk("C1", "PROD-X", "1.1", "hash-a"),
        _chunk("C2", "PROD-Y", "1.1", "hash-b"),
        _chunk("C3", "PROD-X", "1.2", "hash-c"),
    ]
    assert detect_slot_conflicts(chunks) == []


def test_single_chunk_never_conflicts_with_itself():
    assert detect_slot_conflicts([_chunk("C1", "PROD-X", "1.1", "hash-a")]) == []
