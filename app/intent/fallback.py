"""Deterministic intent fallback used offline and after model failure."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.intent.normalizer import extract_amount, extract_tenor_months, fold_text, normalize_entity, normalize_text
from app.intent.taxonomy import INTENT_TAXONOMY
from app.schemas.v2.common import ResolvedValue, SourceType
from app.schemas.v2.context_snapshot import ContextSnapshot
from app.schemas.v2.intent_result import EvidenceSpan, IntentResult, RecommendedAction


_PATTERNS: Dict[str, tuple[str, ...]] = {
    "approve_actions": ("phe duyet", "approve", "duyet hanh dong"),
    "reject_actions": ("tu choi", "reject"),
    "resume_case": ("tiep tuc", "resume", "bo sung ho so", "tai len"),
    "status_lookup": ("trang thai", "den dau", "tien do"),
    "check_missing_documents": ("con thieu", "thieu gi", "ho so thieu", "giay to thieu"),
    "check_eligibility": ("du dieu kien", "kiem tra dieu kien", "co vay duoc", "tham dinh", "eligibility"),
    "compare_products": ("so sanh", "compare"),
    "prepare_customer_response": ("soan email", "soan phan hoi", "tra loi khach", "email khach", "chuan bi email"),
    "prepare_case_task": ("tao task", "lap task", "chuan bi case", "tao case"),
}

_PRODUCT_SIGNALS = (
    "payroll", "chi luong", "tra luong", "dong tien", "cash management",
    "thu ho", "chi ho", "nha cung cap", "von luu dong", "hmtd", "thau chi", "working capital",
)


class DeterministicIntentExtractor:
    def extract(self, message: str, message_id: str, context: Optional[ContextSnapshot] = None) -> IntentResult:
        original = normalize_text(message)
        folded = fold_text(original)
        detected: List[str] = []
        for intent_id, patterns in _PATTERNS.items():
            if any(pattern in folded for pattern in patterns):
                detected.append(intent_id)
        if any(signal in folded for signal in _PRODUCT_SIGNALS):
            detected.insert(0, "find_product")
        detected = list(dict.fromkeys(detected)) or ["out_of_scope"]

        primary = self._choose_primary(detected)
        sub_intents = [item for item in detected if item != primary]
        entities = self._entities(original, folded)
        resolved_slots = self._context_slots(context)
        if products := entities.get("product_ids"):
            resolved_slots["product_ids"] = self._resolved(products, SourceType.USER_EXPLICIT, message_id, 0.95, True)
        if amount := entities.get("requested_amount"):
            resolved_slots["requested_amount"] = self._resolved(amount, SourceType.USER_EXPLICIT, message_id, 0.95, True)
        if tenor := entities.get("tenor"):
            resolved_slots["tenor"] = self._resolved(tenor, SourceType.USER_EXPLICIT, message_id, 0.95, True)
        resolved_slots["objective"] = self._resolved(original, SourceType.USER_EXPLICIT, message_id, 0.95, True)

        required = list(INTENT_TAXONOMY[primary]["required_slots"])
        missing = [slot for slot in required if slot not in resolved_slots and slot not in entities]
        if context and context.conflicts:
            action = RecommendedAction.REQUEST_CONFIRMATION
        elif primary == "out_of_scope":
            action = RecommendedAction.REJECT_OUT_OF_SCOPE
        elif missing and INTENT_TAXONOMY[primary]["risk"] in {"medium", "high"}:
            action = RecommendedAction.ASK_CLARIFICATION
        elif missing:
            action = RecommendedAction.DEFER_MISSING_FIELD
        else:
            action = RecommendedAction.CONTINUE_WORKFLOW

        field_confidence = {
            "primary_intent": 0.92 if primary != "out_of_scope" else 0.75,
            **{name: value.confidence for name, value in resolved_slots.items()},
        }
        return IntentResult(
            primary_intent=primary,
            sub_intents=sub_intents,
            user_goal=original or "Không xác định",
            entities=entities,
            resolved_slots=resolved_slots,
            constraints=[],
            success_criteria=self._success_criteria(detected),
            missing_information=missing,
            ambiguities=[],
            evidence_spans=[EvidenceSpan(field="primary_intent", text=original, message_id=message_id)] if original else [],
            field_confidence=field_confidence,
            overall_confidence=min(field_confidence.values()),
            recommended_action=action,
        )

    @staticmethod
    def _choose_primary(detected: List[str]) -> str:
        priority = (
            "approve_actions", "reject_actions", "resume_case", "check_missing_documents",
            "compare_products", "find_product", "check_eligibility", "prepare_case_task",
            "prepare_customer_response", "status_lookup", "out_of_scope",
        )
        return next(item for item in priority if item in detected)

    @staticmethod
    def _resolved(value: Any, source: SourceType, source_id: str, confidence: float, confirmed: bool) -> ResolvedValue:
        return ResolvedValue(
            value=value,
            source_type=source,
            source_id=source_id,
            confidence=confidence,
            confirmed=confirmed,
            observed_at=datetime.now(timezone.utc),
        )

    def _context_slots(self, context: Optional[ContextSnapshot]) -> Dict[str, ResolvedValue]:
        if context is None:
            return {}
        slots: Dict[str, ResolvedValue] = {}
        if context.workspace.selected_customer_id:
            slots["customer_id"] = self._resolved(context.workspace.selected_customer_id, SourceType.WORKSPACE, "selected_customer_id", 1.0, True)
        if context.workspace.active_case_id:
            slots["case_id"] = self._resolved(context.workspace.active_case_id, SourceType.WORKSPACE, "active_case_id", 1.0, True)
        if context.workspace.selected_product_ids:
            slots["product_ids"] = self._resolved(context.workspace.selected_product_ids, SourceType.WORKSPACE, "selected_product_ids", 1.0, True)
        return slots

    @staticmethod
    def _entities(original: str, folded: str) -> Dict[str, Any]:
        products: List[str] = []
        for signal in _PRODUCT_SIGNALS:
            if signal in folded:
                product = normalize_entity("product", signal)
                if isinstance(product, str) and product.startswith("PROD-"):
                    products.append(product)
        result: Dict[str, Any] = {}
        if products:
            result["product_ids"] = list(dict.fromkeys(products))
        if amount := extract_amount(original):
            result["requested_amount"] = amount
        if tenor := extract_tenor_months(original):
            result["tenor"] = tenor
        result["urgency"] = normalize_entity("urgency", original)
        return result

    @staticmethod
    def _success_criteria(intents: List[str]) -> List[str]:
        mapping = {
            "find_product": "Có sản phẩm trong catalog và nguồn tương ứng",
            "check_eligibility": "Mỗi nhánh có trạng thái, rule và evidence",
            "check_missing_documents": "Có checklist hồ sơ còn thiếu",
            "prepare_customer_response": "Có phản hồi nháp chưa gửi",
            "prepare_case_task": "Có case/task payload nháp",
        }
        return [mapping[item] for item in intents if item in mapping]
