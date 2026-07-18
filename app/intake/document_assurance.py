"""Document Assurance Pipeline for Evidence Validation.

Implements Phase 5 of the SHB Corporate Sales Copilot End-to-End Workflow.
Replaces naive validation with a stringent 3-gate pipeline:
1. Tampering/Fraud check
2. Completeness check
3. Relevance (matching expected requirement) check
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from app.schemas.v2.metadata import MetadataObject, MetadataVersion


class AssessmentStatus(str, Enum):
    PASS = "PASS"
    REJECT_FRAUD = "REJECT_FRAUD"
    REJECT_INCOMPLETE = "REJECT_INCOMPLETE"
    REJECT_IRRELEVANT = "REJECT_IRRELEVANT"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


@dataclass
class DocumentAssessment:
    assessment_id: str
    document_id: str
    status: AssessmentStatus
    fraud_score: float
    completeness_score: float
    relevance_score: float
    reason: str


class DocumentAssuranceService:
    def evaluate(self, document_id: str, document_bytes: bytes, expected_type: str, context: Optional[Dict[str, Any]] = None) -> DocumentAssessment:
        """Evaluates a document through the 3-gate assurance pipeline."""
        # 1. Tampering/Fraud Check (Mocked for MVP)
        fraud_score = self._check_tampering(document_bytes)
        if fraud_score > 0.8:
            return DocumentAssessment(
                assessment_id=f"ASSESS-{uuid.uuid4().hex[:8].upper()}",
                document_id=document_id,
                status=AssessmentStatus.REJECT_FRAUD,
                fraud_score=fraud_score,
                completeness_score=0.0,
                relevance_score=0.0,
                reason="High likelihood of digital tampering or forgery detected."
            )
            
        # 2. Completeness Check (Mocked for MVP)
        completeness_score = self._check_completeness(document_bytes, expected_type)
        if completeness_score < 0.5:
            return DocumentAssessment(
                assessment_id=f"ASSESS-{uuid.uuid4().hex[:8].upper()}",
                document_id=document_id,
                status=AssessmentStatus.REJECT_INCOMPLETE,
                fraud_score=fraud_score,
                completeness_score=completeness_score,
                relevance_score=0.0,
                reason=f"Document is missing key pages or signatures required for {expected_type}."
            )
            
        # 3. Relevance Check (Mocked for MVP)
        relevance_score = self._check_relevance(document_bytes, expected_type, context)
        if relevance_score < 0.6:
            return DocumentAssessment(
                assessment_id=f"ASSESS-{uuid.uuid4().hex[:8].upper()}",
                document_id=document_id,
                status=AssessmentStatus.REJECT_IRRELEVANT,
                fraud_score=fraud_score,
                completeness_score=completeness_score,
                relevance_score=relevance_score,
                reason=f"Document content does not match the expected requirement ({expected_type})."
            )

        # Passed all automated checks
        return DocumentAssessment(
            assessment_id=f"ASSESS-{uuid.uuid4().hex[:8].upper()}",
            document_id=document_id,
            status=AssessmentStatus.PASS,
            fraud_score=fraud_score,
            completeness_score=completeness_score,
            relevance_score=relevance_score,
            reason="Document passed automated assurance pipeline."
        )

    def _check_tampering(self, document_bytes: bytes) -> float:
        # MVP Mock: If it's a PDF, we assume it's fine unless specific marker
        if b"MOCK_FRAUD" in document_bytes:
            return 0.95
        return 0.05

    def _check_completeness(self, document_bytes: bytes, expected_type: str) -> float:
        # MVP Mock
        if b"MOCK_INCOMPLETE" in document_bytes:
            return 0.3
        return 0.9

    def _check_relevance(self, document_bytes: bytes, expected_type: str, context: Optional[Dict[str, Any]]) -> float:
        # MVP Mock
        if b"MOCK_IRRELEVANT" in document_bytes:
            return 0.2
        return 0.85
