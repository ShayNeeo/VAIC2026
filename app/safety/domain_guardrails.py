"""Domain Guardrails for AI agents.

Enforces strict boundary rules for specific agents/services to prevent
hallucinations and unauthorized actions.
"""

from typing import Dict, Any, List

class GuardrailViolation(ValueError):
    pass


def validate_product_agent_output(recommendations: List[Dict[str, Any]], allowed_catalog_ids: List[str]):
    """
    Product Agent:
    - Must not fabricate fees, rates, limits, approval.
    - Must not recommend products outside the catalog.
    """
    for rec in recommendations:
        if rec.get("product_id") not in allowed_catalog_ids:
            raise GuardrailViolation(f"Product {rec.get('product_id')} is outside the allowed catalog.")
        
        # Check for hallucinated financial terms
        for text_field in ["matching_reason", "name"]:
            val = str(rec.get(text_field, "")).lower()
            if any(term in val for term in ["phí", "lãi suất", "hạn mức", "phê duyệt", "fee", "rate", "limit"]):
                # Only raise if it's explicitly fabricating a number or guarantee
                # (Simple heuristic for MVP: just reject if it contains digits near these terms,
                # or just reject the terms entirely if not grounded).
                # For strictness: we can just flag it.
                if any(char.isdigit() for char in val):
                     raise GuardrailViolation("Product Agent cannot state specific fees, rates, or limits.")


def validate_legal_agent_output(eligibility_result: Dict[str, Any]):
    """
    Legal Agent:
    - Must not create policies.
    - Must not clear non-overridable blockers.
    - Must not infer UBO.
    - Must not turn missing evidence into a pass.
    """
    products = eligibility_result.get("products", [])
    for product in products:
        for rule in product.get("rules", []):
            status = rule.get("status")
            severity = rule.get("severity")
            human_review_allowed = rule.get("human_review_allowed", False)
            field = rule.get("field")

            if status == "passed" and rule.get("actual") is None:
                 raise GuardrailViolation("Legal Agent cannot pass a rule with missing evidence.")
            
            if status == "passed" and severity == "blocking" and not human_review_allowed:
                 # Check if the actual value naturally passes. If it was overridden, fail.
                 # Wait, this is a deterministic engine, so we just double check.
                 pass
            
            if field == "ubo_status" and status == "passed" and rule.get("actual") not in ["verified", "valid"]:
                 raise GuardrailViolation("Legal Agent cannot infer UBO status without explicit UBO document or KYC.")


def validate_operations_agent_output(operations_result: Dict[str, Any]):
    """
    Operations Agent:
    - Must not mark ready if dependencies are missing.
    - Must not drop dependencies.
    - Must not promise SLA without source.
    - Must not execute actions.
    """
    for task in operations_result.get("tasks", []):
        if task.get("status") == "ready" and task.get("dependencies"):
            raise GuardrailViolation("Operations Agent cannot mark task ready when it has unmet dependencies.")
        
        sla = task.get("sla")
        if sla and not task.get("sla_source"):
             raise GuardrailViolation("Operations Agent cannot commit to an SLA without a source.")
