"""Governed synthetic B2B policy registry used to explain eligibility results."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List

from app.data_catalog.registry import require_serving_approval


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICIES = ROOT / "data" / "synthetic" / "v2" / "b2b_policies.json"
DEFAULT_SOURCE_CARD = ROOT / "data" / "catalog" / "source_cards" / "synthetic_b2b_policies.json"


class PolicyRegistryError(ValueError):
    """Raised when policy data cannot safely support a legal decision."""


class B2BPolicyRegistry:
    def __init__(self, path: str | Path = DEFAULT_POLICIES, source_card: str | Path = DEFAULT_SOURCE_CARD) -> None:
        require_serving_approval(source_card)
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("synthetic") is not True:
            raise PolicyRegistryError("B2B policy pack must be explicitly synthetic")
        self.version = str(payload["dataset_version"])
        self.policies: List[Dict[str, Any]] = list(payload["policies"])
        self._validate()

    def _validate(self) -> None:
        seen = set()
        required = {"policy_id", "title", "policy_type", "product_ids", "document_id", "document_version", "effective_from", "active", "sections", "owner", "synthetic", "access_scope"}
        for policy in self.policies:
            missing = required - set(policy)
            if missing:
                raise PolicyRegistryError(f"policy {policy.get('policy_id', '<unknown>')} missing {sorted(missing)}")
            if policy["synthetic"] is not True or not policy["product_ids"] or not policy["sections"]:
                raise PolicyRegistryError(f"policy {policy['policy_id']} failed synthetic/scope/section gate")
            for section in policy["sections"]:
                key = (policy["policy_id"], policy["document_version"], section["section_id"])
                if key in seen:
                    raise PolicyRegistryError(f"duplicate policy section {key}")
                seen.add(key)
                for field in ("section_id", "title", "summary", "source_quote"):
                    if not section.get(field):
                        raise PolicyRegistryError(f"policy section {key} missing {field}")

    def active_for_product(self, product_id: str, *, as_of: date | None = None, branch: str = "*") -> List[Dict[str, Any]]:
        check = as_of or date.today()
        matches = []
        for policy in self.policies:
            start = date.fromisoformat(policy["effective_from"])
            end = date.fromisoformat(policy["effective_to"]) if policy.get("effective_to") else None
            if not policy["active"] or start > check or (end and end < check):
                continue
            if "*" not in policy["product_ids"] and product_id not in policy["product_ids"]:
                continue
            branches = policy["access_scope"].get("branches", [])
            if branch != "*" and "*" not in branches and branch not in branches:
                continue
            matches.append(policy)
        return matches

    def section(self, policy_id: str, section_id: str, product_id: str, *, branch: str = "*") -> Dict[str, Any]:
        for policy in self.active_for_product(product_id, branch=branch):
            if policy["policy_id"] != policy_id:
                continue
            for section in policy["sections"]:
                section_scope = section.get("product_ids", policy["product_ids"])
                if "*" not in section_scope and product_id not in section_scope:
                    continue
                if section["section_id"] == section_id:
                    return {**policy, "section": section}
        raise PolicyRegistryError(f"no active policy evidence for {product_id}:{policy_id}:{section_id}")

    def policies_for_result(self, product_id: str, evaluations: Iterable[Any], *, branch: str = "*") -> List[Dict[str, Any]]:
        by_ref = {(item.policy_id, item.section_id): item for item in evaluations}
        output: List[Dict[str, Any]] = []
        for policy in self.active_for_product(product_id, branch=branch):
            for section in policy["sections"]:
                section_scope = section.get("product_ids", policy["product_ids"])
                if "*" not in section_scope and product_id not in section_scope:
                    continue
                evaluation = by_ref.get((policy["policy_id"], section["section_id"]))
                rule_ids = [evaluation.rule_id] if evaluation else []
                if evaluation and evaluation.status.value == "pending_information":
                    effect = "required_information"
                elif evaluation and evaluation.status.value in {"failed", "pending_review"}:
                    effect = "manual_review" if evaluation.status.value == "pending_review" else "blocking"
                elif evaluation and evaluation.severity.value == "warning":
                    effect = "warning"
                else:
                    effect = "informational"
                output.append({"policy": policy, "section": section, "evaluation": evaluation, "rule_ids": rule_ids, "decision_effect": effect})
        return output
