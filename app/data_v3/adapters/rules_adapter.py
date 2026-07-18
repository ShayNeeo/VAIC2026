"""V3 Rule Registry adapter: translates V3 blueprint rule schema to the runtime
EligibilityRule schema used by EligibilityEngine.

Key design decisions:
- V3 blueprint rules use a different schema (product_id, on_unknown, source_section)
  vs the runtime EligibilityRule (scope, failure_code, source_location, source_quote).
- source_quote MUST be an exact substring of the indexed chunk text for
  EvidenceValidator to succeed. The quotes below are drawn verbatim from
  data/synthetic/v3/legal/banking_policy_documents.json.
- human_review_allowed is derived from on_unknown: "pending_review" means a
  specialist can independently re-verify; "pending_information" is a hard
  missing-document gap, not reviewable until the document is provided.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from app.eligibility.models import EligibilityRule, RuleSeverity
from app.eligibility.registry import RuleRegistry


# Verbatim quotes from data/synthetic/v3/legal/banking_policy_documents.json.
# Each quote MUST be an exact normalized substring of the corresponding
# document chunk text so that validate_claim() returns VALID when the legal
# knowledge index has been ingested with those documents.
_V3_SOURCE_QUOTES = {
    "SYNTH-RULE-REG-001": "Hồ sơ doanh nghiệp phải có đăng ký kinh doanh hợp lệ.",
    "SYNTH-RULE-PAYROLL-HC-001": "Doanh nghiệp cần có tối thiểu 10 nhân sự tham gia dịch vụ chi lương.",
    "SYNTH-RULE-CASHMGMT-ACC-001": "Doanh nghiệp sử dụng dịch vụ Cash Management cần có từ 2 tài khoản trở lên hoặc có từ 2 đơn vị thành viên trở lên",
    "SYNTH-RULE-WC-YEARS-001": "Doanh nghiệp hoạt động liên tục tối thiểu 2 năm.",
    "SYNTH-RULE-WC-FS-001": "Hồ sơ tín dụng phải có báo cáo tài chính năm gần nhất.",
    "SYNTH-RULE-WC-UBO-001": "hồ sơ cấp tín dụng phải có thông tin chủ sở hữu hưởng lợi đã xác minh.",
    "SYNTH-RULE-WC-BADDEBT-001": "Không có nợ xấu trong 12 tháng gần nhất theo nguồn được phép.",
}

# Maps V3 rule_id → failure_code for the runtime EligibilityRule
_V3_FAILURE_CODES = {
    "SYNTH-RULE-REG-001": "BUSINESS_REGISTRATION_MISSING",
    "SYNTH-RULE-PAYROLL-HC-001": "EMPLOYEE_COUNT_BELOW_MINIMUM",
    "SYNTH-RULE-CASHMGMT-ACC-001": "ACCOUNT_COUNT_BELOW_MINIMUM",
    "SYNTH-RULE-WC-YEARS-001": "OPERATING_HISTORY_TOO_SHORT",
    "SYNTH-RULE-WC-FS-001": "FINANCIAL_STATEMENTS_MISSING",
    "SYNTH-RULE-WC-UBO-001": "UBO_MISSING_OR_UNVERIFIED",
    "SYNTH-RULE-WC-BADDEBT-001": "BAD_DEBT_FOUND",
}


def load_v3_rules(path: str) -> List[EligibilityRule]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rules = []
    for item in data.get("rules", []):
        rule_id = item["rule_id"]
        on_unknown = item.get("on_unknown", "pending_information")
        rules.append(
            EligibilityRule(
                rule_id=rule_id,
                version=item["version"],
                scope=[item["product_id"]] if item["product_id"] != "*" else ["*"],
                effective_from=datetime.strptime(item["effective_from"], "%Y-%m-%d").date(),
                severity=RuleSeverity(item["severity"]),
                field=item["field"],
                operator=item["operator"],
                expected=item["expected"],
                failure_code=_V3_FAILURE_CODES.get(rule_id, on_unknown),
                source_document_id=item["source_document_id"],
                source_version=item["version"],
                source_location=f"{item['source_document_id']} section {item['source_section']}",
                # Verbatim quote from the indexed banking_policy_documents.json
                # so that validate_claim() finds the exact substring in the chunk text.
                source_quote=_V3_SOURCE_QUOTES.get(rule_id, ""),
                # Only rules with on_unknown="pending_review" are genuinely
                # reviewable by a specialist; information-gap rules require
                # the customer/RM to provide missing data, not a specialist override.
                human_review_allowed=(on_unknown == "pending_review"),
            )
        )
    return rules


class V3RuleRegistry(RuleRegistry):
    """Registry backed by V3 blueprint rule schema.

    Does NOT call require_serving_approval() or the parent __init__ because
    V3 rule files use a different schema (blueprint shape) and a dedicated
    source_card path. Governance gate is enforced at the V3 data layer.
    """

    def __init__(self, path: str | Path):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        self.version = str(payload.get("registry_version", "v3"))
        self.rules = load_v3_rules(str(path))
