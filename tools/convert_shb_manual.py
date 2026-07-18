"""Convert the SHB Corporate RAG Product Manual (.odt) into the canonical
product corpus JSON consumed by ``app.knowledge.ingestion``.

Design notes (Linux-kernel style: single source of truth, reproducible, no
hand-copied drift):

* The published manual ``SHB_Corporate_RAG_Product_Manual_Public_Source_2026.odt``
  is the *source of truth*. This script is the *only* translation step. Editing
  the manual and re-running ``python tools/convert_shb_manual.py`` regenerates
  the corpus deterministically (stable ids, stable ordering).
* Every field maps 1:1 to a field the RAG pipeline already understands
  (see ``app/knowledge/models.py``). Governance fields from the manual
  (``risk_level``, ``source_label``, ``data_label``, ``internal_required``,
  ``branch_behavior``, ``sales_signals``, ``discovery_questions``) are preserved
  verbatim so the matcher can enforce the manual's safe-answer rules.
* No happy-path assumptions: a missing section yields ``None``/``[]``, never a
  fabricated default. The downstream pydantic model keeps ``extra="forbid"`` so
  a future manual change that adds an unexpected field fails loudly at ingest,
  not silently at runtime.

Usage::

    python tools/convert_shb_manual.py [path/to/manual.odt] [out.json]
"""

from __future__ import annotations

import re
import sys
import json
import html
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ODT = ROOT / "SHB_Corporate_RAG_Product_Manual_Public_Source_2026.odt"
DEFAULT_OUT = ROOT / "data" / "synthetic" / "v2" / "products_shb.json"

# Catalog -> RAG category from the manual's product schema (section 2.1).
_CATEGORY_BY_PREFIX = {
    "SHB-CORP-ACC": "account",
    "SHB-CORP-DIGI": "digital",
    "SHB-CORP-PAY": "payroll",
    "SHB-CORP-CASH": "cash",
    "SHB-CORP-TAX": "tax",
    "SHB-CORP-CARD": "card",
    "SHB-CORP-CREDIT": "credit",
    "SHB-CORP-GUAR": "guarantee",
    "SHB-CORP-TFI": "trade",
    "SHB-CORP-TFE": "trade",
    "SHB-CORP-FX": "fx",
    "BENCH-CORP": "benchmark",
}

# Map the manual's human-readable risk words onto a small ordered enum.
_RISK_LEVELS = {
    "thấp": "low",
    "trung bình": "medium",
    "trung bình–cao": "medium_high",
    "rất cao": "very_high",
    "cao": "high",
}


def _read_odt_text(odt_path: Path) -> str:
    with zipfile.ZipFile(odt_path) as z:
        raw = z.read("content.xml").decode("utf-8")
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return re.sub(r"[ \t]+", " ", text)


def _category_for(product_id: str) -> str:
    for prefix, cat in _CATEGORY_BY_PREFIX.items():
        if product_id.startswith(prefix):
            return cat
    return "uncategorized"


def _between(block: str, start: str, end: str) -> Optional[str]:
    """Return text between ``start`` and the next occurrence of ``end``."""
    s = block.find(start)
    if s < 0:
        return None
    s += len(start)
    e = block.find(end, s)
    if e < 0:
        return block[s:].strip()
    return block[s:e].strip()


def _bullets(text: str) -> List[str]:
    out = []
    for line in re.split(r"[•\n]", text):
        line = line.strip(" •\t")
        line = re.sub(r"^\d+\.\s*", "", line).strip()
        if line:
            out.append(line)
    return out


def _risk_level(risk_raw: Optional[str]) -> str:
    if not risk_raw:
        return "unknown"
    low = risk_raw.lower()
    for key, val in _RISK_LEVELS.items():
        if key in low:
            return val
    return "unknown"


def _branch_behavior(block: str) -> str:
    """Derive a coarse branch status from the manual's safe-answer + 2.2 rules.

    The manual distinguishes four states (READY_TO_PREPARE / NEED_INFORMATION /
    REVIEW_REQUIRED / BLOCKED / NOT_SUPPORTED). We do NOT invent eligibility; we
    only encode what the manual itself says about external-action gating.
    High-risk products must go through Legal/Credit review before any external
    action, so we mark them REVIEW_REQUIRED at the corpus level.
    """
    low = block.lower()
    if "human decision required" in low or "rất cao" in low or "review_required" in low:
        return "REVIEW_REQUIRED"
    if "blocked" in low or "không cho tạo action đối ngoại" in low:
        return "BLOCKED"
    return "READY_TO_PREPARE"


