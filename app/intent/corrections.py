"""Context correction and downstream invalidation helpers."""

from __future__ import annotations

from typing import Dict, List

_IMPACT_GRAPH: Dict[str, List[str]] = {
    "customer_id": ["context", "intent", "product", "eligibility", "evidence", "operations"],
    "case_id": ["context", "intent", "workflow", "operations"],
    "product_ids": ["product", "eligibility", "evidence", "operations"],
    "requested_amount": ["intent", "eligibility", "operations"],
    "documents": ["eligibility", "evidence", "operations"],
    "recipient": ["operations", "approval"],
}


def impacted_nodes(field: str) -> List[str]:
    return list(_IMPACT_GRAPH.get(field, ["intent", "workflow"]))

