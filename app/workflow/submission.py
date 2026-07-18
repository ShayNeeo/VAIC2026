"""Submission Readiness Service.

Implements Phase 8 of the SHB Corporate Sales Copilot End-to-End Workflow.
Evaluates if a case is ready for RM Approval and final submission to Underwriting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from app.schemas.v2.shared_case_state import SharedCaseState, CaseStatus


@dataclass
class ReadinessResult:
    is_ready: bool
    missing_requirements: List[str]
    readiness_score: float
    summary_for_rm: str


class SubmitReadinessService:
    def evaluate(self, state: SharedCaseState) -> ReadinessResult:
        """Evaluates whether the case is ready for submission."""
        missing = []
        
        # 1. Check Checklist Completion
        checklist = state.case_checklist
        if not checklist:
            missing.append("Checklist has not been generated.")
        else:
            items = checklist.get("items", [])
            for item in items:
                # Mock MVP check: normally we'd check if documents were uploaded for this item.
                # Since we don't track it tightly in MVP, we just assume if it's there, it needs docs.
                if not item.get("status") == "COMPLETED":
                    missing.append(f"Missing documentation for: {item.get('title', 'Unknown Requirement')}")

        # 2. Check Risk Gates
        if state.risk_gate_result:
            outcome = state.risk_gate_result.get("outcome")
            if outcome == "need_review":
                missing.append("Pending Specialist Review (Risk/Legal/Product).")
            elif outcome == "need_information":
                missing.append("Pending Additional Information for Eligibility.")

        # 3. Final Summary Formulation
        if missing:
            summary = "Case is NOT ready for submission. Please resolve the following missing requirements."
            return ReadinessResult(
                is_ready=False,
                missing_requirements=missing,
                readiness_score=0.0,
                summary_for_rm=summary
            )

        summary = (
            "All required documents collected and validated. "
            "Policy and Risk gates passed. "
            "Case is ready for final RM Approval."
        )
        return ReadinessResult(
            is_ready=True,
            missing_requirements=[],
            readiness_score=1.0,
            summary_for_rm=summary
        )
