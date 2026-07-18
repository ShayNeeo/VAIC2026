"""Create versioned, deduplicated drafts without external side effects."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.data_catalog.registry import require_serving_approval


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOP = ROOT / "data" / "synthetic" / "v2" / "operations_sop.json"
DEFAULT_SOP_SOURCE_CARD = ROOT / "data" / "catalog" / "source_cards" / "synthetic_operations_sop.json"


def content_hash(payload: Any) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def dedup_key(*, organization: str, customer_id: str, case_id: str, task_type: str, product_id: str | None, subject: str) -> str:
    normalized_subject = " ".join(subject.lower().split())
    return ":".join(
        [organization, customer_id, case_id, task_type, product_id or "none", content_hash(normalized_subject)[7:19]]
    )


class OperationsService:
    def __init__(
        self,
        sop_path: str | Path = DEFAULT_SOP,
        source_card_path: str | Path = DEFAULT_SOP_SOURCE_CARD,
    ) -> None:
        require_serving_approval(source_card_path)
        self.sop = json.loads(Path(sop_path).read_text(encoding="utf-8"))

    def prepare(
        self,
        *,
        organization: str,
        customer_id: str,
        case_id: str,
        customer_name: str,
        product_result: Dict[str, Any],
        eligibility_result: Dict[str, Any],
        available_documents: Optional[Iterable[Dict[str, Any]]] = None,
        existing_artifacts: Optional[Iterable[Dict[str, Any]]] = None,
        previous_result: Optional[Dict[str, Any]] = None,
        execution_plan: Optional[Dict[str, Any]] = None,
        next_best_questions: Optional[Iterable[Dict[str, Any]]] = None,
        next_best_actions: Optional[Iterable[Dict[str, Any]]] = None,
        evidence_ids: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        checklist = self._checklist(product_result, eligibility_result, available_documents or [])
        missing = [item for item in checklist if item["current_status"] == "missing"]
        products = [item["product_id"] for item in product_result.get("recommendations", [])]
        message = self._message(customer_name, missing)
        subject = f"Theo dõi nhu cầu {', '.join(products) or 'sản phẩm doanh nghiệp'}"
        task_key = dedup_key(
            organization=organization,
            customer_id=customer_id,
            case_id=case_id,
            task_type="product_follow_up",
            product_id=products[0] if len(products) == 1 else None,
            subject=subject,
        )
        existing = {item.get("dedup_key"): item for item in (existing_artifacts or [])}
        task_action = "reuse" if task_key in existing else "create"
        version = int(previous_result.get("artifact_version", 0)) + 1 if previous_result else 1
        crm_payload = {
            "case_id": case_id,
            "customer_id": customer_id,
            "subject": subject,
            "product_ids": products,
            "status": "draft",
            "task": {"type": "product_follow_up", "dedup_key": task_key},
        }
        proposal = self._proposal(
            customer_name=customer_name,
            product_result=product_result,
            eligibility_result=eligibility_result,
            evidence_ids=list(evidence_ids or []),
        )
        import uuid
        
        requirements = []
        for item in missing:
            requirements.append({"code": item["document_type_id"], "description": f"Yêu cầu từ operations (SOP: {self.sop['sop_version']})"})
            
        result = {
            "artifact_version": version,
            "sop_version": self.sop["sop_version"],
            "agent_run_id": f"ARUN-OPS-{uuid.uuid4().hex[:8].upper()}",
            "facts_used": [{"checklist": checklist}],
            "requirements": requirements,
            "citations": [],
            "decision_brief": {
                "products": products,
                "eligibility_status": eligibility_result.get("overall_status"),
                "missing_count": len(missing),
            },
            "required_document_checklist": checklist,
            "missing_information": [item["document_type_id"] for item in missing],
            "customer_message_draft": {
                "status": "draft_not_sent",
                "subject": "Đề nghị bổ sung thông tin cho nhu cầu doanh nghiệp",
                "body": message,
            },
            "crm_case_draft": crm_payload,
            "task_drafts": [{**crm_payload["task"], "subject": subject, "action": task_action}],
            "proposal_draft": proposal,
            "execution_plan": execution_plan,
            "next_best_questions": list(next_best_questions or []),
            "next_best_actions": list(next_best_actions or []),
            "artifact_actions": [{"artifact": "task", "action": task_action, "dedup_key": task_key}],
            "external_side_effects": [],
            "due_date": (date.today() + timedelta(days=self.sop["task_types"]["product_follow_up"]["sla_business_days"])).isoformat(),
        }
        result["action_readiness"] = "ready_for_rm_approval" if eligibility_result.get("overall_status") == "passed" else "blocked"
        result["action_payload"] = {
            "crm_case_draft": crm_payload,
            "task_drafts": result["task_drafts"],
            "customer_message_draft": result["customer_message_draft"],
            "proposal_draft": proposal,
        }
        result["content_hash"] = content_hash(result)
        return result

    def _checklist(
        self,
        product_result: Dict[str, Any],
        eligibility_result: Dict[str, Any],
        available_documents: Iterable[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        items: Dict[str, Dict[str, Any]] = {}
        verified_document_types = {
            str(item.get("document_type"))
            for item in available_documents
            if str(item.get("status")) == "verified" and item.get("document_type")
        }
        for product in product_result.get("recommendations", []):
            for document_type in product.get("prerequisites", []):
                entry = items.setdefault(document_type, self._item(document_type))
                entry["required_for_product_ids"].append(product["product_id"])
                entry["reasons"].append("product_prerequisite")
        for product in eligibility_result.get("products", []):
            for rule in product.get("rules", []):
                if rule.get("status") != "pending_information":
                    continue
                document_type = str(rule.get("expected")) if rule.get("field") == "documents" else str(rule.get("field"))
                entry = items.setdefault(document_type, self._item(document_type))
                entry["required_for_product_ids"].append(product["product_id"])
                entry["source_rule_ids"].append(rule["rule_id"])
                entry["reasons"].append("eligibility_rule")
        for entry in items.values():
            entry["required_for_product_ids"] = sorted(set(entry["required_for_product_ids"]))
            entry["source_rule_ids"] = sorted(set(entry["source_rule_ids"]))
            entry["reasons"] = sorted(set(entry["reasons"]))
            if entry["document_type_id"] in verified_document_types:
                entry["current_status"] = "verified"
        return sorted(items.values(), key=lambda item: item["document_type_id"])

    def _item(self, document_type: str) -> Dict[str, Any]:
        return {
            "document_type_id": document_type,
            "display_name": self.sop["document_names"].get(document_type, document_type),
            "required_for_product_ids": [],
            "source_rule_ids": [],
            "reasons": [],
            "severity": "blocking",
            "current_status": "missing",
        }

    @staticmethod
    def _message(customer_name: str, missing: List[Dict[str, Any]]) -> str:
        if not missing:
            return "\n".join(
                [
                    f"Kính gửi {customer_name},",
                    "",
                    "SHB đã ghi nhận nhu cầu và đang chuẩn bị phương án sản phẩm để RM trao đổi cùng Quý doanh nghiệp.",
                    "Thông tin này là bản nháp phục vụ tư vấn, không phải cam kết phê duyệt sản phẩm hoặc cấp tín dụng.",
                    "",
                    "Trân trọng.",
                ]
            )
        lines = [f"Kính gửi {customer_name},", "", "Để tiếp tục xem xét nhu cầu, vui lòng bổ sung:"]
        lines.extend(f"- {item['display_name']}" for item in missing)
        lines.extend(
            [
                "",
                "Đây là danh sách hồ sơ phục vụ bước xem xét, không phải cam kết phê duyệt sản phẩm hoặc cấp tín dụng.",
                "Trân trọng.",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _proposal(
        *,
        customer_name: str,
        product_result: Dict[str, Any],
        eligibility_result: Dict[str, Any],
        evidence_ids: List[str],
    ) -> Dict[str, Any]:
        recommendations = product_result.get("recommendations", [])
        conditions: List[str] = []
        for product in eligibility_result.get("products", []):
            for rule in product.get("rules", []):
                if rule.get("status") != "passed":
                    conditions.append(str(rule.get("failure_code") or rule.get("rule_id")))
        return {
            "status": "draft_not_sent",
            "template_version": "synthetic-proposal-v1",
            "customer_name": customer_name,
            "title": "Đề xuất sơ bộ giải pháp ngân hàng doanh nghiệp",
            "solutions": [
                {
                    "product_id": item.get("product_id"),
                    "name": item.get("name"),
                    "matching_reason": item.get("matching_reason"),
                    "benefits": item.get("benefits", []),
                }
                for item in recommendations
            ],
            "conditions_or_missing": list(dict.fromkeys(conditions)),
            "evidence_ids": evidence_ids,
            "disclaimer": "Bản nháp phục vụ RM rà soát; không phải cam kết cấp sản phẩm, hạn mức hoặc tín dụng.",
        }
