"""Evidence Verification — exact match for fee/limit, semantic for claims."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from mcp_common.llm_client import get_gemma_client, deterministic_semantic_score
from mcp_common.config import settings
from mcp_common.schemas import EvidenceItem

# Import worktree catalog
from servers.product_agent.product.matcher import SHB_PRODUCT_CATALOG


class EvidenceVerifier:
    """Validate every important claim has grounded evidence."""

    def __init__(self):
        self._gemma = get_gemma_client()
        self._sources = self._build_sources()

    def _build_sources(self) -> Dict[Tuple[str, str], str]:
        from app.tools.legal_tools import SYNTHETIC_COMPLIANCE_POLICIES

        sources: Dict[Tuple[str, str], str] = {}
        for product in SHB_PRODUCT_CATALOG.values():
            meta = product["source_metadata"]
            sources[(meta["document"], meta["section"])] = " ".join([
                product["name"],
                product["description"],
                product["eligibility_rules"],
                " ".join(product["required_documents"]),
            ])
        for policy in SYNTHETIC_COMPLIANCE_POLICIES.values():
            sources[(policy["document"], policy["section"])] = policy["text"]
        return sources

    def verify(self, evidences: List[EvidenceItem]) -> Tuple[List[EvidenceItem], Dict[str, Any]]:
        """Return updated evidences with is_valid + summary."""
        valid = 0
        invalid = 0
        updated = []

        for ev in evidences:
            key = (ev.source_document_id, ev.section_or_page)
            source_text = self._sources.get(key, "")

            # Exact match required for fee/limit/numeric claims
            is_numeric_claim = any(kw in ev.claim.lower() for kw in ["phí", "hạn mức", "lãi suất", "fee", "limit", "rate", "%"])

            if is_numeric_claim:
                ev.is_valid = bool(source_text and ev.quote.strip() and ev.quote.strip() in source_text)
            else:
                # Semantic support for qualitative claims
                if source_text and ev.quote.strip():
                    score = self._semantic_support(ev.quote, source_text)
                    ev.is_valid = score >= settings.EVIDENCE_SEMANTIC_THRESHOLD
                    ev.validation_score = score
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

Trả lời CHỈ một số 0.0-1.0 (ví dụ: 0.85)."""
                resp = self._gemma.generate_sync(prompt, temperature=0.0, max_output_tokens=8)
                return float(resp.strip())
            except Exception:
                pass
        return deterministic_semantic_score(claim, source)