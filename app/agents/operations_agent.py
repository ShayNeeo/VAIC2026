"""Operations preparation node. It only creates drafts, never external actions."""

from __future__ import annotations

from typing import Any, Dict

from app.schemas.state import SharedCaseState
from app.tools.operations_tools import SLA_HOURS, check_document_completeness, draft_customer_email, get_required_documents


class OperationsAgent:
    owner = "Operations"

    def run(self, state: SharedCaseState) -> Dict[str, Any]:
        product_ids = state.product_result.get("recommended_products", [])
        required = get_required_documents(product_ids)
        missing = check_document_completeness(required, state.documents)
        missing = list(dict.fromkeys([*state.missing_information, *missing]))
        state.missing_information = missing
        company_name = str(state.company_profile.get("name", state.customer_id))
        email = draft_customer_email(company_name, missing)
        task_type = "missing_information" if missing else "open_service"
        tasks = [
            {
                "task_description": f"Thu thập và kiểm tra {item}",
                "assigned_team": state.rm_id,
                "sla_hours": SLA_HOURS[task_type],
            }
            for item in missing
        ] or [
            {
                "task_description": "Kiểm tra lần cuối hồ sơ và chuẩn bị mở dịch vụ",
                "assigned_team": state.rm_id,
                "sla_hours": SLA_HOURS["open_service"],
            }
        ]
        result = {
            "proposed_crm_case": {
                "case_title": f"Corporate service request - {company_name}",
                "priority": "high" if state.risk_level == "high" else "normal",
                "tasks": tasks,
            },
            "required_documents": required,
            "missing_documents": missing,
            "customer_email_draft": email,
            "decision_brief": {
                "products": product_ids,
                "legal_status": state.legal_result.get("eligibility_status", "unknown"),
                "risk_level": state.risk_level,
            },
        }
        state.operations_result = result
        state.audit_log.append({"actor": "Operations", "action": "operations.prepare_draft", "result": {"missing_count": len(missing)}})
        return result

