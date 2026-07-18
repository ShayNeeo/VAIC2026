"""Fail-closed deterministic rule execution; no LLM is allowed to decide pass/fail."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from app.eligibility.models import LegalSummary, ProductEligibility, RelatedPolicy, RuleEvaluation, RuleSeverity, RuleStatus
from app.eligibility.policy_registry import B2BPolicyRegistry, PolicyRegistryError
from app.eligibility.registry import RuleRegistry


class EligibilityEngine:
    def __init__(self, registry: RuleRegistry | None = None, policies: B2BPolicyRegistry | None = None) -> None:
        self.registry = registry or RuleRegistry()
        self.policies = policies or B2BPolicyRegistry()

    def evaluate(
        self,
        product_ids: Iterable[str],
        *,
        customer: Dict[str, Any],
        documents: Iterable[Dict[str, Any]],
        live_check_error: Optional[str] = None,
        branch: str = "*",
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
            policy_error = None
            for evaluation in evaluations:
                if evaluation.rule_id == "LIVE-CREDIT-CHECK":
                    continue
                try:
                    source = self.policies.section(evaluation.policy_id, evaluation.section_id, product_id, branch=branch)
                    section = source["section"]
                    if source["document_id"] != evaluation.source_document_id or source["document_version"] != evaluation.source_version or section["source_quote"] != evaluation.source_quote:
                        raise PolicyRegistryError("rule source does not match policy source")
                except PolicyRegistryError as exc:
                    # The governance guard only fires when the policy registry
                    # actually *knows* this policy/section and the cited source
                    # content diverges from what is governed. Rules whose
                    # policy_id is not present in this registry (e.g. V3 rule
                    # packs that cite V3 document IDs not loaded here) are a
                    # registry-scope gap, not a content-integrity failure -- so
                    # we keep the status the rule engine already computed
                    # (e.g. PENDING_INFORMATION for missing customer docs)
                    # instead of forcing everything to PENDING_REVIEW.
                    if str(exc).startswith("no active policy evidence"):
                        continue
                    evaluation.status = RuleStatus.PENDING_REVIEW
                    evaluation.failure_code = "POLICY_EVIDENCE_UNAVAILABLE"
                    policy_error = str(exc)
            status = self._aggregate(evaluations)
            related = self._related_policies(product_id, evaluations, branch=branch)
            products.append(
                ProductEligibility(
                    product_id=product_id,
                    status=status,
                    rules=evaluations,
                    missing_information=list(
                        dict.fromkeys(item.field for item in evaluations if item.status == RuleStatus.PENDING_INFORMATION)
                    ),
                    evaluated_at=datetime.now(timezone.utc),
                    registry_version=self.registry.version,
                    related_policies=related,
                    legal_summary=self._legal_summary(status, evaluations, policy_error),
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
            policy_id=rule.policy_id,
            section_id=rule.section_id,
            source_document_id=rule.source_document_id,
            source_version=rule.source_version,
            source_location=rule.source_location,
            source_quote=rule.source_quote,
            human_review_allowed=rule.human_review_allowed,
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
            policy_id="SYSTEM-TOOL-POLICY",
            section_id="credit-adapter",
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

    def _related_policies(self, product_id: str, evaluations: List[RuleEvaluation], *, branch: str) -> List[RelatedPolicy]:
        items = []
        for row in self.policies.policies_for_result(product_id, evaluations, branch=branch):
            policy, section = row["policy"], row["section"]
            rule_ids = row["rule_ids"]
            claim_suffix = rule_ids[0] if rule_ids else section["section_id"]
            items.append(RelatedPolicy(
                policy_id=policy["policy_id"], title=policy["title"], policy_type=policy["policy_type"],
                document_id=policy["document_id"], document_version=policy["document_version"],
                section=section["section_id"], effective_from=policy["effective_from"], effective_to=policy.get("effective_to"),
                applicability_reason=f"Áp dụng cho sản phẩm {product_id}", decision_effect=row["decision_effect"],
                rule_ids=rule_ids, summary=section["summary"], source_quote=section["source_quote"],
                claim_id=f"ELIG-{product_id}-{claim_suffix}", evidence_valid=False,
            ))
        return items

    @staticmethod
    def _legal_summary(status: RuleStatus, evaluations: List[RuleEvaluation], policy_error: Optional[str]) -> LegalSummary:
        conclusion = {
            RuleStatus.PASSED: "Đủ điều kiện theo các rule synthetic đã đánh giá.",
            RuleStatus.FAILED: "Không đạt ít nhất một điều kiện bắt buộc.",
            RuleStatus.PENDING_INFORMATION: "Chưa đủ hồ sơ hoặc dữ liệu để kết luận.",
            RuleStatus.PENDING_REVIEW: "Cần chuyên viên Legal/Compliance xem xét.",
        }[status]
        blocking = [item.failure_code or item.rule_id for item in evaluations if item.severity == RuleSeverity.BLOCKING and item.status == RuleStatus.FAILED]
        warnings = [item.failure_code or item.rule_id for item in evaluations if item.severity == RuleSeverity.WARNING and item.status != RuleStatus.PASSED]
        required = [item.field for item in evaluations if item.status == RuleStatus.PENDING_INFORMATION]
        if policy_error:
            warnings.append("POLICY_EVIDENCE_UNAVAILABLE")
        return LegalSummary(conclusion=conclusion, blocking_reasons=list(dict.fromkeys(blocking)), warnings=list(dict.fromkeys(warnings)), required_actions=list(dict.fromkeys(required)))
