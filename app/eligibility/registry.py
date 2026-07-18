"""Versioned effective-date rule registry."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import List

from app.eligibility.models import EligibilityRule
from app.data_catalog.registry import require_serving_approval


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES = ROOT / "data" / "synthetic" / "v2" / "eligibility_rules.json"
DEFAULT_RULES_SOURCE_CARD = ROOT / "data" / "catalog" / "source_cards" / "synthetic_eligibility_rules.json"


class RuleRegistry:
    def __init__(
        self,
        path: str | Path = DEFAULT_RULES,
        source_card_path: str | Path = DEFAULT_RULES_SOURCE_CARD,
    ) -> None:
        require_serving_approval(source_card_path)
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        self.version = str(payload["registry_version"])
        self.rules = [EligibilityRule.model_validate(item) for item in payload["rules"]]
        if len({(rule.rule_id, rule.version) for rule in self.rules}) != len(self.rules):
            raise ValueError("duplicate rule_id/version")

    def for_product(self, product_id: str, *, as_of: date | None = None) -> List[EligibilityRule]:
        effective = as_of or date.today()
        return [
            rule
            for rule in self.rules
            if ("*" in rule.scope or product_id in rule.scope)
            and rule.effective_from <= effective
            and (rule.effective_to is None or rule.effective_to >= effective)
        ]
