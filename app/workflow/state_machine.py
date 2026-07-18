"""Centralized case status transition validation."""

from __future__ import annotations

from app.schemas.v2.shared_case_state import CaseStatus


class InvalidTransitionError(ValueError):
    pass


ALLOWED = {
    CaseStatus.NEW: {CaseStatus.UNDERSTANDING},
    CaseStatus.UNDERSTANDING: {CaseStatus.CLARIFICATION_REQUIRED, CaseStatus.PLANNED, CaseStatus.COMPLETED, CaseStatus.FAILED},
    CaseStatus.CLARIFICATION_REQUIRED: {CaseStatus.UNDERSTANDING, CaseStatus.REJECTED},
    CaseStatus.PLANNED: {CaseStatus.IN_ANALYSIS, CaseStatus.FAILED},
    CaseStatus.IN_ANALYSIS: {
        CaseStatus.PENDING_INFORMATION, CaseStatus.PENDING_REVIEW,
        CaseStatus.PENDING_APPROVAL, CaseStatus.FAILED,
    },
    CaseStatus.PENDING_INFORMATION: {CaseStatus.IN_ANALYSIS, CaseStatus.REJECTED},
    CaseStatus.PENDING_REVIEW: {CaseStatus.IN_ANALYSIS, CaseStatus.PENDING_APPROVAL, CaseStatus.REJECTED},
    CaseStatus.PENDING_APPROVAL: {CaseStatus.EXECUTING, CaseStatus.REJECTED, CaseStatus.IN_ANALYSIS},
    CaseStatus.EXECUTING: {CaseStatus.COMPLETED, CaseStatus.FAILED},
    CaseStatus.FAILED: {CaseStatus.IN_ANALYSIS, CaseStatus.REJECTED},
    CaseStatus.COMPLETED: set(),
    CaseStatus.REJECTED: set(),
}


def transition(current: CaseStatus, target: CaseStatus) -> CaseStatus:
    if target not in ALLOWED[current]:
        raise InvalidTransitionError(f"invalid transition: {current.value} -> {target.value}")
    return target
