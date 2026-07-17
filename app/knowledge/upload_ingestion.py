"""Governed upload-to-index pipeline with quarantine and lineage."""

from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from app.data_catalog.registry import require_serving_approval
from app.knowledge.index import PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk
from app.knowledge.parsers import extraction_quality, parse_document_bytes
from app.safety.input_guardrails_v2 import screen_input


class GovernedUploadIngestionService:
    def __init__(self, index: PersistentHybridIndex) -> None:
        self.index = index

    def ingest(
        self,
        *,
        filename: str,
        data: bytes,
        source_card_path: str | Path,
        document_id: str,
        document_version: str,
        product_id: str,
        effective_from: date,
        effective_to: Optional[date],
        branch: str,
        segments: Iterable[str] = (),
    ) -> Dict[str, Any]:
        card = require_serving_approval(source_card_path)
        sections = parse_document_bytes(filename, data)
        quality = extraction_quality(sections)
        unsafe_locations = [section.location for section in sections if not screen_input(section.text).safe]
        publishable = bool(quality["publishable"] and not unsafe_locations)
        source_hash = hashlib.sha256(data).hexdigest()
        if not publishable:
            return {
                "status": "quarantined",
                "source_id": card.source_id,
                "source_hash": source_hash,
                "quality": {**quality, "prompt_injection_flags": len(unsafe_locations)},
                "indexed": 0,
                "unsafe_locations": unsafe_locations,
            }
        chunks = []
        non_empty = [section for section in sections if section.text.strip()]
        for index, section in enumerate(non_empty, start=1):
            text = section.text.strip()
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"{document_id}:{document_version}:{index}",
                    document_id=document_id,
                    document_version=document_version,
                    product_id=product_id,
                    section_path=section.location,
                    chunk_type=str(section.metadata.get("type", "uploaded_document")),
                    text=text,
                    effective_from=effective_from,
                    effective_to=effective_to,
                    active=True,
                    segments=list(segments),
                    access_scope={"branches": [branch]},
                    content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )
            )
        indexed = self.index.upsert(
            chunks,
            source_hash=source_hash,
            dataset_version=f"{card.source_id}:{document_version}",
        )
        return {
            "status": "indexed",
            "source_id": card.source_id,
            "source_hash": source_hash,
            "quality": {**quality, "prompt_injection_flags": 0},
            "indexed": indexed,
            "chunk_ids": [chunk.chunk_id for chunk in chunks],
        }
