"""Merge context values into IntentResult without losing provenance."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from app.intent.confidence import calibrated_confidence
from app.intent.slot_registry import WorkflowStage, required_slots
from app.schemas.v2.common import ResolvedValue, SourceType
from app.schemas.v2.context_snapshot import ContextSnapshot
from app.schemas.v2.intent_result import IntentResult, RecommendedAction


class SlotResolver:
    def resolve(
        self,
        result: IntentResult,
        context: ContextSnapshot,
        *,
        stage: WorkflowStage = WorkflowStage.UNDERSTANDING,
    ) -> IntentResult:
        slots: Dict[str, ResolvedValue] = dict(result.resolved_slots)
        now = datetime.now(timezone.utc)
        defaults = {
            "customer_id": (
                context.workspace.selected_customer_id,
                SourceType.WORKSPACE,
                "selected_customer_id",
            ),
            "case_id": (context.workspace.active_case_id, SourceType.WORKSPACE, "active_case_id"),
            "product_ids": (
                list(context.workspace.selected_product_ids) or None,
                SourceType.WORKSPACE,
                "selected_product_ids",
            ),
        }
        for name, (value, source, source_id) in defaults.items():
            if name not in slots and value is not None:
                slots[name] = ResolvedValue(
                    value=value,
                    source_type=source,
                    source_id=source_id,
                    confidence=1.0,
                    confirmed=True,
                    observed_at=now,
                )
        needed = set()
        for intent_id in [result.primary_intent, *result.sub_intents]:
            needed.update(required_slots(intent_id, stage))
        missing = sorted(name for name in needed if name not in slots and name not in result.entities)
        conflicts = {item.field for item in context.conflicts}
        field_confidence = dict(result.field_confidence)
        for name, value in slots.items():
            field_confidence[name] = calibrated_confidence(
                value,
                stale=context.customer.stale and value.source_type == SourceType.CRM,
                conflict=name in conflicts,
            )
        action = result.recommended_action
        if any(item.requires_confirmation for item in context.conflicts):
            action = RecommendedAction.REQUEST_CONFIRMATION
        elif missing and stage in {WorkflowStage.UNDERSTANDING, WorkflowStage.ELIGIBILITY, WorkflowStage.EXTERNAL_ACTION}:
            action = RecommendedAction.ASK_CLARIFICATION
        elif missing:
            action = RecommendedAction.DEFER_MISSING_FIELD
        overall = min(field_confidence.values()) if field_confidence else result.overall_confidence
        return result.model_copy(
            update={
                "resolved_slots": slots,
                "missing_information": missing,
                "field_confidence": field_confidence,
                "overall_confidence": overall,
                "recommended_action": action,
            }
        )

