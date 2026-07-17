"""Fail-closed deterministic rule execution; no LLM is allowed to decide pass/fail."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from app.eligibility.models import ProductEligibility, RuleEvaluation, RuleSeverity, RuleStatus
from app.eligibility.registry import RuleRegistry


class EligibilityEngine:
    def __init__(self, registry: RuleRegistry | None = None) -> None:
        self.registry = registry or RuleRegistry()

    def evaluate(
        self,
        product_ids: Iterable[str],
        *,
        customer: Dict[str, Any],
        documents: Iterable[Dict[str, Any]],
        live_check_error: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_documents = {
            str(item.get("document_type") or item.get("doc_type")): item for item in documents
        }
        products: List[ProductEligibility] = []
        for product_id in product_ids:
            evaluations = [
                self._execute(rule, customer, normalized_documents)
                for rule in self.registry.for_product(product_id)
            ]
            if live_check_error and product_id == "PROD-WORKING-CAPITAL":
                evaluations.append(self._live_failure(live_check_error))
            products.append(
                ProductEligibility(
                    product_id=product_id,
                    status=self._aggregate(evaluations),
                    rules=evaluations,
                    missing_information=list(
                        dict.fromkeys(item.field for item in evaluations if item.status == RuleStatus.PENDING_INFORMATION)
                    ),
                    evaluated_at=datetime.now(timezone.utc),
                    registry_version=self.registry.version,
                )
            )
        overall = self._aggregate([item for product in products for item in product.rules])
        return {
            "overall_status": overall.value,
            "products": [item.model_dump(mode="json") for item in products],
            "registry_version": self.registry.version,
        }

    @staticmethod
    def _execute(rule, customer: Dict[str, Any], documents: Dict[str, Dict[str, Any]]) -> RuleEvaluation:
        if rule.operator == "required_document":
            document = documents.get(str(rule.expected))
            actual = document.get("status") if document else None
            missing = document is None or actual not in {"verified", "valid"}
            status = RuleStatus.PENDING_INFORMATION if missing else RuleStatus.PASSED
        else:
            actual = customer.get(rule.field)
            if rule.field == "ubo_status" and "ubo_information" in documents:
                ubo_document = documents["ubo_information"]
                if ubo_document.get("status") in {"verified", "valid"}:
                    actual = "verified"
            if actual is None:
                status = RuleStatus.PENDING_INFORMATION
            elif rule.operator == "gte":
                status = RuleStatus.PASSED if float(actual) >= float(rule.expected) else RuleStatus.FAILED
            elif rule.operator == "equals":
                status = RuleStatus.PASSED if actual == rule.expected else RuleStatus.FAILED
            elif rule.operator == "one_of":
                normalized = str(actual).lower()
                if rule.field == "ubo_status" and normalized in {
                    "chua xac minh day du", "chưa xác minh đầy đủ", "incomplete", "missing"
                }:
                    status = RuleStatus.PENDING_INFORMATION
                else:
                    status = RuleStatus.PASSED if normalized in {str(value).lower() for value in rule.expected} else RuleStatus.FAILED
            else:
                status = RuleStatus.PENDING_REVIEW
        return RuleEvaluation(
            rule_id=rule.rule_id,
            rule_version=rule.version,
            status=status,
            severity=rule.severity,
            field=rule.field,
            actual=actual,
            expected=rule.expected,
            failure_code=rule.failure_code if status != RuleStatus.PASSED else None,
            source_document_id=rule.source_document_id,
            source_version=rule.source_version,
            source_location=rule.source_location,
            source_quote=rule.source_quote,
        )

    @staticmethod
    def _live_failure(error: str) -> RuleEvaluation:
        return RuleEvaluation(
            rule_id="LIVE-CREDIT-CHECK",
            rule_version="adapter-v1",
            status=RuleStatus.PENDING_REVIEW,
            severity=RuleSeverity.BLOCKING,
            field="credit_live_check",
            actual=error,
            expected="available",
            failure_code="LIVE_CHECK_UNAVAILABLE",
            source_document_id="SYSTEM-TOOL-CONTRACT",
            source_version="2.0.0",
            source_location="credit adapter",
            source_quote="Khi nguồn kiểm tra tín dụng lỗi, hệ thống không được tự kết luận đạt.",
        )

    @staticmethod
    def _aggregate(evaluations: Iterable[RuleEvaluation]) -> RuleStatus:
        items = list(evaluations)
        blocking = [item for item in items if item.severity == RuleSeverity.BLOCKING]
        if any(item.status == RuleStatus.PENDING_REVIEW for item in blocking):
            return RuleStatus.PENDING_REVIEW
        if any(item.status == RuleStatus.FAILED for item in blocking):
            return RuleStatus.FAILED
        if any(item.status == RuleStatus.PENDING_INFORMATION for item in blocking):
            return RuleStatus.PENDING_INFORMATION
        return RuleStatus.PASSED
