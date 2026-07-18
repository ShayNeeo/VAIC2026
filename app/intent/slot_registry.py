"""Stage-aware slot requirements for V2 intents."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Set


class WorkflowStage(str, Enum):
    UNDERSTANDING = "understanding"
    RETRIEVAL = "retrieval"
    ELIGIBILITY = "eligibility"
    EXTERNAL_ACTION = "external_action"


SLOT_REQUIREMENTS: Dict[str, Dict[WorkflowStage, Set[str]]] = {
    "find_product": {
        WorkflowStage.UNDERSTANDING: {"objective"},
        WorkflowStage.RETRIEVAL: {"customer_id", "objective"},
        WorkflowStage.ELIGIBILITY: {"customer_id", "product_ids"},
        WorkflowStage.EXTERNAL_ACTION: {"customer_id", "product_ids"},
    },
    "check_eligibility": {
        WorkflowStage.UNDERSTANDING: {"customer_id"},
        WorkflowStage.RETRIEVAL: {"customer_id", "product_ids"},
        WorkflowStage.ELIGIBILITY: {"customer_id", "product_ids"},
        WorkflowStage.EXTERNAL_ACTION: {"customer_id", "product_ids"},
    },
    "check_missing_documents": {
        WorkflowStage.UNDERSTANDING: {"customer_id"},
        WorkflowStage.RETRIEVAL: {"customer_id"},
        WorkflowStage.ELIGIBILITY: {"customer_id", "product_ids"},
        WorkflowStage.EXTERNAL_ACTION: {"customer_id", "product_ids"},
    },
    "resume_case": {
        WorkflowStage.UNDERSTANDING: {"case_id"},
        WorkflowStage.RETRIEVAL: {"case_id", "changed_artifacts"},
        WorkflowStage.ELIGIBILITY: {"case_id", "changed_artifacts"},
        WorkflowStage.EXTERNAL_ACTION: {"case_id", "changed_artifacts"},
    },
    "prepare_customer_response": {
        WorkflowStage.UNDERSTANDING: {"customer_id", "purpose"},
        WorkflowStage.RETRIEVAL: {"customer_id", "purpose"},
        WorkflowStage.ELIGIBILITY: {"customer_id", "purpose"},
        WorkflowStage.EXTERNAL_ACTION: {"customer_id", "recipient", "verified_draft"},
    },
    "prepare_case_task": {
        WorkflowStage.UNDERSTANDING: {"customer_id", "task_type"},
        WorkflowStage.RETRIEVAL: {"customer_id", "task_type"},
        WorkflowStage.ELIGIBILITY: {"customer_id", "task_type"},
        WorkflowStage.EXTERNAL_ACTION: {"customer_id", "task_type", "action_payload"},
    },
    "approve_actions": {
        WorkflowStage.UNDERSTANDING: {"case_id"},
        WorkflowStage.RETRIEVAL: {"case_id"},
        WorkflowStage.ELIGIBILITY: {"case_id"},
        WorkflowStage.EXTERNAL_ACTION: {"case_id", "action_payload"},
    },
}


def required_slots(intent_id: str, stage: WorkflowStage) -> Set[str]:
    by_stage = SLOT_REQUIREMENTS.get(intent_id, {})
    return set(by_stage.get(stage, set()))

