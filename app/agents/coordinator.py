"""Planner/Coordinator facade over the compiled LangGraph workflow."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from pydantic import BaseModel, ConfigDict

from app.agents.contracts import (
    AssistanceRequest,
    CollaborationSession,
    ConstraintNotice,
    ExpertFinding,
    SynthesisResult,
    TaskAssignment,
)
from app.agents.langgraph_workflow import ExpertCollaborationGraph, ExpertGraphState
from app.agents.manifests import COORDINATOR_MANIFEST


class CoordinationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    product_result: Dict[str, Any]
    eligibility_result: Dict[str, Any]
    credit_result: Dict[str, Any]
    insurance_result: Dict[str, Any]
    alternative_product_result: Optional[Dict[str, Any]] = None
    alternative_eligibility_result: Optional[Dict[str, Any]] = None
    assignments: tuple[TaskAssignment, ...] = ()
    findings: tuple[ExpertFinding, ...] = ()
    assistance_requests: tuple[AssistanceRequest, ...] = ()
    constraint_notices: tuple[ConstraintNotice, ...] = ()
    collaboration_session: CollaborationSession
    synthesis_result: SynthesisResult
    graph_node_trace: tuple[str, ...] = ()


class CoordinatorAgent:
    manifest = COORDINATOR_MANIFEST

    def __init__(
        self,
        product_agent: Any,
        credit_agent: Any,
        insurance_agent: Any,
        eligibility_engine: Any,
    ) -> None:
        self.graph = ExpertCollaborationGraph(
            product_agent=product_agent,
            credit_agent=credit_agent,
            insurance_agent=insurance_agent,
            eligibility_engine=eligibility_engine,
        )

    async def coordinate(
        self,
        *,
        case_id: str,
        trace_id: str,
        query: str,
        branch: str,
        customer_attributes: Dict[str, Any],
        documents: List[Dict[str, Any]],
        business_snapshot: Optional[Dict[str, Any]],
        requested_product_ids: Optional[Sequence[str]],
        intent_entities: Optional[Dict[str, Any]],
        start_at: str,
        existing_product_result: Optional[Dict[str, Any]] = None,
        existing_eligibility_result: Optional[Dict[str, Any]] = None,
        existing_credit_result: Optional[Dict[str, Any]] = None,
        existing_insurance_result: Optional[Dict[str, Any]] = None,
    ) -> CoordinationResult:
        nodes = ["retrieve_products", "evaluate_eligibility", "validate_evidence", "prepare_operations"]
        initial: ExpertGraphState = {
            "case_id": case_id,
            "trace_id": trace_id,
            "query": query,
            "branch": branch,
            "customer_attributes": customer_attributes,
            "documents": documents,
            "business_snapshot": business_snapshot,
            "requested_product_ids": requested_product_ids,
            "intent_entities": intent_entities or {},
            "start_index": nodes.index(start_at),
            "product_result": dict(existing_product_result or {}),
            "eligibility_result": dict(existing_eligibility_result or {}),
            "credit_result": dict(existing_credit_result or {}),
            "insurance_result": dict(existing_insurance_result or {}),
            "assignments": [],
            "findings": [],
            "assistance_requests": [],
            "constraint_notices": [],
            "graph_node_trace": [],
        }
        final = await self.graph.ainvoke(initial)
        return CoordinationResult(
            product_result=final.get("product_result", {}),
            eligibility_result=final.get("eligibility_result", {}),
            credit_result=final.get("credit_result", {}),
            insurance_result=final.get("insurance_result", {}),
            alternative_product_result=final.get("alternative_product_result"),
            alternative_eligibility_result=final.get("alternative_eligibility_result"),
            assignments=tuple(final.get("assignments", [])),
            findings=tuple(final.get("findings", [])),
            assistance_requests=tuple(final.get("assistance_requests", [])),
            constraint_notices=tuple(final.get("constraint_notices", [])),
            collaboration_session=final["collaboration_session"],
            synthesis_result=final["synthesis_result"],
            graph_node_trace=tuple(final.get("graph_node_trace", [])),
        )

