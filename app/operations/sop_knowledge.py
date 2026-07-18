"""Operations SOP knowledge base -- RAG & Guardrail Implementation Plan
Phase 2 section 11.3 ("Operations Agent hiện chưa có retrieval thật").

New, additive module: does NOT modify app/operations/service.py (which
was under active concurrent edit by another agent during this Phase --
see docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md Phase 2 "Agent Migration"
for why touching that file directly was avoided). OperationsService.prepare()
still reads data/synthetic/v2/operations_sop.json as a static dict, exactly
as before -- this module is a separate, parallel SOP KNOWLEDGE index
(mirroring the shape of app.knowledge.legal_service.LegalKnowledgeService)
that ControlledRetrievalOrchestrator can query for the OPERATIONS agent
type. It proves Operations retrieval is real and correctly grounded/cited,
without claiming OperationsService itself has been migrated.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List

from typing import Optional

from app.config import settings
from app.knowledge.index import EmbeddingProvider, PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk
from app.knowledge.retrieval_contracts import AuthorityTier, VerificationStatus

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOP_WORKFLOW = ROOT / "data" / "synthetic" / "v3" / "operations" / "sop_workflow.json"


class OperationsKnowledgeService:
    """Real RAG for SOP steps -- one KnowledgeChunk per (workflow_id,
    step_id), so a Product/Case-specific Operations query ("bước tiếp theo
    cho Bulk Payment là gì?") can be answered with a cited, versioned SOP
    step instead of an entire static JSON dump."""

    def __init__(self, index_path: str | Path | None = None, *, provider: Optional[EmbeddingProvider] = None) -> None:
        # See app/knowledge/legal_service.py's __init__ comment: without an
        # explicit provider=, this hits the real, SHARED
        # data/vector_db/openai_vector_cache.json via .env's
        # KNOWLEDGE_EMBEDDING_PROVIDER=openai. Tests/benchmarks pass
        # provider=LocalEmbedding() to stay isolated and deterministic.
        path = index_path or (Path(settings.VECTOR_DB_DIR) / "v2_operations_sop.sqlite3")
        self.index = PersistentHybridIndex(path, provider=provider)

    def ingest(self, sop_path: str | Path = DEFAULT_SOP_WORKFLOW) -> int:
        source = Path(sop_path)
        raw = source.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        effective_from = payload.get("effective_from", "2026-01-01")

        # Phase 3 (Hierarchical Parent-Child Retrieval, section 26): one
        # synthetic PARENT chunk per workflow_id -- a workflow-level
        # overview whose text is the ordered list of its steps' task
        # templates, so expand_to_parent_context() on a retrieved step
        # gives an Agent the surrounding workflow context without ever
        # dumping the entire SOP document. Grounded in this repo's real
        # SOP data (workflow_id groups already exist in sop_workflow.json)
        # -- not a fabricated hierarchy layered on unrelated chunks.
        steps_by_workflow: dict[str, list] = {}
        for step in payload["steps"]:
            steps_by_workflow.setdefault(step["workflow_id"], []).append(step)

        chunks: List[KnowledgeChunk] = []
        for workflow_id, steps in steps_by_workflow.items():
            steps_sorted = sorted(steps, key=lambda s: s["sequence"])
            product_id = steps_sorted[0]["product_id"]
            overview_text = f"{workflow_id} -- quy trình gồm {len(steps_sorted)} bước: " + "; ".join(
                f"({s['sequence']}) {s['task_template']}" for s in steps_sorted
            )
            parent_chunk_id = f"{workflow_id}:OVERVIEW"
            chunks.append(
                KnowledgeChunk(
                    chunk_id=parent_chunk_id,
                    document_id=steps_sorted[0]["source_document_id"], document_version=steps_sorted[0]["version"],
                    product_id=product_id, section_path="OVERVIEW", chunk_type="sop_workflow_overview",
                    text=overview_text, effective_from=effective_from, effective_to=None, active=True,
                    segments=[], access_scope={"branches": ["*"]},
                    content_hash=hashlib.sha256(overview_text.encode("utf-8")).hexdigest(),
                    source_type="sop", authority_tier=AuthorityTier.TIER_2_VERIFIED_INTERNAL,
                    verification_status=VerificationStatus.VERIFIED,
                )
            )
            for step in steps_sorted:
                text = " | ".join(
                    [
                        f"{step['workflow_id']} bước {step['step_id']} (thứ tự {step['sequence']})",
                        f"Điều kiện tiên quyết: {step['precondition']}",
                        f"Công việc: {step['task_template']}",
                        f"Người phụ trách: {step['owner_role']}",
                        f"SLA: {step['sla_hours']} giờ",
                        f"Cần phê duyệt: {'có' if step['approval_required'] else 'không'}",
                    ]
                )
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=f"{step['workflow_id']}:{step['step_id']}:{step['version']}",
                        document_id=step["source_document_id"],
                        document_version=step["version"],
                        product_id=step["product_id"],
                        section_path=step["step_id"],
                        chunk_type="sop_step",
                        text=text,
                        effective_from=effective_from,
                        effective_to=None,
                        active=True,
                        segments=[],
                        access_scope={"branches": ["*"]},
                        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        source_type="sop",
                        authority_tier=AuthorityTier.TIER_2_VERIFIED_INTERNAL,
                        verification_status=VerificationStatus.VERIFIED,
                        parent_chunk_id=parent_chunk_id,
                    )
                )
        source_hash = hashlib.sha256(raw).hexdigest()
        return self.index.upsert(chunks, source_hash=source_hash, dataset_version=payload["registry_version"])

    def ensure_index(self) -> None:
        if self.index.count() == 0:
            self.ingest()
