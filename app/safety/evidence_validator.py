"""Independent deterministic citation validation against controlled sources."""

from __future__ import annotations

from typing import Dict, Tuple

from app.schemas.state import SharedCaseState
from app.tools.legal_tools import SYNTHETIC_COMPLIANCE_POLICIES
from app.tools.product_tools import SHB_PRODUCT_CATALOG


class EvidenceValidator:
    def __init__(self) -> None:
        self._sources = self._build_sources()

    def validate(self, state: SharedCaseState) -> Dict[str, int | bool]:
        valid = 0
        invalid = 0
        for evidence in state.evidences:
            key = (evidence.source_doc, evidence.page_or_section)
            source_text = self._sources.get(key, "")
            evidence.is_valid = bool(source_text and evidence.quote.strip() and evidence.quote.strip() in source_text)
            if evidence.is_valid:
                valid += 1
            else:
                invalid += 1
                state.audit_log.append(
                    {
                        "actor": "EvidenceValidator",
                        "action": "hallucination_flag",
                        "result": {"claim": evidence.claim, "source_doc": evidence.source_doc},
                    }
                )
        result = {"valid": valid, "invalid": invalid, "all_valid": invalid == 0 and valid > 0}
        state.audit_log.append({"actor": "EvidenceValidator", "action": "validate_evidence", "result": result})
        return result

    @staticmethod
    def _build_sources() -> Dict[Tuple[str, str], str]:
        sources: Dict[Tuple[str, str], str] = {}
        for product in SHB_PRODUCT_CATALOG.values():
            metadata = product["source_metadata"]
            sources[(metadata["document"], metadata["section"])] = " ".join(
                [
                    product["name"],
                    product["description"],
                    product["eligibility_rules"],
                    " ".join(product["required_documents"]),
                ]
            )
        for policy in SYNTHETIC_COMPLIANCE_POLICIES.values():
            sources[(policy["document"], policy["section"])] = policy["text"]
        return sources

