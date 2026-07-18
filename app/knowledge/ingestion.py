"""Idempotent JSON product ingestion with deterministic quality gates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List, Tuple

from pydantic import ValidationError

from app.knowledge.models import IngestReport, KnowledgeChunk, ProductDocument


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_product_chunks(path: str | Path) -> Tuple[List[KnowledgeChunk], IngestReport]:
    source = Path(path)
    raw = source.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    chunks: List[KnowledgeChunk] = []
    errors: List[str] = []
    accepted = 0
    for row_number, item in enumerate(payload.get("products", []), start=1):
        try:
            product = ProductDocument.model_validate(item)
            accepted += 1
            # Field-grounded chunk text: each salient field is a labelled
            # section so retrieval matches on meaning (not just product name)
            # and evidence quotes stay human-verifiable against the manual.
            text_parts = [
                product.product_id,
                product.name,
                product.description,
                "Lợi ích: " + "; ".join(product.benefits),
                "Điều kiện: " + product.eligibility_summary,
                "Hồ sơ: " + "; ".join(product.required_documents),
            ]
            if product.business_need:
                text_parts.append("Nhu cầu: " + product.business_need)
            if product.target_profile:
                text_parts.append("Khách hàng mục tiêu: " + product.target_profile)
            if product.public_features:
                text_parts.append("Thông tin công khai: " + "; ".join(product.public_features))
            if product.public_conditions:
                text_parts.append("Điều kiện công khai: " + "; ".join(product.public_conditions))
            if product.internal_required:
                text_parts.append("Cần kiểm tra nội bộ: " + "; ".join(product.internal_required))
            if product.sales_signals:
                text_parts.append("Tín hiệu bán: " + "; ".join(product.sales_signals))
            if product.discovery_questions:
                text_parts.append("Câu hỏi RM: " + " / ".join(product.discovery_questions))
            text = " | ".join(text_parts)
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"{product.document_id}:{product.document_version}:{product.product_id}",
                    document_id=product.document_id,
                    document_version=product.document_version,
                    product_id=product.product_id,
                    section_path=product.section,
                    text=text,
                    effective_from=product.effective_from,
                    effective_to=product.effective_to,
                    active=product.active,
                    segments=product.segments,
                    access_scope=product.access_scope,
                    content_hash=_sha256(text.encode("utf-8")),
                    risk_level=product.risk_level,
                    source_label=product.source_label,
                    data_label=product.data_label,
                    internal_required=product.internal_required,
                    branch_behavior=product.branch_behavior,
                    source_date=product.source_date,
                )
            )
        except ValidationError as exc:
            errors.append(f"row={row_number}: {exc.errors()[0]['msg']}")
    report = IngestReport(
        dataset_version=str(payload.get("dataset_version", "unknown")),
        source_path=str(source),
        source_hash=_sha256(raw),
        accepted=accepted,
        rejected=len(errors),
        indexed=len(chunks),
        errors=errors,
    )
    return chunks, report
