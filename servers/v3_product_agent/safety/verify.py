"""V3 Evidence Verification — exact match for fee/limit, semantic for claims.

V3 Principles (§11):
- Fee/limit/numeric claims → exact match required
- Qualitative claims → semantic support score ≥ threshold
- Every claim must have valid evidence before approval
- Hallucination flag for invalid claims
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from mcp_common.config import settings
from mcp_common.llm_client import get_gemma_client, deterministic_semantic_score
from mcp_common.schemas import EvidenceItem, ValidationMethod


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

    def verify(self, evidences: List[EvidenceItem]) -> Tuple[List[EvidenceItem], Dict[str, Any]]:
        """Return updated evidences with is_valid + summary."""
        valid = 0
        invalid = 0
        updated = []

        for ev in evidences:
            key = (ev.source_document_id, ev.section_or_page)
            source_text = self._sources.get(key, "")

            # Exact match required for numeric claims (fee, limit, rate)
            is_numeric_claim = any(
                kw in ev.claim.lower()
                for kw in ["phí", "hạn mức", "lãi suất", "fee", "limit", "rate", "%"]
            )

            if is_numeric_claim:
                ev.is_valid = bool(
                    source_text
                    and ev.quote.strip()
                    and ev.quote.strip() in source_text
                )
                ev.validation_method = ValidationMethod.EXACT_MATCH
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