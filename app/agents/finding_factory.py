"""Shared construction helpers for immutable ExpertFinding artifacts."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from app.agents.contracts import (
    AgentManifest,
    AgentRunMetadata,
    ConfidenceBreakdown,
    EvidenceReference,
    ExpertFinding,
    StopReason,
    TaskAssignment,
    canonical_hash,
)
from app.agents.manifests import TOOL_POLICY_VERSION
from app.safety.domain_guardrails import validate_no_hidden_reasoning


def build_finding(
    *,
    manifest: AgentManifest,
    task: TaskAssignment,
    finding_id: str,
    conclusion: str,
    rationale: Iterable[str],
    known_facts: Iterable[Dict[str, Any]],
    inferences: Iterable[Dict[str, Any]],
    unknowns: Iterable[Dict[str, Any]],
    assumptions: Iterable[Dict[str, Any]],
    recommendations: Iterable[Dict[str, Any]],
    constraints: Iterable[Dict[str, Any]],
    evidence_refs: Iterable[EvidenceReference],
    confidence: ConfidenceBreakdown,
    domain_result: Dict[str, Any],
    stop_reason: StopReason,
    model: str,
    prompt_version: str,
    tools_called: Iterable[str],
    denied_tools: Iterable[str],
    latency_ms: int,
    fallback_reason: Optional[str],
    revision: int = 1,
    parent_finding_id: Optional[str] = None,
    assistance_request_ids: Iterable[str] = (),
) -> ExpertFinding:
    body = {
        "finding_id": finding_id,
        "task_id": task.task_id,
        "agent_type": manifest.agent_type.value,
        "revision": revision,
        "conclusion": conclusion,
        "decision_rationale_summary": list(rationale),
        "known_facts": list(known_facts),
        "inferences": list(inferences),
        "unknowns": list(unknowns),
        "assumptions": list(assumptions),
        "recommendations": list(recommendations),
        "constraints": list(constraints),
        "evidence_refs": [item.model_dump(mode="json") for item in evidence_refs],
        "domain_result": domain_result,
    }
    validate_no_hidden_reasoning(body)
    output_hash = canonical_hash(body)
    fallback_used = bool(fallback_reason)
    run = AgentRunMetadata(
        run_id=str(domain_result.get("agent_run_id") or f"RUN-{finding_id}"),
        model=model,
        mode="deterministic_fallback" if fallback_used else "llm",
        prompt_version=prompt_version,
        manifest_version=manifest.manifest_version,
        tool_policy_version=TOOL_POLICY_VERSION,
        tools_called=tuple(tools_called),
        denied_tools=tuple(denied_tools),
        latency_ms=max(0, int(latency_ms)),
        fallback_reason=fallback_reason,
        output_hash=output_hash,
    )
    return ExpertFinding(
        finding_id=finding_id,
        case_id=task.case_id,
        trace_id=task.trace_id,
        task_id=task.task_id,
        agent_type=manifest.agent_type,
        agent_manifest_version=manifest.manifest_version,
        revision=revision,
        parent_finding_id=parent_finding_id,
        conclusion=conclusion,
        decision_rationale_summary=tuple(rationale),
        known_facts=tuple(known_facts),
        inferences=tuple(inferences),
        unknowns=tuple(unknowns),
        assumptions=tuple(assumptions),
        recommendations=tuple(recommendations),
        constraints=tuple(constraints),
        evidence_refs=tuple(evidence_refs),
        confidence=confidence,
        assistance_request_ids=tuple(assistance_request_ids),
        fallback_used=fallback_used,
        output_hash=output_hash,
        stop_reason=stop_reason,
        agent_run=run,
        domain_result=domain_result,
    )


def validate_assignment(task: TaskAssignment, manifest: AgentManifest) -> None:
    if task.assigned_to != manifest.agent_type:
        raise ValueError(
            f"task {task.task_id} assigned to {task.assigned_to.value}, not {manifest.agent_type.value}"
        )
    if task.task_type not in manifest.accepted_task_types:
        raise ValueError(f"{manifest.agent_type.value} does not accept task type {task.task_type!r}")
    excess = set(task.allowed_tool_names) - set(manifest.allowed_tools)
    if excess:
        raise ValueError(f"task attempted to grant unauthorized tools: {sorted(excess)}")

