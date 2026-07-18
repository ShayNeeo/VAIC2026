"""LangGraph implementation of governed Product/Credit/Insurance
collaboration.

Three independent expert runtimes -- Product, Credit, Insurance -- each
read only what their own domain needs and never read another expert's
finding: Product never reads eligibility/credit/insurance results; Credit
reads product_result + the deterministic eligibility_result (never
insurance_result); Insurance reads only product_result + customer profile
(never eligibility_result or credit_result). They run one after another in
this graph for implementation simplicity, but that ordering is not a data
dependency between them -- see each node's docstring.

Eligibility/hard-rule checking is a plain deterministic graph step
(``eligibility_check`` / ``eligibility_check_alternative``), not an LLM-
wrapped "LegalExpert" Agent -- it calls EligibilityEngine.evaluate()
directly, exactly the same deterministic call app/agents/legal_expert.py
previously made through an Agent wrapper. That file is kept (not deleted)
for anything that still imports it directly, but the live collaboration
graph no longer dispatches to it.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.contracts import (
    AgentType,
    AssistanceRequest,
    CollaborationSession,
    ConstraintNotice,
    ExpertFinding,
    SynthesisResult,
    TaskAssignment,
    canonical_hash,
)
from app.agents.manifests import manifest_for
from app.safety.domain_guardrails import validate_legal_agent_output
from app.workflow.synthesis import synthesize_expert_results

if TYPE_CHECKING:
    # Deferred: app.eligibility.engine -> app.eligibility.registry ->
    # app.data_catalog.registry -> app.schemas.v2 -> app.agents.contracts
    # -> app.agents/__init__.py forms an import cycle if imported eagerly
    # here (app.agents/__init__.py eagerly imports this module's chain).
    # EligibilityEngine is only used for a type hint below; evaluate() is
    # called duck-typed at runtime.
    from app.eligibility.engine import EligibilityEngine


LANGGRAPH_WORKFLOW_VERSION = "expert-collaboration-langgraph-2.0.0-product-credit-insurance"


class ExpertGraphState(TypedDict, total=False):
    case_id: str
    trace_id: str
    query: str
    branch: str
    customer_attributes: Dict[str, Any]
    documents: List[Dict[str, Any]]
    business_snapshot: Optional[Dict[str, Any]]
    requested_product_ids: Optional[Sequence[str]]
    intent_entities: Dict[str, Any]
    start_index: int
    product_result: Dict[str, Any]
    eligibility_result: Dict[str, Any]
    credit_result: Dict[str, Any]
    insurance_result: Dict[str, Any]
    alternative_product_result: Optional[Dict[str, Any]]
    alternative_eligibility_result: Optional[Dict[str, Any]]
    assignments: List[TaskAssignment]
    findings: List[ExpertFinding]
    assistance_requests: List[AssistanceRequest]
    constraint_notices: List[ConstraintNotice]
    collaboration_session: CollaborationSession
    synthesis_result: SynthesisResult
    graph_node_trace: List[str]


class ExpertCollaborationGraph:
    """Compiles a finite, typed graph; expert nodes return independent findings."""

    def __init__(
        self,
        *,
        product_agent: Any,
        credit_agent: Any,
        insurance_agent: Any,
        eligibility_engine: EligibilityEngine,
    ) -> None:
        self.product_agent = product_agent
        self.credit_agent = credit_agent
        self.insurance_agent = insurance_agent
        self.eligibility_engine = eligibility_engine
        builder = StateGraph(ExpertGraphState)
        builder.add_node("product_expert", self._product_node)
        builder.add_node("eligibility_check", self._eligibility_node)
        builder.add_node("credit_expert", self._credit_node)
        builder.add_node("insurance_expert", self._insurance_node)
        builder.add_node("product_alternative", self._product_alternative_node)
        builder.add_node("eligibility_check_alternative", self._eligibility_alternative_node)
        builder.add_node("coordinator_synthesis", self._synthesis_node)
        builder.add_edge(START, "product_expert")
        builder.add_edge("product_expert", "eligibility_check")
        builder.add_edge("eligibility_check", "credit_expert")
        # Credit and Insurance do not read each other's result -- see the
        # module docstring. They run one after another here purely for
        # implementation simplicity (avoids needing custom reducers for a
        # genuinely parallel fan-out); neither node's input depends on the
        # other having already run.
        builder.add_edge("credit_expert", "insurance_expert")
        builder.add_conditional_edges(
            "insurance_expert",
            self._route_after_experts,
            {
                "alternative": "product_alternative",
                "synthesis": "coordinator_synthesis",
            },
        )
        builder.add_edge("product_alternative", "eligibility_check_alternative")
        builder.add_edge("eligibility_check_alternative", "coordinator_synthesis")
        builder.add_edge("coordinator_synthesis", END)
        self.compiled = builder.compile()

    async def ainvoke(self, state: ExpertGraphState) -> ExpertGraphState:
        return await self.compiled.ainvoke(state)

    async def _product_node(self, state: ExpertGraphState) -> Dict[str, Any]:
        trace = [*state.get("graph_node_trace", []), "product_expert"]
        if state.get("start_index", 0) > 0 and state.get("product_result"):
            return {"graph_node_trace": trace}
        task = self._task(
            state,
            agent_type=AgentType.PRODUCT_EXPERT,
            task_type="product_discovery",
            objective="Tìm và xếp hạng sản phẩm đáp ứng nhu cầu đã xác nhận.",
            round_number=1,
            input_payload={
                "query": state["query"],
                "requested_product_ids": list(state.get("requested_product_ids") or []),
            },
        )
        finding = await self.product_agent.analyze(
            task,
            query=state["query"],
            branch=state["branch"],
            requested_product_ids=state.get("requested_product_ids"),
            customer_attributes=state["customer_attributes"],
            top_k=3,
        )
        return {
            "assignments": [*state.get("assignments", []), task],
            "findings": [*state.get("findings", []), finding],
            "product_result": dict(finding.domain_result),
            "graph_node_trace": trace,
        }

    def _eligibility_node(self, state: ExpertGraphState) -> Dict[str, Any]:
        """Plain deterministic step -- calls EligibilityEngine.evaluate()
        directly (the exact same call app/agents/legal_expert.py used to
        make through an LLM-wrapped Agent). No manifest, no ExpertFinding,
        no LLM enrichment: this is the rule engine, not an expert opinion."""
        trace = [*state.get("graph_node_trace", []), "eligibility_check"]
        if state.get("start_index", 0) > 1 and state.get("eligibility_result"):
            return {"graph_node_trace": trace}
        product_ids = [
            str(item.get("product_id")) for item in state.get("product_result", {}).get("recommendations", [])
        ]
        result = self.eligibility_engine.evaluate(
            product_ids, customer=state["customer_attributes"], documents=state["documents"],
        )
        validate_legal_agent_output(result)
        return {"eligibility_result": dict(result), "graph_node_trace": trace}

    async def _credit_node(self, state: ExpertGraphState) -> Dict[str, Any]:
        """Reads product_result + the deterministic eligibility_result; never
        reads insurance_result."""
        trace = [*state.get("graph_node_trace", []), "credit_expert"]
        if state.get("start_index", 0) > 1 and state.get("credit_result"):
            return {"graph_node_trace": trace}
        task = self._task(
            state,
            agent_type=AgentType.CREDIT_EXPERT,
            task_type="credit_structuring",
            objective="Phân tích sâu hồ sơ, bối cảnh, khả năng trả nợ và cấu trúc tín dụng sơ bộ.",
            round_number=1,
            input_payload={
                "product_ids": [
                    item.get("product_id") for item in state.get("product_result", {}).get("recommendations", [])
                ],
                "eligibility_status": state.get("eligibility_result", {}).get("overall_status"),
            },
        )
        entities = state.get("intent_entities", {})
        finding = await self.credit_agent.analyze(
            task,
            product_result=state.get("product_result", {}),
            eligibility_result=state.get("eligibility_result", {}),
            customer_attributes=state["customer_attributes"],
            documents=state["documents"],
            business_snapshot=state.get("business_snapshot"),
            requested_amount=self._entity_number(entities, "expected_amount", "amount", "requested_amount"),
            requested_tenor_months=self._entity_integer(entities, "tenor_months", "tenor"),
            loan_purpose=self._entity_text(entities, "loan_purpose", "purpose", "objective"),
            branch=state["branch"],
        )
        return {
            "assignments": [*state.get("assignments", []), task],
            "findings": [*state.get("findings", []), finding],
            "credit_result": dict(finding.domain_result),
            "graph_node_trace": trace,
        }

    async def _insurance_node(self, state: ExpertGraphState) -> Dict[str, Any]:
        """Reads only product_result + customer profile; never reads
        eligibility_result or credit_result -- fully independent of the
        other two experts' findings."""
        trace = [*state.get("graph_node_trace", []), "insurance_expert"]
        if state.get("start_index", 0) > 1 and state.get("insurance_result"):
            return {"graph_node_trace": trace}
        task = self._task(
            state,
            agent_type=AgentType.INSURANCE_EXPERT,
            task_type="insurance_coverage_review",
            objective="Đánh giá mức độ sẵn sàng bảo hiểm cho sản phẩm đã đề xuất.",
            round_number=1,
            input_payload={
                "product_ids": [
                    item.get("product_id") for item in state.get("product_result", {}).get("recommendations", [])
                ],
            },
        )
        finding = await self.insurance_agent.analyze(
            task,
            product_result=state.get("product_result", {}),
            customer_attributes=state["customer_attributes"],
            documents=state["documents"],
            business_snapshot=state.get("business_snapshot"),
            branch=state["branch"],
        )
        return {
            "assignments": [*state.get("assignments", []), task],
            "findings": [*state.get("findings", []), finding],
            "insurance_result": dict(finding.domain_result),
            "graph_node_trace": trace,
        }

    @staticmethod
    def _route_after_experts(state: ExpertGraphState) -> str:
        return "alternative" if state.get("credit_result", {}).get("hard_blocks") else "synthesis"

    async def _product_alternative_node(self, state: ExpertGraphState) -> Dict[str, Any]:
        trace = [*state.get("graph_node_trace", []), "product_alternative"]
        dedup_key = canonical_hash(
            {"case_id": state["case_id"], "type": "find_non_credit_alternative", "exclude_credit": True}
        )
        existing = {item.dedup_key for item in state.get("assistance_requests", [])}
        if dedup_key in existing:
            return {"graph_node_trace": trace}
        # Issued by the Coordinator, mediating on behalf of the
        # deterministic credit hard-block -- not by an "Agent" (there is
        # no LegalExpert runtime in this graph to be the sender).
        request = AssistanceRequest(
            request_id=f"HELP-{uuid.uuid4().hex[:10].upper()}",
            case_id=state["case_id"],
            trace_id=state["trace_id"],
            from_agent=AgentType.PLANNER_COORDINATOR,
            target_agent=AgentType.PRODUCT_EXPERT,
            question_type="find_non_credit_alternative",
            question="Tìm phương án phi tín dụng vẫn hỗ trợ mục tiêu trong khi tín dụng đang hard-block.",
            constraints=("exclude:credit=true", "preserve:blocked_credit_candidate=true"),
            priority="high",
            dedup_key=dedup_key,
            round=2,
        )
        task = self._task(
            state,
            agent_type=AgentType.PRODUCT_EXPERT,
            task_type="product_alternative",
            objective=request.question,
            round_number=2,
            input_payload={"request_id": request.request_id, "constraints": list(request.constraints)},
            constraints=request.constraints,
        )
        parent = next(
            (item.finding_id for item in state.get("findings", []) if item.agent_type == AgentType.PRODUCT_EXPERT),
            None,
        )
        finding = await self.product_agent.analyze(
            task,
            query=state["query"],
            branch=state["branch"],
            customer_attributes=state["customer_attributes"],
            top_k=2,
            exclude_credit=True,
            parent_finding_id=parent,
        )
        return {
            "assignments": [*state.get("assignments", []), task],
            "findings": [*state.get("findings", []), finding],
            "assistance_requests": [*state.get("assistance_requests", []), request],
            "alternative_product_result": dict(finding.domain_result),
            "graph_node_trace": trace,
        }

    def _eligibility_alternative_node(self, state: ExpertGraphState) -> Dict[str, Any]:
        trace = [*state.get("graph_node_trace", []), "eligibility_check_alternative"]
        alternative = state.get("alternative_product_result") or {}
        if not alternative.get("recommendations"):
            return {"alternative_eligibility_result": None, "graph_node_trace": trace}
        product_ids = [str(item.get("product_id")) for item in alternative.get("recommendations", [])]
        result = self.eligibility_engine.evaluate(
            product_ids, customer=state["customer_attributes"], documents=state["documents"],
        )
        validate_legal_agent_output(result)
        return {"alternative_eligibility_result": dict(result), "graph_node_trace": trace}

    async def _synthesis_node(self, state: ExpertGraphState) -> Dict[str, Any]:
        trace = [*state.get("graph_node_trace", []), "coordinator_synthesis"]
        now = datetime.now(timezone.utc)
        notices: List[ConstraintNotice] = []
        for product in state.get("eligibility_result", {}).get("products", []):
            for rule in product.get("rules", []):
                status = str(rule.get("status"))
                if status not in {"failed", "pending_review", "pending_information"}:
                    continue
                notices.append(
                    ConstraintNotice(
                        constraint_id=f"CON-{uuid.uuid4().hex[:10].upper()}",
                        case_id=state["case_id"],
                        trace_id=state["trace_id"],
                        # "LegalExpert" here labels the deterministic
                        # eligibility/legal rule domain the contract enum
                        # allows -- no LegalExpert Agent runs in this graph.
                        issued_by="LegalExpert",
                        constraint_type="missing_information" if status == "pending_information" else "hard_rule",
                        severity="blocking" if str(rule.get("severity")) == "blocking" else "review",
                        description=(
                            f"{product.get('product_id')} / {rule.get('rule_id')} = {status}; "
                            "Coordinator không được thay đổi verdict."
                        ),
                        overridable=bool(rule.get("human_review_allowed", False)),
                        effective_at=now,
                    )
                )
        findings = state.get("findings", [])
        assignments = state.get("assignments", [])
        requests = state.get("assistance_requests", [])
        hard_block = bool(state.get("credit_result", {}).get("hard_blocks")) or bool(
            state.get("insurance_result", {}).get("hard_blocks")
        )
        convergence_hash = canonical_hash(
            {
                "findings": [item.output_hash for item in findings],
                "constraints": [item.constraint_id for item in notices],
                "assistance": [item.dedup_key for item in requests],
            }
        )
        session = CollaborationSession(
            session_id=f"COLLAB-{uuid.uuid4().hex[:12].upper()}",
            case_id=state["case_id"],
            trace_id=state["trace_id"],
            status="needs_human_review" if hard_block else "converged",
            current_round=2 if requests else 1,
            task_ids=self._unique(item.task_id for item in assignments),
            finding_ids=self._unique(item.finding_id for item in findings),
            assistance_request_ids=self._unique(item.request_id for item in requests),
            constraint_ids=self._unique(item.constraint_id for item in notices),
            convergence_hashes=[convergence_hash],
            stop_reason="hard_block_preserved" if hard_block else "no_new_information",
            started_at=now,
            completed_at=datetime.now(timezone.utc),
        )
        synthesis = synthesize_expert_results(
            case_id=state["case_id"],
            trace_id=state["trace_id"],
            product_result=state.get("product_result", {}),
            eligibility_result=state.get("eligibility_result", {}),
            credit_result=state.get("credit_result", {}),
            insurance_result=state.get("insurance_result"),
            alternative_product_result=state.get("alternative_product_result"),
            alternative_eligibility_result=state.get("alternative_eligibility_result"),
            findings=findings,
        )
        return {
            "constraint_notices": notices,
            "collaboration_session": session,
            "synthesis_result": synthesis,
            "graph_node_trace": trace,
        }

    @staticmethod
    def _task(
        state: ExpertGraphState,
        *,
        agent_type: AgentType,
        task_type: str,
        objective: str,
        round_number: int,
        input_payload: Dict[str, Any],
        constraints: Sequence[str] = (),
    ) -> TaskAssignment:
        manifest = manifest_for(agent_type)
        return TaskAssignment(
            task_id=f"TASK-{agent_type.value.upper()}-{uuid.uuid4().hex[:10].upper()}",
            case_id=state["case_id"],
            trace_id=state["trace_id"],
            assigned_to=agent_type,
            task_type=task_type,
            objective=objective,
            constraints=tuple(constraints),
            allowed_tool_names=manifest.allowed_tools,
            round=round_number,
            deadline_at=datetime.now(timezone.utc) + timedelta(milliseconds=manifest.timeout_ms),
            input_hash=canonical_hash(input_payload),
        )

    @staticmethod
    def _unique(values) -> List[str]:
        return list(dict.fromkeys(str(value) for value in values))

    @staticmethod
    def _unwrap(value: Any) -> Any:
        return value.get("value") if isinstance(value, dict) and "value" in value else value

    @classmethod
    def _entity_number(cls, entities: Dict[str, Any], *keys: str) -> Optional[float]:
        for key in keys:
            value = cls._unwrap(entities.get(key))
            if value is None or isinstance(value, bool):
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None

    @classmethod
    def _entity_integer(cls, entities: Dict[str, Any], *keys: str) -> Optional[int]:
        value = cls._entity_number(entities, *keys)
        return int(value) if value is not None else None

    @classmethod
    def _entity_text(cls, entities: Dict[str, Any], *keys: str) -> Optional[str]:
        for key in keys:
            value = cls._unwrap(entities.get(key))
            if value is not None and str(value).strip():
                return str(value).strip()
        return None
