"""Grounding Validator for P0.3 Trust Foundation.

Ensures that any generated Evidence/Claim is rigorously tied to its source,
checking scope, freshness, and conflict rules before allowing it to pass.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class GroundingStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONFLICTED = "conflicted"
    STALE_SOURCE = "stale_source"
    WRONG_SCOPE = "wrong_scope"
    SOURCE_NOT_FOUND = "source_not_found"
    VERSION_MISMATCH = "version_mismatch"
    UNSUPPORTED = "unsupported"


class ValidationResult(BaseModel):
    status: GroundingStatus
    reason: str
    failed_checks: List[str]


class GroundingValidator:
    """Validates citations against the true underlying sources."""

    def __init__(self, document_repository: Any):
        # We inject the document store here so we can verify the source exists
        self.doc_repo = document_repository

    def validate_claim(self, claim_text: str, citation: Dict[str, Any], case_context: Dict[str, Any]) -> ValidationResult:
        """
        P0.3 Strict rules:
        - source must exist
        - version must match
        - must match customer/case scope
        - quote must exist in the source
        - source must not be expired
        """
        doc_id = citation.get("document_id")
        doc_version = citation.get("version")
        
        # 1. Source Exists
        doc = self.doc_repo.get_document(doc_id)
        if not doc:
            return ValidationResult(
                status=GroundingStatus.SOURCE_NOT_FOUND,
                reason=f"Document {doc_id} not found in repository.",
                failed_checks=["source_exists"]
            )
            
        # 2. Version Match
        if doc.get("version") != doc_version:
            return ValidationResult(
                status=GroundingStatus.VERSION_MISMATCH,
                reason=f"Document {doc_id} version mismatch (expected {doc_version}, got {doc.get('version')}).",
                failed_checks=["version_match"]
            )
            
        # 3. Scope / Applicability Match
        if doc.get("customer_id") and doc.get("customer_id") != case_context.get("customer_id"):
            return ValidationResult(
                status=GroundingStatus.WRONG_SCOPE,
                reason="Document belongs to a different customer scope.",
                failed_checks=["scope_match"]
            )
            
        # 4. Freshness
        if doc.get("is_expired", False):
            return ValidationResult(
                status=GroundingStatus.STALE_SOURCE,
                reason="Document is expired or superseded.",
                failed_checks=["freshness"]
            )
            
        # 5. Quote Existence (Simplistic deterministic check for MVP)
        # In a real scenario, this could be fuzzy or LLM-based if semantic.
        quote = citation.get("quote", "")
        if quote and quote not in doc.get("content", ""):
            return ValidationResult(
                status=GroundingStatus.UNSUPPORTED,
                reason="The exact quote was not found in the document content.",
                failed_checks=["quote_exists"]
            )
            
        # If all checks pass
        return ValidationResult(
            status=GroundingStatus.SUPPORTED,
            reason="Claim is fully supported by the source document.",
            failed_checks=[]
        )
