"""Complexity routing: simple single-agent RAG vs. full multi-agent plan.

Extracted from V2WorkflowEngine so the router is its own addressable,
independently testable component (plan_v2/09_WORKFLOW_ORCHESTRATION.md
section 9 lists `app/workflow/router.py` as the intended file for this;
it was previously inlined as V2WorkflowEngine._is_complex_case).
"""

from __future__ import annotations

from app.schemas.v2.shared_case_state import SharedCaseState

COMPLEX_KEYWORDS = {"credit", "loan", "borrow", "working_capital", "thấu chi", "hạn mức", "vay"}

# Deliberate allowlist, not a denylist: app.workflow.engine.run() is only ever
# invoked in the context of an already-created case (create_case/rerun_with_
# message), so a "find_product"/new-request intent always means the RM wants
# a real case (eligibility -> evidence -> risk gate -> approval), not a
# read-only lookup. Only intents that are inherently status/info lookups on
# something that already exists qualify as "simple" -- everything else,
# including any multi-intent message, fails closed to the full pipeline
# (plan_v2/09_WORKFLOW_ORCHESTRATION.md section 5: "no external action" is a
# simple-route requirement, and find_product/prepare_case_task/etc. always
# lead to a drafted external action once approved).
SIMPLE_PRIMARY_INTENTS = {"status_lookup", "compare_products", "check_missing_documents"}


class ComplexityRouter:
    """plan_v2/09_WORKFLOW_ORCHESTRATION.md section 5: complex if multi-intent,
    credit/legal/KYC, missing-information loop, draft/create/send intent, or
    cross-product dependencies. Simple otherwise (single read-only intent, no
    external action, no high-risk eligibility decision)."""

    @staticmethod
    def route(state: SharedCaseState) -> str:
        return "complex" if ComplexityRouter.is_complex(state) else "simple"

    @staticmethod
    def is_complex(state: SharedCaseState) -> bool:
        return not ComplexityRouter.is_simple(state)

    @staticmethod
    def is_simple(state: SharedCaseState) -> bool:
        intent = state.intent_result
        if not intent:
            return False
        if intent.sub_intents:
            return False
        if intent.primary_intent not in SIMPLE_PRIMARY_INTENTS:
            return False
        query_lower = state.request.text.lower()
        if any(keyword in query_lower for keyword in COMPLEX_KEYWORDS):
            return False
        if "PROD-WORKING-CAPITAL" in intent.entities.get("product_ids", []):
            return False
        return True
