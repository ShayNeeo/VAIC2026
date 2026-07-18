"""Conflict detection MVP -- RAG & Guardrail Implementation Plan Phase 2
section 14.

Honest scope note: the prompt's example is a *structured-fact* conflict
("CRM employee_count = 500" vs "Document employee_count = 430") -- two
independently-extracted values for the same (subject, field_name) pair.
This repository has no structured-fact store to compare against (no
extracted-fact table with subject/field_name/value columns); everything
PersistentHybridIndex serves is unstructured chunk text. Building the full
structured-fact conflict engine described in the prompt is out of scope
for this pass.

What IS real and testable here: two KnowledgeChunks that occupy the same
*logical slot* (same product_id + section_path -- i.e. the same rule/
section is indexed twice) but disagree in content_hash. That is a genuine,
detectable data-quality signal (a re-ingest that didn't retire the old
chunk, or two authoring pipelines writing to the same slot) and a
defensible, narrower proxy for "conflicting sources retrieved together" --
not the general case, and documented as such everywhere this is surfaced
(RetrievalConflict.reason always says explicitly what was compared).
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from app.knowledge.models import KnowledgeChunk
from app.knowledge.retrieval_contracts import RetrievalConflict


def detect_slot_conflicts(chunks: List[KnowledgeChunk]) -> List[RetrievalConflict]:
    """Group the given chunks by (product_id, section_path); any group with
    more than one distinct content_hash is a conflict. Only compares chunks
    that were actually passed in (e.g. the candidate set already selected
    for one GroundingPack) -- this is a retrieval-time check, not a
    corpus-wide audit."""
    slots: Dict[Tuple[str, str], List[KnowledgeChunk]] = {}
    for chunk in chunks:
        slots.setdefault((chunk.product_id, chunk.section_path), []).append(chunk)

    conflicts: List[RetrievalConflict] = []
    for (product_id, section_path), group in slots.items():
        distinct_hashes = {c.content_hash: c for c in group}
        if len(distinct_hashes) <= 1:
            continue
        ordered = sorted(distinct_hashes.values(), key=lambda c: c.chunk_id)
        for i in range(len(ordered) - 1):
            a, b = ordered[i], ordered[i + 1]
            conflicts.append(
                RetrievalConflict(
                    conflict_id=f"CONFLICT-{a.chunk_id}-{b.chunk_id}",
                    chunk_id_a=a.chunk_id,
                    chunk_id_b=b.chunk_id,
                    reason=(
                        f"Both chunks occupy product_id={product_id!r} "
                        f"section_path={section_path!r} with different content_hash "
                        f"({a.content_hash} vs {b.content_hash}) -- same logical slot, disagreeing content."
                    ),
                    requires_human_review=True,
                )
            )
    return conflicts
