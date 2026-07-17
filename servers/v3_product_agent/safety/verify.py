"""V3 Evidence Verification — exact match for fee/limit, semantic for claims.

V3 Principles (§11):
- Fee/limit/numeric claims → exact match required
- Qualitative claims → semantic support score ≥ threshold
- Every claim must have valid evidence before approval
- Hallucination flag for invalid claims
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from mcp_common.config import settings
from mcp_common.llm_client import get_gemma_client, deterministic_semantic_score
from mcp_common.schemas import EvidenceItem, ValidationMethod

from servers.v3_product_agent.product.catalog import V3_PRODUCT_CATALOG

#: Keywords that mark a numeric claim (fee / limit / rate).
NUMERIC_KEYWORDS = ("phí", "hạn mức", "lãi suất", "fee", "limit", "rate", "%")

#: Map a claim's fee keyword to the catalog ``fee.name`` it must match.
FEE_KEYWORD_MAP = {
    "lãi suất": "interest_rate",
    "interest_rate": "interest_rate",
    "rate": "interest_rate",
    "hạn mức": "limit",
    "limit": "limit",
    "phí": "fee",
    "fee": "fee",
}


class EvidenceVerifier:
    """Validate every important claim has grounded evidence (V3 §11)."""

    def __init__(self):
        self._gemma = get_gemma_client()
        self._sources = self._build_sources()

    def _build_sources(self) -> Dict[Tuple[str, str], str]:
        """Build source text lookup from catalog and policies."""
        from servers.v3_product_agent.product.catalog import V3_PRODUCT_CATALOG

        sources: Dict[Tuple[str, str], str] = {}
        for product in V3_PRODUCT_CATALOG.values():
            meta = product["source_metadata"]
            sources[(meta["document"], meta["section"])] = " ".join([
                product["name"],
                product["description"],
                product["eligibility_rules"],
                " ".join(p.document_type for p in product["prerequisites"]),
            ])
        # Synthetic compliance policies
        sources[("Compliance_Policy_v3.pdf", "Section_4.2")] = (
            "UBO declaration is mandatory for credit products. "
            "BCTC audited required for working capital."
        )
        sources[("SOP_v3.pdf", "Section_3.1")] = (
            "Checklist must include business registration, "
            "authorized representative, and product-specific documents."
        )
        return sources

    @staticmethod
    def _extract_number(text: str) -> "float | None":
        """First numeric token in a claim (handles `8.5 %` style)."""
        match = re.search(r"(\d+(?:[.,]\d+)?)", text)
        return float(match.group(1).replace(",", ".")) if match else None

    def _verify_numeric(self, ev: EvidenceItem, source_text: str) -> bool:
        """NUMERIC_EXACT: claim value+unit must match a catalog fee/limit.

        Resolution order (§11: no semantic for numbers):
        1. exact catalog fee lookup for the cited product section,
        2. substring quote match in source text.
        Fail closed when neither matches.
        """
        number = self._extract_number(ev.claim)
        if number is None:
            return bool(source_text and ev.quote.strip() and ev.quote.strip() in source_text)

        for pid, entry in V3_PRODUCT_CATALOG.items():
            if entry["source_metadata"]["section"] == ev.section_or_page:
                for fee in entry.get("fees_limits", []):
                    expected_name = None
                    for kw, name in FEE_KEYWORD_MAP.items():
                        if kw in ev.claim.lower():
                            expected_name = name
                            break
                    if expected_name and fee.name == expected_name and abs(fee.value - number) < 1e-6:
                        return True
        return bool(source_text and ev.quote.strip() and ev.quote.strip() in source_text)

    def verify(self, evidences: List[EvidenceItem]) -> Tuple[List[EvidenceItem], Dict[str, Any]]:
        """Return updated evidences with is_valid + summary."""
        valid = 0
        invalid = 0
        updated = []

        for ev in evidences:
            key = (ev.source_document_id, ev.section_or_page)
            source_text = self._sources.get(key, "")

            # Exact match required for numeric claims (fee, limit, rate)
            is_numeric_claim = any(kw in ev.claim.lower() for kw in NUMERIC_KEYWORDS)

            if is_numeric_claim:
                # Fee/limit/rate -> exact numeric match (§11: no semantic for numbers)
                ev.is_valid = self._verify_numeric(ev, source_text)
                ev.validation_method = ValidationMethod.NUMERIC_EXACT
                ev.validation_score = 1.0 if ev.is_valid else 0.0
            else:
                # Semantic support for qualitative claims
                if source_text and ev.quote.strip():
                    score = self._semantic_support(ev.quote, source_text)
                    ev.is_valid = score >= settings.EVIDENCE_SEMANTIC_THRESHOLD
                    ev.validation_score = score
                    ev.validation_method = ValidationMethod.SEMANTIC_SUPPORT
                else:
                    ev.is_valid = False

            if ev.is_valid:
                valid += 1
            else:
                invalid += 1

            updated.append(ev)

        summary = {
            "valid": valid,
            "invalid": invalid,
            "all_valid": invalid == 0 and valid > 0,
        }
        return updated, summary

    def _semantic_support(self, claim: str, source: str) -> float:
        """Gemma semantic support score or deterministic fallback."""
        if settings.USE_GEMMA_FOR_VERIFY:
            try:
                prompt = f"""Đánh giá claim có được hỗ trợ bởi source không?
Claim: "{claim}"
Source: "{source[:1500]}"

Chỉ trả về số 0.0-1.0 (ví dụ: 0.85)."""
                resp = self._gemma.generate_sync(prompt, temperature=0.0, max_output_tokens=8)
                return float(resp.strip())
            except Exception:
                pass
        return deterministic_semantic_score(claim, source)