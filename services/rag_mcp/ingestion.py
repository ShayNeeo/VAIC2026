"""Validated, structure-aware and atomic ingestion for the MCP demo corpus."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from services.rag_mcp.config import ROOT
from services.rag_mcp.embedding import EmbeddingProvider
from services.rag_mcp.schemas import IngestSummary
from services.rag_mcp.store import RagStore


MANIFEST_PATH = ROOT / "data" / "rag_mcp_corpus" / "v1" / "manifest.json"
DATA_ROOT = (ROOT / "data").resolve()
SYNTHETIC_PREFIX = "DỮ LIỆU MÔ PHỎNG - KHÔNG DÙNG LÀM QUYẾT ĐỊNH THẬT"
INJECTION_MARKERS = (
    "ignore previous instructions",
    "bỏ qua chỉ dẫn trước",
    "reveal system prompt",
    "bypass approval",
    "call crm tool",
)


class IngestionError(ValueError):
    pass


def _quality_template() -> Dict[str, int]:
    return {
        "manifest_checks": 0,
        "source_card_checks": 0,
        "utf8_files": 0,
        "schema_checks": 0,
        "uniqueness_checks": 0,
        "reference_checks": 0,
        "effective_date_checks": 0,
        "injection_checks": 0,
        "rows_validated": 0,
        "chunks_built": 0,
    }


def _resolve_data_path(relative_path: str) -> Path:
    path = (ROOT / relative_path).resolve()
    if not path.is_relative_to(DATA_ROOT):
        raise IngestionError(f"source path is outside governed data root: {relative_path}")
    if not path.exists() or not path.is_file():
        raise IngestionError(f"source file not found: {relative_path}")
    return path


def _read_utf8(path: Path, quality: Dict[str, int]) -> tuple[str, bytes]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IngestionError(f"invalid UTF-8 source: {path}") from exc
    quality["utf8_files"] += 1
    return text, raw


def _read_json(path: Path, quality: Dict[str, int]) -> tuple[Dict[str, Any], bytes]:
    text, raw = _read_utf8(path, quality)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise IngestionError(f"invalid JSON source: {path}") from exc
    if not isinstance(value, dict):
        raise IngestionError(f"JSON root must be an object: {path}")
    return value, raw


def _read_csv(path: Path, quality: Dict[str, int]) -> tuple[List[Dict[str, str]], bytes]:
    text, raw = _read_utf8(path, quality)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise IngestionError(f"CSV has no header: {path}")
    rows = [dict(row) for row in reader]
    if not rows:
        raise IngestionError(f"CSV contains no rows: {path}")
    return rows, raw


def _require_fields(rows: Sequence[Dict[str, str]], fields: Sequence[str], path: Path, quality: Dict[str, int]) -> None:
    available = set(rows[0]) if rows else set()
    missing = set(fields).difference(available)
    if missing:
        raise IngestionError(f"{path.name} missing columns: {sorted(missing)}")
    quality["schema_checks"] += 1


def _require_unique(rows: Sequence[Dict[str, str]], fields: Sequence[str], path: Path, quality: Dict[str, int]) -> None:
    seen: set[tuple[str, ...]] = set()
    for row in rows:
        key = tuple(str(row.get(field, "")).strip() for field in fields)
        if not all(key) or key in seen:
            raise IngestionError(f"{path.name} has blank/duplicate key {fields}: {key}")
        seen.add(key)
    quality["uniqueness_checks"] += 1


def _require_synthetic(rows: Sequence[Dict[str, str]], path: Path) -> None:
    if any(str(row.get("synthetic_flag", "")).lower() != "true" for row in rows):
        raise IngestionError(f"non-synthetic row found in demo corpus: {path.name}")


def _validate_dates(start: str, end: str | None, label: str, quality: Dict[str, int]) -> None:
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end) if end else None
    except ValueError as exc:
        raise IngestionError(f"invalid effective date at {label}") from exc
    if end_date and start_date > end_date:
        raise IngestionError(f"effective_from is after effective_to at {label}")
    quality["effective_date_checks"] += 1


def _validate_card(card: Dict[str, Any], path: Path, quality: Dict[str, int]) -> None:
    required = (
        "source_id",
        "name",
        "domain",
        "tier",
        "dataset_version",
        "effective_from",
        "owner",
    )
    if any(not card.get(field) for field in required):
        raise IngestionError(f"source card is incomplete: {path}")
    if card.get("domain") not in {"product", "legal", "credit", "operations"}:
        raise IngestionError(f"unsupported source domain: {card.get('domain')}")
    if not card.get("governance", {}).get("approved"):
        raise IngestionError(f"source card is not approved: {path}")
    if card.get("lifecycle_status") != "ACTIVE":
        raise IngestionError(f"source card is not active: {path}")
    if card.get("tier") != "E_SYNTHETIC":
        raise IngestionError(f"demo corpus only accepts E_SYNTHETIC sources: {path}")
    _validate_dates(card["effective_from"], card.get("effective_to"), card["source_id"], quality)
    quality["source_card_checks"] += 1


def _safe_text(parts: Iterable[Any], quality: Dict[str, int]) -> str:
    body = " | ".join(str(part).strip() for part in parts if part not in (None, "", [], {}))
    lowered = body.lower()
    if any(marker in lowered for marker in INJECTION_MARKERS):
        raise IngestionError("source content failed prompt-injection quarantine")
    quality["injection_checks"] += 1
    return f"{SYNTHETIC_PREFIX} | {body}"


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:120]


def _source_hash(files: Sequence[tuple[Path, bytes]]) -> str:
    digest = hashlib.sha256()
    for path, raw in sorted(files, key=lambda item: str(item[0])):
        digest.update(str(path.relative_to(ROOT)).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(raw)
        digest.update(b"\0")
    return digest.hexdigest()


def _base_chunk(
    *,
    card: Dict[str, Any],
    source_hash: str,
    chunk_id: str,
    document_id: str,
    section_path: str,
    chunk_type: str,
    text: str,
    embedding: EmbeddingProvider,
    product_id: str | None = None,
    effective_from: str | None = None,
    effective_to: str | None = None,
    active: bool = True,
    segments: Sequence[str] = (),
    branches: Sequence[str] = ("*",),
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "chunk_id": chunk_id,
        "source_id": card["source_id"],
        "domain": card["domain"],
        "document_id": document_id,
        "document_version": card["dataset_version"],
        "product_id": product_id,
        "section_path": section_path,
        "chunk_type": chunk_type,
        "text": text,
        "effective_from": effective_from or card["effective_from"],
        "effective_to": effective_to if effective_to is not None else card.get("effective_to"),
        "active": active,
        "segments": list(segments),
        "branches": list(branches) or ["*"],
        "sensitivity": card.get("governance", {}).get("sensitivity", "INTERNAL"),
        "owner": card["owner"].get("business_owner", "unknown"),
        "source_tier": card["tier"],
        "content_hash": content_hash,
        "vector": embedding.embed(text),
        "metadata": {
            "source_hash": source_hash,
            "dataset_version": card["dataset_version"],
            "decision_role": card.get("decision_role", "EVALUATION_ONLY"),
            "synthetic": True,
            "data_disclaimer": SYNTHETIC_PREFIX,
            **(metadata or {}),
        },
    }


def _markdown_sections(text: str) -> List[tuple[str, str, int, int]]:
    sections: List[tuple[str, str, int, int]] = []
    heading = "Document"
    body: List[str] = []
    start_line = 1

    def flush(end_line: int) -> None:
        content = "\n".join(line for line in body if line.strip()).strip()
        if content:
            blocks = [content[index : index + 1600] for index in range(0, len(content), 1600)]
            for block_index, block in enumerate(blocks, 1):
                suffix = f" / part {block_index}" if len(blocks) > 1 else ""
                sections.append((f"{heading}{suffix}", block, start_line, end_line))

    for line_no, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if match:
            flush(line_no - 1)
            heading = match.group(2).strip()
            body = []
            start_line = line_no
        else:
            body.append(line)
    flush(len(text.splitlines()))
    return sections


def _markdown_chunks(
    *,
    card: Dict[str, Any],
    source_hash: str,
    path: Path,
    text: str,
    embedding: EmbeddingProvider,
    quality: Dict[str, int],
    product_id: str | None,
    chunk_type: str,
) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    for index, (heading, body, start_line, end_line) in enumerate(_markdown_sections(text), 1):
        safe = _safe_text([heading, body], quality)
        chunks.append(
            _base_chunk(
                card=card,
                source_hash=source_hash,
                chunk_id=f"{card['domain']}:doc:{_slug(path.stem)}:{index:03d}",
                document_id=path.stem,
                section_path=f"{heading} [lines {start_line}-{end_line}]",
                chunk_type=chunk_type,
                text=safe,
                product_id=product_id,
                embedding=embedding,
                metadata={"source_file": str(path.relative_to(ROOT)).replace("\\", "/")},
            )
        )
    return chunks


def _validate_references(values: Iterable[str], known: set[str], label: str, quality: Dict[str, int]) -> None:
    unknown = sorted({value for value in values if value and value not in known})
    if unknown:
        raise IngestionError(f"unknown product reference in {label}: {unknown}")
    quality["reference_checks"] += 1


def _product_pack(
    card: Dict[str, Any], paths: Sequence[Path], source_hash: str, embedding: EmbeddingProvider,
    quality: Dict[str, int], known_products: set[str], raw_cache: Dict[Path, tuple[str, bytes]],
) -> List[Dict[str, Any]]:
    by_name = {path.name: path for path in paths}
    products_path = by_name["products.csv"]
    products, _ = _read_csv(products_path, quality)
    _require_fields(
        products,
        [
            "product_id", "product_name", "product_type", "description", "target_segment",
            "status", "branches", "synthetic_flag",
        ],
        products_path,
        quality,
    )
    _require_unique(products, ["product_id"], products_path, quality)
    _require_synthetic(products, products_path)
    chunks: List[Dict[str, Any]] = []
    for row in products:
        product_id = row["product_id"]
        text = _safe_text(
            [
                product_id,
                row["product_name"],
                f"Loại: {row['product_type']}",
                row["description"],
                f"Phân khúc: {row['target_segment']}",
                f"Tính năng: {row.get('key_features', '')}",
                f"Điều kiện đầu vào: {row.get('prerequisites', '')}",
                f"Tiền tệ: {row.get('supported_currencies', '')}",
                f"Doanh thu tham chiếu tối thiểu: {row.get('minimum_revenue_vnd', '')} VND",
            ],
            quality,
        )
        chunks.append(
            _base_chunk(
                card=card,
                source_hash=source_hash,
                chunk_id=f"product:master:{_slug(product_id)}",
                document_id="SYN-PRODUCT-MASTER",
                section_path=product_id,
                chunk_type="product_master",
                text=text,
                product_id=product_id,
                active=row["status"].lower() == "active",
                segments=[row["target_segment"].upper()],
                branches=[value for value in row["branches"].split(";") if value],
                embedding=embedding,
                metadata={"source_file": "data/raw_csv_json/products.csv", "row_id": product_id},
            )
        )

    pricing_path = by_name["product_pricing_limits.csv"]
    pricing, _ = _read_csv(pricing_path, quality)
    _require_fields(
        pricing,
        ["pricing_id", "product_id", "segment", "currency", "fee_type", "effective_from", "effective_to", "synthetic_flag"],
        pricing_path,
        quality,
    )
    _require_unique(pricing, ["pricing_id"], pricing_path, quality)
    _require_synthetic(pricing, pricing_path)
    _validate_references((row["product_id"] for row in pricing), known_products, pricing_path.name, quality)
    for row in pricing:
        _validate_dates(row["effective_from"], row.get("effective_to") or None, row["pricing_id"], quality)
        text = _safe_text(
            [
                row["pricing_id"], row["product_id"], f"Phân khúc: {row['segment']}",
                f"Loại phí: {row['fee_type']}", f"Phí: {row.get('fee_amount')} {row['currency']}",
                f"Tỷ lệ phí: {row.get('fee_rate_pct')}%", f"Hạn mức tham chiếu: {row.get('limit_amount')} {row['currency']}",
                f"SLA: {row.get('sla_business_hours')} giờ làm việc", f"Triển khai: {row.get('implementation_days')} ngày",
            ],
            quality,
        )
        chunks.append(
            _base_chunk(
                card=card, source_hash=source_hash, chunk_id=f"product:pricing:{_slug(row['pricing_id'])}",
                document_id="SYN-PRICING-LIMITS", section_path=row["pricing_id"], chunk_type="product_pricing",
                text=text, product_id=row["product_id"], effective_from=row["effective_from"],
                effective_to=row.get("effective_to") or None, segments=[row["segment"].upper()], embedding=embedding,
                metadata={"source_file": "data/raw_csv_json/product_pricing_limits.csv", "row_id": row["pricing_id"]},
            )
        )

    bundles_path = by_name["solution_bundles.csv"]
    bundles, _ = _read_csv(bundles_path, quality)
    _require_fields(bundles, ["bundle_id", "bundle_name", "use_case", "product_ids", "synthetic_flag"], bundles_path, quality)
    _require_unique(bundles, ["bundle_id"], bundles_path, quality)
    _require_synthetic(bundles, bundles_path)
    for row in bundles:
        product_ids = [value for value in row["product_ids"].split(";") if value]
        _validate_references(product_ids, known_products, row["bundle_id"], quality)
        text = _safe_text(
            [
                row["bundle_id"], row["bundle_name"], f"Use case: {row['use_case']}",
                f"Sản phẩm: {row['product_ids']}", f"Lý do: {row.get('rationale')}",
                f"Kết quả kỳ vọng: {row.get('target_outcomes')}", f"Điểm nền mô phỏng: {row.get('base_match_score')}",
            ],
            quality,
        )
        chunks.append(
            _base_chunk(
                card=card, source_hash=source_hash, chunk_id=f"product:bundle:{_slug(row['bundle_id'])}",
                document_id="SYN-SOLUTION-BUNDLES", section_path=row["bundle_id"], chunk_type="solution_bundle",
                text=text, segments=[row.get("target_segment", "CORPORATE").upper()], embedding=embedding,
                metadata={"source_file": "data/raw_csv_json/solution_bundles.csv", "row_id": row["bundle_id"], "product_ids": product_ids},
            )
        )

    product_by_doc = {
        "Bieu_phi_dich_vu_Tai_tro_thuong_mai_XNK.md": "PRD-FX-001",
        "Huong_dan_quan_ly_dong_tien_Cash_Management.md": "PRD-CM-001",
        "The_le_dich_vu_chi_luong_Corporate_Online.md": "PRD-PY-001",
        "Huong_dan_tai_khoan_thanh_toan_doanh_nghiep.md": "PRD-CA-001",
        "Huong_dan_dich_vu_thu_ho_khoan_phai_thu.md": "PRD-CO-001",
        "Huong_dan_dich_vu_thanh_toan_nha_cung_cap.md": "PRD-PO-001",
    }
    for filename, product_id in product_by_doc.items():
        path = by_name[filename]
        text, _ = raw_cache[path]
        chunks.extend(
            _markdown_chunks(
                card=card, source_hash=source_hash, path=path, text=text, embedding=embedding,
                quality=quality, product_id=product_id, chunk_type="product_reference_document",
            )
        )
    return chunks


def _legal_pack(
    card: Dict[str, Any], paths: Sequence[Path], source_hash: str, embedding: EmbeddingProvider,
    quality: Dict[str, int], known_products: set[str], raw_cache: Dict[Path, tuple[str, bytes]],
) -> List[Dict[str, Any]]:
    by_name = {path.name: path for path in paths}
    policy_path = by_name["product_policies.csv"]
    policies, _ = _read_csv(policy_path, quality)
    _require_fields(
        policies,
        ["policy_id", "product_id", "rule_type", "condition_field", "operator", "rule_text", "effective_from", "version", "synthetic_flag"],
        policy_path,
        quality,
    )
    _require_unique(policies, ["policy_id"], policy_path, quality)
    _require_synthetic(policies, policy_path)
    _validate_references((row["product_id"] for row in policies), known_products, policy_path.name, quality)
    chunks: List[Dict[str, Any]] = []
    for row in policies:
        _validate_dates(row["effective_from"], row.get("effective_to") or None, row["policy_id"], quality)
        text = _safe_text(
            [
                row["policy_id"], row["product_id"], f"Loại rule: {row['rule_type']}",
                f"Điều kiện: {row['condition_field']} {row['operator']} {row.get('threshold_value')}",
                f"Mức độ: {row.get('severity')}", f"Evidence bắt buộc: {row.get('required_evidence')}", row["rule_text"],
            ],
            quality,
        )
        chunks.append(
            _base_chunk(
                card=card, source_hash=source_hash, chunk_id=f"legal:policy:{_slug(row['policy_id'])}",
                document_id="SYN-PRODUCT-POLICIES", section_path=row["policy_id"], chunk_type="legal_policy_rule",
                text=text, product_id=row["product_id"], effective_from=row["effective_from"],
                effective_to=row.get("effective_to") or None, embedding=embedding,
                metadata={
                    "source_file": "data/raw_csv_json/product_policies.csv", "row_id": row["policy_id"],
                    "rule_type": row["rule_type"], "severity": row.get("severity"), "rule_version": row["version"],
                },
            )
        )

    legal_docs = {
        "Quy_trinh_KYC_va_Mo_tai_khoan_doanh_nghiep.md": None,
        "Huong_dan_bao_lanh_ngan_hang_B2B.md": "PRD-GU-001",
    }
    for filename, product_id in legal_docs.items():
        path = by_name[filename]
        text, _ = raw_cache[path]
        chunks.extend(
            _markdown_chunks(
                card=card, source_hash=source_hash, path=path, text=text, embedding=embedding,
                quality=quality, product_id=product_id, chunk_type="legal_reference_document",
            )
        )
    return chunks


def _credit_pack(
    card: Dict[str, Any], paths: Sequence[Path], source_hash: str, embedding: EmbeddingProvider,
    quality: Dict[str, int], known_products: set[str], raw_cache: Dict[Path, tuple[str, bytes]],
) -> List[Dict[str, Any]]:
    """Build policy-only credit chunks; customer facilities never enter vector RAG."""

    by_name = {path.name: path for path in paths}
    chunks: List[Dict[str, Any]] = []
    product_id = "PRD-WC-001"
    _validate_references([product_id], known_products, "credit_reference_pack", quality)

    markdown_path = by_name["Quy_che_cho_vay_von_luu_dong_KHDN_SHB.md"]
    markdown, _ = raw_cache[markdown_path]
    chunks.extend(
        _markdown_chunks(
            card=card,
            source_hash=source_hash,
            path=markdown_path,
            text=markdown,
            embedding=embedding,
            quality=quality,
            product_id=product_id,
            chunk_type="credit_lending_policy",
        )
    )

    manual_path = by_name["shb_credit_policy_manual.json"]
    manual_text, _ = raw_cache[manual_path]
    manual = json.loads(manual_text)
    required = ("document_id", "version", "effective_from", "chapters")
    if any(not manual.get(field) for field in required):
        raise IngestionError("credit policy manual is incomplete")
    if "synthetic" not in str(manual.get("note", "")).lower():
        raise IngestionError("credit policy manual must disclose synthetic data")
    for chapter in manual.get("chapters", []):
        for article in chapter.get("articles", []):
            article_id = str(article.get("article_id"))
            text = _safe_text(
                [
                    manual.get("title"),
                    chapter.get("title"),
                    article_id,
                    article.get("title"),
                    article.get("text"),
                ],
                quality,
            )
            chunks.append(
                _base_chunk(
                    card=card,
                    source_hash=source_hash,
                    chunk_id=f"credit:manual:{_slug(article_id)}",
                    document_id=str(manual["document_id"]),
                    section_path=f"{chapter.get('chapter_id')} / {article_id}",
                    chunk_type="credit_policy_article",
                    text=text,
                    product_id=product_id,
                    effective_from=str(manual["effective_from"]),
                    effective_to=manual.get("effective_to"),
                    embedding=embedding,
                    metadata={
                        "source_file": str(manual_path.relative_to(ROOT)).replace("\\", "/"),
                        "article_id": article_id,
                        "rule_refs": sorted(
                            {
                                str(rule_ref)
                                for clause in article.get("clauses", [])
                                for rule_ref in clause.get("rule_refs", [])
                            }
                        ),
                    },
                )
            )
            for clause in article.get("clauses", []):
                clause_id = str(clause.get("clause_id"))
                clause_text = _safe_text(
                    [article_id, clause_id, clause.get("text"), f"Rule refs: {clause.get('rule_refs', [])}"],
                    quality,
                )
                chunks.append(
                    _base_chunk(
                        card=card,
                        source_hash=source_hash,
                        chunk_id=f"credit:manual:{_slug(article_id)}:{_slug(clause_id)}",
                        document_id=str(manual["document_id"]),
                        section_path=f"{chapter.get('chapter_id')} / {article_id} / {clause_id}",
                        chunk_type="credit_policy_clause",
                        text=clause_text,
                        product_id=product_id,
                        effective_from=str(manual["effective_from"]),
                        effective_to=manual.get("effective_to"),
                        embedding=embedding,
                        metadata={
                            "source_file": str(manual_path.relative_to(ROOT)).replace("\\", "/"),
                            "article_id": article_id,
                            "clause_id": clause_id,
                            "rule_refs": list(clause.get("rule_refs", [])),
                        },
                    )
                )
    quality["rows_validated"] += len(chunks)
    return chunks


def _operations_pack(
    card: Dict[str, Any], paths: Sequence[Path], source_hash: str, embedding: EmbeddingProvider,
    quality: Dict[str, int], known_products: set[str], _raw_cache: Dict[Path, tuple[str, bytes]],
) -> List[Dict[str, Any]]:
    specs = {
        "sop_workflows.csv": ("workflow_step", ("workflow_id", "step_no"), "workflow_id"),
        "checklist_definitions.csv": ("operations_checklist", ("checklist_item_id",), "checklist_item_id"),
        "sla_rules.csv": ("operations_sla", ("sla_rule_id",), "sla_rule_id"),
        "email_templates.csv": ("operations_template", ("template_id",), "template_id"),
        "raci_matrix.csv": ("operations_raci", ("raci_id",), "raci_id"),
    }
    chunks: List[Dict[str, Any]] = []
    for path in paths:
        chunk_type, key_fields, row_id_field = specs[path.name]
        rows, _ = _read_csv(path, quality)
        _require_fields(rows, [*key_fields, "synthetic_flag"], path, quality)
        _require_unique(rows, key_fields, path, quality)
        _require_synthetic(rows, path)
        if path.name == "checklist_definitions.csv":
            _validate_references((row["product_id"] for row in rows), known_products, path.name, quality)
        for row in rows:
            row_id = "-".join(row[field] for field in key_fields)
            display = [f"{key}: {value}" for key, value in row.items() if key not in {"source_id", "synthetic_flag"} and value]
            text = _safe_text(display, quality)
            product_id = row.get("product_id") or None
            active = str(row.get("active", "true")).lower() == "true"
            chunks.append(
                _base_chunk(
                    card=card, source_hash=source_hash,
                    chunk_id=f"operations:{_slug(path.stem)}:{_slug(row_id)}",
                    document_id=f"SYN-{path.stem.upper().replace('_', '-')}", section_path=row_id,
                    chunk_type=chunk_type, text=text, product_id=product_id, active=active, embedding=embedding,
                    metadata={"source_file": str(path.relative_to(ROOT)).replace("\\", "/"), "row_id": row.get(row_id_field, row_id)},
                )
            )
        quality["rows_validated"] += len(rows)
    return chunks


ADAPTERS = {
    "product_reference_pack": _product_pack,
    "legal_reference_pack": _legal_pack,
    "credit_reference_pack": _credit_pack,
    "operations_reference_pack": _operations_pack,
}


class BuiltinCorpusIngestor:
    def __init__(self, store: RagStore, embedding: EmbeddingProvider) -> None:
        self.store = store
        self.embedding = embedding

    def seed(self) -> IngestSummary:
        run_id = f"RAG-ING-{uuid.uuid4().hex.upper()}"
        started_at = datetime.now(timezone.utc).isoformat()
        quality = _quality_template()
        corpus_version = "unknown"
        try:
            manifest, _ = _read_json(MANIFEST_PATH, quality)
            for field in ("schema_version", "corpus_id", "dataset_version", "sources"):
                if not manifest.get(field):
                    raise IngestionError(f"corpus manifest missing {field}")
            if manifest.get("data_mode") != "SHB_ENTERPRISE_DATA":
                raise IngestionError("server requires SHB_ENTERPRISE_DATA manifest")
            corpus_version = str(manifest["dataset_version"])
            quality["manifest_checks"] += 1

            products_path = _resolve_data_path("data/raw_csv_json/products.csv")
            product_rows, _ = _read_csv(products_path, quality)
            _require_fields(product_rows, ["product_id", "synthetic_flag"], products_path, quality)
            _require_unique(product_rows, ["product_id"], products_path, quality)
            _require_synthetic(product_rows, products_path)
            known_products = {row["product_id"] for row in product_rows}

            packages: List[Tuple[Dict[str, Any], List[Dict[str, Any]]]] = []
            source_hashes: Dict[str, str] = {}
            by_domain: Dict[str, int] = {}
            all_chunk_ids: set[str] = set()

            for spec in manifest["sources"]:
                if not isinstance(spec, dict) or spec.get("adapter") not in ADAPTERS:
                    raise IngestionError(f"invalid corpus source adapter: {spec}")
                card_path = _resolve_data_path(str(spec["source_card"]))
                card, card_raw = _read_json(card_path, quality)
                _validate_card(card, card_path, quality)
                if card["dataset_version"] != corpus_version:
                    raise IngestionError(f"source/card version mismatch: {card['source_id']}")

                paths = [_resolve_data_path(str(value)) for value in spec.get("files", [])]
                if not paths:
                    raise IngestionError(f"source has no files: {card['source_id']}")
                raw_cache: Dict[Path, tuple[str, bytes]] = {}
                hashed_files: List[tuple[Path, bytes]] = [(card_path, card_raw)]
                for path in paths:
                    text, raw = _read_utf8(path, quality)
                    raw_cache[path] = (text, raw)
                    hashed_files.append((path, raw))
                source_hash = _source_hash(hashed_files)
                chunks = ADAPTERS[spec["adapter"]](
                    card, paths, source_hash, self.embedding, quality, known_products, raw_cache
                )
                if not chunks:
                    raise IngestionError(f"source produced no chunks: {card['source_id']}")
                for chunk in chunks:
                    if chunk["chunk_id"] in all_chunk_ids:
                        raise IngestionError(f"duplicate global chunk_id: {chunk['chunk_id']}")
                    all_chunk_ids.add(chunk["chunk_id"])
                    _validate_dates(
                        str(chunk["effective_from"]),
                        str(chunk["effective_to"]) if chunk.get("effective_to") else None,
                        chunk["chunk_id"],
                        quality,
                    )
                source = {
                    "source_id": card["source_id"],
                    "name": card["name"],
                    "domain": card["domain"],
                    "tier": card["tier"],
                    "sensitivity": card.get("governance", {}).get("sensitivity", "INTERNAL"),
                    "owner": card["owner"],
                    "dataset_version": corpus_version,
                    "source_hash": source_hash,
                    "active": True,
                }
                packages.append((source, chunks))
                source_hashes[card["source_id"]] = source_hash
                by_domain[card["domain"]] = by_domain.get(card["domain"], 0) + len(chunks)
                quality["chunks_built"] += len(chunks)

            quality["rows_validated"] += sum(1 for _ in all_chunk_ids)
            self.store.replace_corpus(
                packages,
                run_id=run_id,
                corpus_version=corpus_version,
                quality=quality,
                started_at=started_at,
            )
            return IngestSummary(
                run_id=run_id,
                status="passed",
                corpus_version=corpus_version,
                source_count=len(packages),
                chunk_count=sum(len(chunks) for _, chunks in packages),
                chunks_by_domain=by_domain,
                source_hashes=source_hashes,
                quality_checks=quality,
                rejected_chunk_count=0,
                warnings=[
                    "Synthetic corpus only; replace source cards and obtain owner approval before pilot."
                ],
            )
        except Exception as exc:
            self.store.record_ingestion_failure(
                run_id=run_id,
                corpus_version=corpus_version,
                started_at=started_at,
                quality=quality,
                error_message=str(exc),
            )
            if isinstance(exc, IngestionError):
                raise
            raise IngestionError(f"unexpected ingestion failure: {exc}") from exc
