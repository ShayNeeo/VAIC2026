"""End-to-end synthetic V2 analysis workflow with safe partial resume."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Dict, Iterable, List

from app.eligibility.engine import EligibilityEngine
from app.intent.extractor import IntentExtractor
from app.intent.slot_resolver import SlotResolver
from app.knowledge.legal_service import LegalKnowledgeService
from app.knowledge.service import ProductKnowledgeService
from app.operations.service import OperationsService
from app.product.service import ProductService
from app.safety.evidence_validator import ValidationStatus, validate_claim
from app.schemas.v2.shared_case_state import (
    Approval, ApprovalStatus, CaseStatus, Evidence, SharedCaseState, Task, TaskStatus,
)
from app.workflow.impact import impacted_nodes
from app.workflow.next_best import NextBestService
from app.workflow.planner import PlannerService
from app.workflow.risk_gate import RiskGateDecision, RiskGuardrailGate
from app.workflow.router import ComplexityRouter
from app.workflow.state_machine import transition


def _hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


class V2WorkflowEngine:
    def __init__(
        self,
        *,
        intent: IntentExtractor | None = None,
        product: ProductService | None = None,
        eligibility: EligibilityEngine | None = None,
        operations: OperationsService | None = None,
        planner: PlannerService | None = None,
        next_best: NextBestService | None = None,
        router: ComplexityRouter | None = None,
        risk_gate: RiskGuardrailGate | None = None,
        legal_knowledge: LegalKnowledgeService | None = None,
        index_path: str | None = None,
    ) -> None:
        self.intent = intent or IntentExtractor()
        self.product = product or ProductService(ProductKnowledgeService(index_path))
        self.eligibility = eligibility or EligibilityEngine()
        self.operations = operations or OperationsService()
        self.planner = planner or PlannerService()
        self.next_best = next_best or NextBestService()
        self.router = router or ComplexityRouter()
        self.risk_gate = risk_gate or RiskGuardrailGate()
        # Independent source-of-truth for evidence validation (see
        # _product_evidence/_legal_evidence): the SAME index that serves
        # legal/eligibility RAG search, so a claimed quote is checked against
        # what the system actually has indexed, not re-trusted at face value.
        self.legal_knowledge = legal_knowledge or LegalKnowledgeService()

    async def run(self, state: SharedCaseState, *, force_route: str | None = None) -> SharedCaseState:
        """force_route ("simple"|"complex") bypasses ComplexityRouter for
        evaluation/benchmark purposes only (see benchmarks/run.py) -- default
        None preserves normal production routing untouched."""
        state.status = transition(state.status, CaseStatus.UNDERSTANDING)
        started = perf_counter()
        result = await self.intent.extract_intent(state.request.text, state.request.message_id, state.context)
        result = SlotResolver().resolve(result, state.context)
        state.intent_result = result
        intent_run = getattr(self.intent, "last_run", {})
        self._ai_log(
            state,
            component="RequirementExtractor",
            event="intent_extracted",
            mode=str(intent_run.get("mode", "unknown")),
            model=str(intent_run.get("model", "unknown")),
            prompt_version=str(intent_run.get("prompt_version", "intent-schema-v2.1")),
            latency_ms=self._elapsed_ms(started),
            token_usage=dict(intent_run.get("token_usage") or {}),
            output_summary={
                "primary_intent": result.primary_intent,
                "sub_intents": result.sub_intents,
                "confidence": result.overall_confidence,
                "recommended_action": result.recommended_action.value,
                "fallback_reason": intent_run.get("fallback_reason"),
            },
        )
        self._event(state, "Intent", "intent_resolved", {"primary": result.primary_intent, "sub": result.sub_intents})
        if result.recommended_action.value in {"ask_clarification", "request_confirmation"}:
            state.status = transition(state.status, CaseStatus.CLARIFICATION_REQUIRED)
            state.workflow.current_node = "resolve_slots"
            return self._touch(state)
        if force_route is not None:
            if force_route not in {"simple", "complex"}:
                raise ValueError(f"force_route must be 'simple' or 'complex', got {force_route!r}")
            is_complex = force_route == "complex"
        else:
            is_complex = self.router.is_complex(state)

        if not is_complex:
            state.status = transition(state.status, CaseStatus.COMPLETED)
            from app.schemas.v2.planning import ExecutionPlan, PlanStep
            state.execution_plan = ExecutionPlan(
                plan_version=1,
                goals=[result.user_goal],
                steps=[PlanStep(step_id="product", title="Tra cứu thông tin sản phẩm (Single-Agent RAG)", owner="Product", status="completed", reason="Câu hỏi đơn giản")],
                created_at=datetime.now(timezone.utc)
            ).model_dump(mode="json")
            
            branch = str(state.context.employee.access_scope.get("branch") or "*")
            requested = state.intent_result.entities.get("product_ids") if state.intent_result else None
            state.product_result = self.product.recommend(
                state.request.text, branch=branch, requested_product_ids=requested, customer_attributes=state.context.customer.attributes
            )
            self._ai_log(
                state, component="ComplexityRouter", event="simple_query_routed",
                mode="single_agent_rag", model="none", prompt_version="v2.1", latency_ms=0,
                output_summary={"action": "direct_rag", "hits": len(state.product_result.get("recommendations", []))}
            )
            return self._touch(state)

        state.status = transition(state.status, CaseStatus.PLANNED)
        initial_plan = self.planner.plan(
            snapshot=state.customer_business_snapshot,
            user_goal=result.user_goal,
        )
        state.execution_plan = initial_plan.model_dump(mode="json")
        self._ai_log(
            state,
            component="Planner",
            event="initial_plan_created",
            mode="deterministic_workflow",
            model="planner-rules-v1",
            prompt_version="planner-contract-v1",
            latency_ms=0,
            output_summary={
                "plan_version": initial_plan.plan_version,
                "step_ids": [item.step_id for item in initial_plan.steps],
            },
        )
        self._event(state, "Planner", "planner_plan_created", {"plan_version": initial_plan.plan_version})
        state.workflow.tasks = self._tasks(state)
        state.status = transition(state.status, CaseStatus.IN_ANALYSIS)
        return self._analysis(state, start_at="retrieve_products")

    async def rerun_with_message(
        self,
        state: SharedCaseState,
        *,
        message: str,
        message_id: str,
    ) -> SharedCaseState:
        """Start a new analysis run while preserving case, context and user-safe history."""

        if state.status in {CaseStatus.COMPLETED, CaseStatus.REJECTED}:
            raise ValueError(f"case cannot accept a new message from {state.status.value}")
        now = datetime.now(timezone.utc)
        self._event(
            state,
            "RM",
            "new_message_received",
            {"previous_message_id": state.request.message_id, "message_id": message_id},
        )
        state.status = CaseStatus.NEW
        state.request = state.request.model_copy(
            update={"message_id": message_id, "text": message, "received_at": now}
        )
        state.intent_result = None
        state.product_result = None
        state.eligibility_result = None
        state.operations_result = None
        state.execution_plan = None
        state.next_best_questions = []
        state.next_best_actions = []
        state.evidences = []
        state.approval = Approval(status=ApprovalStatus.NOT_REQUIRED)
        state.workflow = state.workflow.model_copy(
            update={"current_node": None, "tasks": [], "loop_count": 0, "resume_from_nodes": []}
        )
        return await self.run(state)

    def resume(self, state: SharedCaseState, *, changes: Iterable[str]) -> SharedCaseState:
        nodes = impacted_nodes(changes)
        if state.workflow.loop_count >= 3:
            state.status = CaseStatus.FAILED
            self._event(state, "Workflow", "max_resume_loops", {"changes": list(changes)})
            return self._touch(state)
        if state.status not in {CaseStatus.PENDING_INFORMATION, CaseStatus.PENDING_REVIEW, CaseStatus.PENDING_APPROVAL, CaseStatus.FAILED}:
            raise ValueError(f"case cannot resume from {state.status.value}")
        state.status = transition(state.status, CaseStatus.IN_ANALYSIS)
        state.workflow.loop_count += 1
        state.workflow.resume_from_nodes = nodes
        state.approval = Approval(status=ApprovalStatus.NOT_REQUIRED)
        self._event(state, "Workflow", "partial_resume", {"nodes": nodes})
        start = nodes[0]
        if start in {"collect_context", "extract_intent", "resolve_slots"}:
            raise ValueError("context/request changes require async full run with a new message")
        return self._analysis(state, start_at=start)

    def _analysis(self, state: SharedCaseState, *, start_at: str) -> SharedCaseState:
        nodes = ["retrieve_products", "evaluate_eligibility", "validate_evidence", "prepare_operations"]
        start_index = nodes.index(start_at)
        if start_index <= 0:
            started = perf_counter()
            requested = state.intent_result.entities.get("product_ids") if state.intent_result else None
            branch = str(state.context.employee.access_scope.get("branch") or "*")
            state.product_result = self.product.recommend(
                state.request.text,
                branch=branch,
                requested_product_ids=requested,
                customer_attributes=state.context.customer.attributes,
            )
            self._complete_task(state, "product", state.product_result)
            self._product_evidence(state)
            recommendations = state.product_result.get("recommendations", [])
            self._ai_log(
                state,
                component="ProductRAG",
                event="products_retrieved_and_ranked",
                mode="persistent_hybrid_retrieval",
                model=self.product.knowledge.index.provider.name,
                prompt_version="product-matcher-v2.1",
                latency_ms=self._elapsed_ms(started),
                output_summary={
                    "product_ids": [item.get("product_id") for item in recommendations],
                    "match_scores": {
                        item.get("product_id"): item.get("match_score") for item in recommendations
                    },
                },
                sources=[
                    {
                        "document_id": source.get("source_document_id"),
                        "version": source.get("source_version"),
                        "location": source.get("location"),
                        "retrieval_score": source.get("retrieval_score"),
                    }
                    for item in recommendations
                    for source in item.get("evidences", [])
                ],
            )
        if not state.product_result or not state.product_result.get("recommendations"):
            state.status = transition(state.status, CaseStatus.PENDING_REVIEW)
            self._event(state, "Product", "no_grounded_product", {})
            return self._touch(state)
        if start_index <= 1:
            started = perf_counter()
            product_ids = [item["product_id"] for item in state.product_result["recommendations"]]
            documents = [
                {"document_type": item.document_type, "status": item.status.value, "document_id": item.document_id}
                for item in state.context.documents
            ]
            state.eligibility_result = self.eligibility.evaluate(
                product_ids,
                customer=state.context.customer.attributes,
                documents=documents,
            )
            self._complete_task(state, "eligibility", state.eligibility_result)
            self._legal_evidence(state)
            self._ai_log(
                state,
                component="EligibilityEngine",
                event="rules_evaluated",
                mode="deterministic_fail_closed",
                model="no_llm",
                prompt_version=f"rule-registry-{state.eligibility_result.get('registry_version', 'unknown')}",
                latency_ms=self._elapsed_ms(started),
                output_summary={
                    "overall_status": state.eligibility_result.get("overall_status"),
                    "rules": [
                        {
                            "rule_id": rule.get("rule_id"),
                            "version": rule.get("rule_version"),
                            "status": rule.get("status"),
                        }
                        for product in state.eligibility_result.get("products", [])
                        for rule in product.get("rules", [])
                    ],
                },
                sources=[
                    {
                        "document_id": item.source_document_id,
                        "version": item.source_version,
                        "location": item.location,
                    }
                    for item in state.evidences
                    if item.module == "Eligibility"
                ],
            )
        questions, actions = self.next_best.build(state.eligibility_result or {})
        state.next_best_questions = [item.model_dump(mode="json") for item in questions]
        state.next_best_actions = [item.model_dump(mode="json") for item in actions]
        replanned = self.planner.replan(
            state.execution_plan,
            eligibility_result=state.eligibility_result or {},
        )
        state.execution_plan = replanned.model_dump(mode="json")
        self._ai_log(
            state,
            component="Planner",
            event="plan_revised_from_eligibility",
            mode="deterministic_workflow",
            model="planner-rules-v1",
            prompt_version="planner-contract-v1",
            latency_ms=0,
            output_summary={
                "plan_version": replanned.plan_version,
                "reason": replanned.changed_because,
                "question_count": len(state.next_best_questions),
                "action_count": len(state.next_best_actions),
            },
        )
        self._event(
            state,
            "Planner",
            "planner_replanned",
            {"plan_version": replanned.plan_version, "reason": replanned.changed_because},
        )
        if start_index <= 2:
            all_valid = all(item.is_valid and item.quote for item in state.evidences)
            self._ai_log(
                state,
                component="EvidenceValidator",
                event="claims_validated",
                mode="deterministic_guardrail",
                model="no_llm",
                prompt_version="evidence-policy-v1",
                latency_ms=0,
                output_summary={"valid": all_valid, "claim_count": len(state.evidences)},
                sources=[{"claim_id": item.claim_id, "valid": item.is_valid} for item in state.evidences],
            )
            self._event(state, "EvidenceValidator", "evidence_validated", {"valid": all_valid, "count": len(state.evidences)})
            if not all_valid:
                self._apply_risk_gate(state)
                state.status = transition(state.status, CaseStatus.PENDING_REVIEW)
                return self._touch(state)
        if start_index <= 3:
            started = perf_counter()
            state.operations_result = self.operations.prepare(
                organization=state.context.employee.organization_unit,
                customer_id=str(state.context.customer.customer_id),
                case_id=state.case_id,
                customer_name=str(state.context.customer.attributes.get("name", state.context.customer.customer_id)),
                product_result=state.product_result,
                eligibility_result=state.eligibility_result or {},
                available_documents=[
                    {
                        "document_type": item.document_type,
                        "status": item.status.value,
                        "document_id": item.document_id,
                    }
                    for item in state.context.documents
                ],
                previous_result=state.operations_result,
                execution_plan=state.execution_plan,
                next_best_questions=state.next_best_questions,
                next_best_actions=state.next_best_actions,
                evidence_ids=[item.claim_id for item in state.evidences],
            )
            self._complete_task(state, "operations", state.operations_result)
            self._ai_log(
                state,
                component="OperationsComposer",
                event="drafts_prepared",
                mode="template_plus_rules",
                model="no_llm",
                prompt_version="operations-template-v1",
                latency_ms=self._elapsed_ms(started),
                output_summary={
                    "artifact_version": state.operations_result.get("artifact_version"),
                    "action_readiness": state.operations_result.get("action_readiness"),
                    "missing_count": len(state.operations_result.get("missing_information", [])),
                    "external_side_effect_count": len(state.operations_result.get("external_side_effects", [])),
                },
            )
        decision = self._apply_risk_gate(state)
        if decision.outcome == "approve":
            state.status = transition(state.status, CaseStatus.PENDING_APPROVAL)
            state.approval = Approval(
                status=ApprovalStatus.PENDING,
                payload_hash=_hash(state.operations_result.get("action_payload") or state.operations_result["crm_case_draft"]),
            )
        elif decision.outcome == "need_information":
            state.status = transition(state.status, CaseStatus.PENDING_INFORMATION)
        else:
            state.status = transition(state.status, CaseStatus.PENDING_REVIEW)
        state.workflow.current_node = "await_approval" if decision.outcome == "approve" else "await_information"
        return self._touch(state)

    def clear_specialist_block(self, state: SharedCaseState) -> SharedCaseState:
        """A human specialist (Legal/Product) has resolved every reason the
        risk gate put this case into PENDING_REVIEW -- see
        app/api/v2/employee_router.py's specialist-reviews endpoint, which
        only calls this once ALL of RiskGateDecision.required_reviewer_roles
        have a matching 'cleared' review for the current case version.

        Deliberately does NOT re-run evaluate_eligibility/validate_evidence:
        those are deterministic and would just re-derive the exact same
        blocking verdict from the exact same underlying documents, since a
        specialist's judgment is not new input data those engines consume --
        it is a human override of their verdict, which is a decision this
        method (and its caller) makes explicitly and audibly, never silently
        inside the deterministic pipeline."""
        if state.status != CaseStatus.PENDING_REVIEW:
            raise ValueError(f"cannot clear specialist block from {state.status.value}")
        if state.operations_result is None:
            state.operations_result = self.operations.prepare(
                organization=state.context.employee.organization_unit,
                customer_id=str(state.context.customer.customer_id),
                case_id=state.case_id,
                customer_name=str(state.context.customer.attributes.get("name", state.context.customer.customer_id)),
                product_result=state.product_result or {},
                eligibility_result=state.eligibility_result or {},
                available_documents=[
                    {"document_type": item.document_type, "status": item.status.value, "document_id": item.document_id}
                    for item in state.context.documents
                ],
                execution_plan=state.execution_plan,
                next_best_questions=state.next_best_questions,
                next_best_actions=state.next_best_actions,
                evidence_ids=[item.claim_id for item in state.evidences],
            )
            self._complete_task(state, "operations", state.operations_result)
        payload = state.operations_result.get("action_payload") or state.operations_result.get("crm_case_draft") or {}
        state.status = transition(state.status, CaseStatus.PENDING_APPROVAL)
        state.approval = Approval(status=ApprovalStatus.PENDING, payload_hash=_hash(payload))
        state.workflow.current_node = "await_approval"
        self._event(state, "SpecialistReview", "specialist_review_cleared_case", {})
        return self._touch(state)

    def _apply_risk_gate(self, state: SharedCaseState) -> RiskGateDecision:
        decision = self.risk_gate.evaluate(
            eligibility_result=state.eligibility_result or {},
            evidences=state.evidences,
        )
        state.risk_gate_result = decision.to_dict()
        self._ai_log(
            state,
            component="RiskGuardrailGate",
            event="risk_evaluated",
            mode="deterministic_guardrail",
            model="no_llm",
            prompt_version="risk-gate-v1",
            latency_ms=0,
            output_summary=decision.to_dict(),
        )
        self._event(state, "RiskGuardrailGate", "risk_evaluated", decision.to_dict())
        return decision

    @staticmethod
    def _tasks(state: SharedCaseState) -> List[Task]:
        definitions = [
            ("product", "product_matching", "Product", []),
            ("eligibility", "eligibility_check", "Compliance", ["product"]),
            ("evidence", "evidence_validation", "Safety", ["eligibility"]),
            ("operations", "operations_draft", "Operations", ["evidence"]),
        ]
        return [
            Task(
                task_id=task_id, task_type=task_type, owner=owner, status=TaskStatus.READY if not dependencies else TaskStatus.PENDING,
                dependencies=dependencies, dedup_key=f"{state.case_id}:{task_type}",
            )
            for task_id, task_type, owner, dependencies in definitions
        ]

    @staticmethod
    def _complete_task(state: SharedCaseState, task_id: str, output: Dict[str, Any]) -> None:
        for task in state.workflow.tasks:
            if task.task_id == task_id:
                task.status = TaskStatus.COMPLETED
                task.input_hash = _hash({"request": state.request.text, "context": state.context.customer.profile_version})
                task.output_ref = f"{task_id}_result:{_hash(output)[7:19]}"

    def _product_evidence(self, state: SharedCaseState) -> None:
        state.evidences = [item for item in state.evidences if item.module != "Product"]
        index = self.product.knowledge.index
        for recommendation in state.product_result.get("recommendations", []):
            for pos, source in enumerate(recommendation.get("evidences", []), start=1):
                claim_id = f"PROD-{recommendation['product_id']}-{pos}"
                result = validate_claim(
                    claim_id=claim_id,
                    source_document_id=source["source_document_id"],
                    source_version=source["source_version"],
                    quote=source["quote"],
                    index=index,
                )
                state.evidences.append(
                    Evidence(
                        claim_id=claim_id, module="Product",
                        claim=f"Sản phẩm {recommendation['product_id']} tồn tại trong catalog còn hiệu lực.",
                        source_document_id=source["source_document_id"], source_version=source["source_version"],
                        location=source["location"], quote=source["quote"],
                        is_valid=result.is_valid,
                        validation_score=1.0 if result.exact_match else 0.0,
                        human_review_allowed=result.status == ValidationStatus.INVALID,
                    )
                )

    def _legal_evidence(self, state: SharedCaseState) -> None:
        state.evidences = [item for item in state.evidences if item.module != "Eligibility"]
        self.legal_knowledge.ensure_index()
        index = self.legal_knowledge.index
        for product in state.eligibility_result.get("products", []):
            for rule in product.get("rules", []):
                claim_id = f"ELIG-{product['product_id']}-{rule['rule_id']}"
                result = validate_claim(
                    claim_id=claim_id,
                    source_document_id=rule["source_document_id"],
                    source_version=rule["source_version"],
                    quote=rule["source_quote"],
                    index=index,
                )
                state.evidences.append(
                    Evidence(
                        claim_id=claim_id, module="Eligibility",
                        claim=f"{rule['rule_id']} kết luận {rule['status']} cho {product['product_id']}.",
                        source_document_id=rule["source_document_id"], source_version=rule["source_version"],
                        location=rule["source_location"], quote=rule["source_quote"],
                        is_valid=result.is_valid,
                        validation_score=1.0 if result.exact_match else 0.0,
                        human_review_allowed=result.status == ValidationStatus.INVALID,
                    )
                )

    @staticmethod
    def _event(state: SharedCaseState, actor: str, action: str, payload: Dict[str, Any]) -> None:
        state.audit_events.append({"actor": actor, "action": action, "at": datetime.now(timezone.utc).isoformat(), "payload": payload})

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return max(0, round((perf_counter() - started) * 1000))

    @staticmethod
    def _ai_log(
        state: SharedCaseState,
        *,
        component: str,
        event: str,
        mode: str,
        model: str,
        prompt_version: str,
        latency_ms: int,
        output_summary: Dict[str, Any],
        sources: List[Dict[str, Any]] | None = None,
        token_usage: Dict[str, int] | None = None,
    ) -> None:
        """Persist a sanitized decision record without raw prompts, PII or secrets."""
        state.ai_decision_log.append(
            {
                "log_id": f"AI-{len(state.ai_decision_log) + 1:04d}",
                "at": datetime.now(timezone.utc).isoformat(),
                "trace_id": state.trace_id,
                "case_id": state.case_id,
                "component": component,
                "event": event,
                "mode": mode,
                "model": model,
                "prompt_or_policy_version": prompt_version,
                "workflow_version": state.workflow.workflow_version,
                "latency_ms": latency_ms,
                "token_usage": token_usage or {"input": 0, "output": 0, "total": 0},
                "estimated_cost": 0.0,
                "output_summary": output_summary,
                "sources": sources or [],
                "safety": {"raw_pii_logged": False, "secret_logged": False},
            }
        )

    @staticmethod
    def _touch(state: SharedCaseState) -> SharedCaseState:
        state.updated_at = datetime.now(timezone.utc)
        return state