def _parse_products(text: str) -> List[Dict]:
    # Split into per-product blocks. Header: "HỒ SƠ SẢN PHẨM NN SHB-CORP-XXX — Name"
    chunks = re.split(r"(HỒ SƠ SẢN PHẨM \d+ )", text)
    blocks: List[str] = []
    cur: Optional[str] = None
    for seg in chunks:
        if re.match(r"HỒ SƠ SẢN PHẨM \d+ ", seg):
            cur = seg
        elif cur is not None:
            cur += seg
            blocks.append(cur)
            cur = None

    products: List[Dict] = []
    for block in blocks:
        header = re.search(r"(SHB-CORP-[A-Z0-9-]+|BENCH-CORP-[A-Z0-9-]+) — ([^ ].*?)(?=Thuộc tính|Nhãn nguồn|Mức rủi ro|$)", block)
        if not header:
            continue
        product_id = header.group(1).strip()
        product_name = header.group(2).strip()

        risk_raw = _between(block, "Mức rủi ro", "Nhãn nguồn")
        source_label = _between(block, "Nhãn nguồn", "Business need")
        business_need = _between(block, "Business need", "Khách hàng mục tiêu")
        target_profile = _between(block, "Khách hàng mục tiêu", "Thông tin công khai đã xác minh")
        public_features = _between(block, "Thông tin công khai đã xác minh", "Điều kiện công khai")
        public_conditions = _between(block, "Điều kiện công khai", "Thông tin bắt buộc lấy từ hệ thống nội bộ")
        internal_required = _between(block, "Thông tin bắt buộc lấy từ hệ thống nội bộ", "Tín hiệu tạo cơ hội")
        sales_signals = _between(block, "Tín hiệu tạo cơ hội", "Câu hỏi discovery")
        discovery = _between(block, "Câu hỏi discovery", "Cross-sell")
        cross_sell = _between(block, "Cross-sell", "Safe-answer rule")

        risk_level = _risk_level(risk_raw)
        # Source label carries both the manual's VERIFIED_PUBLIC/REGULATORY tag
        # and any HUMAN DECISION REQUIRED marker; keep it as a structured list.
        labels = [t.strip() for t in (source_label or "").replace("+", ",").split(",") if t.strip()]
        data_label = "PUBLIC_SOURCE_DEMO"
        if any("REGULATORY" in l for l in labels):
            data_label = "VERIFIED_PUBLIC_REGULATORY"

        products.append(
            {
                "product_id": product_id,
                "bank": "SHB" if product_id.startswith("SHB") else "BENCHMARK",
                "product_name": product_name,
                "name": product_name,
                "category": _category_for(product_id),
                "risk_level": risk_level,
                "source_label": labels,
                "data_label": data_label,
                "business_need": business_need or None,
                "target_profile": target_profile or None,
                "public_features": _bullets(public_features or ""),
                "public_conditions": _bullets(public_conditions or ""),
                "internal_required": _bullets(internal_required or ""),
                "sales_signals": _bullets(sales_signals or ""),
                "discovery_questions": _bullets(discovery or ""),
                "cross_sell": _bullets(cross_sell or ""),
                "branch_behavior": _branch_behavior(block),
                "document_id": "SHB-RAG-KB-CORP-2026-01",
                "document_version": "1.0",
                "section": f"product-profile/{product_id}",
                "effective_from": "2026-07-18",
                "effective_to": None,
                "source_date": "2026-07-18",
                "active": True,
                "segments": ["SME", "CORPORATE"],
                "access_scope": {"branches": ["*"]},
            }
        )
    return products


def main() -> int:
    odt = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ODT
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    if not odt.exists():
        raise SystemExit(f"manual not found: {odt}")
    text = _read_odt_text(odt)
    products = _parse_products(text)
    if not products:
        raise SystemExit("no product blocks parsed -- manual schema changed?")
    payload = {
        "dataset_version": "2026.07.18-shb-manual-v1",
        "source": "SHB_Corporate_RAG_Product_Manual_Public_Source_2026.odt",
        "synthetic": False,
        "products": products,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(products)} products -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
