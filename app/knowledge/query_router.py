"""Query Router -- RAG & Guardrail Implementation Plan Phase 3 section 22.

Pure rule-based strategy selection from a QueryUnderstandingResult +
AgentType. No ML/LLM routing model -- the prompt's own rule table is
fully deterministic (ID -> exact first, Legal condition -> policy first,
etc.), so a learned router would be solving a problem this repo's corpus
size (dozens of records) does not justify.
"""

from __future__ import annotations

from enum import Enum

from app.knowledge.query_understanding import QueryUnderstandingResult
from app.knowledge.retrieval_contracts import AgentType


class RetrievalStrategy(str, Enum):
    EXACT_ONLY = "EXACT_ONLY"
    SPARSE_ONLY = "SPARSE_ONLY"
    DENSE_ONLY = "DENSE_ONLY"
    HYBRID_RRF = "HYBRID_RRF"
    STRUCTURED_PLUS_HYBRID = "STRUCTURED_PLUS_HYBRID"
    POLICY_FIRST = "POLICY_FIRST"
    EVIDENCE_FIRST = "EVIDENCE_FIRST"
    DOCUMENT_LOCAL = "DOCUMENT_LOCAL"
    MULTI_HOP = "MULTI_HOP"
    ABSTAIN = "ABSTAIN"


def route_query(understanding: QueryUnderstandingResult, agent_type: AgentType) -> RetrievalStrategy:
    if "empty_query" in understanding.ambiguity:
        return RetrievalStrategy.ABSTAIN

    if understanding.multi_hop:
        return RetrievalStrategy.MULTI_HOP

    # "ID chuẩn -> exact first": a query that resolved to a known ID and
    # nothing else (no free-text signal beyond the ID itself) can be
    # answered by exact lookup alone.
    if understanding.exact_lookup_required and len(understanding.normalized_query.split()) <= 3:
        return RetrievalStrategy.EXACT_ONLY

    # "Legal condition -> policy first"
    if agent_type == AgentType.LEGAL_POLICY and understanding.task_type == "eligibility_check":
        return RetrievalStrategy.POLICY_FIRST

    # "Customer-specific conclusion -> evidence first" -- proxied by task_type
    # document_lookup, since this repo's QueryUnderstandingResult has no
    # separate "is about a specific customer's evidence" signal without a
    # customer_id already being present on the request (checked by the
    # caller, not this pure function).
    if understanding.task_type == "document_lookup":
        return RetrievalStrategy.EVIDENCE_FIRST

    # "Product exploration -> structured customer facts + hybrid catalog"
    if agent_type == AgentType.PRODUCT and understanding.task_type == "product_discovery":
        return RetrievalStrategy.STRUCTURED_PLUS_HYBRID if understanding.exact_lookup_required else RetrievalStrategy.HYBRID_RRF

    if understanding.exact_lookup_required:
        return RetrievalStrategy.STRUCTURED_PLUS_HYBRID

    return RetrievalStrategy.HYBRID_RRF
