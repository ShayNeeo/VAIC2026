"""Rule Registry (L3).

Quản lý compliance rules. Load từ file JSON (theo plan_v3 section 11) hoặc
fallback về in-memory rules. Hỗ trợ filter theo version, product scope và date.
"""

import json
import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from .models import ComplianceRule
from .knowledge_base import BUILTIN_COMPLIANCE_RULES

logger = logging.getLogger(__name__)


class RuleRegistry:
    """Registry quản lý các rule tuân thủ pháp lý."""

    def __init__(self, data_path: str = "data/legal/rules/compliance_rules.json"):
        self.data_path = Path(data_path)
        self._rules: Dict[str, ComplianceRule] = {}
        self.load_rules()

    def load_rules(self) -> None:
        """Load rules từ JSON, fallback về built-in nếu lỗi."""
        self._rules.clear()
        
        try:
            if self.data_path.exists():
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                raw_rules = data.get("rules", [])
                logger.info(f"Loaded {len(raw_rules)} rules from {self.data_path}")
            else:
                logger.warning(f"File {self.data_path} not found. Using built-in rules.")
                raw_rules = BUILTIN_COMPLIANCE_RULES
                
            for raw in raw_rules:
                try:
                    rule = ComplianceRule(**raw)
                    self._rules[rule.rule_id] = rule
                except Exception as e:
                    logger.error(f"Error parsing rule {raw.get('rule_id', 'unknown')}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load rules: {e}. Using built-in fallback.")
            for raw in BUILTIN_COMPLIANCE_RULES:
                try:
                    rule = ComplianceRule(**raw)
                    self._rules[rule.rule_id] = rule
                except Exception:
                    pass

    def get_rule(self, rule_id: str) -> Optional[ComplianceRule]:
        """Lấy rule theo ID."""
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[ComplianceRule]:
        """Lấy tất cả rules."""
        return list(self._rules.values())

    def get_active_rules(self, as_of: Optional[date] = None) -> List[ComplianceRule]:
        """Lấy các rules đang có hiệu lực."""
        check_date = as_of or date.today()
        return [r for r in self._rules.values() if r.is_effective(check_date)]

    def get_rules_for_product(self, product_id: str, as_of: Optional[date] = None) -> List[ComplianceRule]:
        """Lấy các rules đang active và apply cho product này."""
        active_rules = self.get_active_rules(as_of)
        # Sắp xếp theo priority (số càng nhỏ ưu tiên càng cao)
        product_rules = [r for r in active_rules if r.applies_to(product_id)]
        product_rules.sort(key=lambda r: r.priority)
        return product_rules
