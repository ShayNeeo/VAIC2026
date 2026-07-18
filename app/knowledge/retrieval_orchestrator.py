"""Controlled Retrieval Plane runtime -- RAG & Guardrail Implementation
Plan Phase 2 section 4.

Status: IMPLEMENTED and covered by real tests
(tests/retrieval/test_runtime_orchestrator.py), but NOT wired into the
live Product/Legal/Operations call paths yet -- ProductService,
LegalKnowledgeService and OperationsService still call
PersistentHybridIndex.search()/their own logic directly (see
docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md Phase 2 "Agent Migration" for
why: those three files were concurrently being edited by another agent
with uncommitted changes during this Phase, so rewriting their internals
carried real collision risk against work this session did not author and
could not fully see in flight). This orchestrator is a complete, callable,
tested pipeline any of those services (or a new call site) can opt into.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.knowledge.agent_retrieval_policies import AGENT_RETRIEVAL_POLICIES
from app.knowledge.conflict_detection import detect_slot_conflicts
from app.knowledge.diversity import mmr_select
from app.knowledge.fusion import FusedCandidate, FusionMode, LinearSumFusion, ReciprocalRankFusion
from app.knowledge.index import PersistentHybridIndex
from app.knowledge.models import KnowledgeChunk, RetrievalHit
from app.knowledge.observability import EventObserver, RetrievalEvent
from app.knowledge.query_expansion import expanded_query_text
from app.knowledge.reranker import HeuristicReranker, RerankedCandidate, RerankerMode
from app.knowledge.retrieval_contracts import (
    ControlledRetrievalResult,
    GroundingItem,
    MetadataRef,
    RetrievalChannel,
    RetrievalDiagnostics,
    RetrievalErrorCode,
    RetrievalGroundingPack,
    RetrievalRequest,
    RetrievalStatus,
    SourceLocator,
    SourceLocatorType,
)


class ControlledRetrievalOrchestrator:
    """Runtime pipeline: validate request -> resolve Agent policy ->
    exact lookup -> sparse BM25 + dense search -> RRF fusion ->
    conflict detection -> top-k -> GroundingPack.

    Security/lifecycle filtering happens INSIDE the sparse/dense/exact
    calls (PersistentHybridIndex._filter_eligible, shared by all three
    channels -- see app/knowledge/index.py), not as a separate step here,
    so no channel can ever bypass it: there is no code path in this class
    that reads a knowledge_chunks row without going through the index's
    own filtering.
    """

    def __init__(self, index: PersistentHybridIndex) -> None:
        self.index = index

    def retrieve(
        self,
        request: RetrievalRequest,
        *,
        top_k: int = 5,
        fusion_mode: FusionMode = FusionMode.RRF,
        query_expansion_enabled: bool = False,
        reranker_mode: RerankerMode = RerankerMode.NONE,
        mmr_enabled: bool = False,
        mmr_lambda: float = 0.7,
        observer: Optional[EventObserver] = None,
    ) -> ControlledRetrievalResult:
        """Phase 3 feature flags (query_expansion_enabled/reranker_mode/
        mmr_enabled) all default to their Phase-2 behavior (off/NONE/off)
        -- per "Không bật mặc định nếu benchmark không cải thiện", see
        docs/RAG_ABLATION_REPORT.md for whether enabling them actually
        helps on this repo's corpus before any caller turns them on by
        default."""
        start = time.monotonic()
        run_id = f"RUN-{uuid.uuid4().hex[:12]}"

        policy = AGENT_RETRIEVAL_POLICIES.get(request.agent_type)
        if policy is None:
            return ControlledRetrievalResult(
                diagnostics=RetrievalDiagnostics(
                    status=RetrievalStatus.ERROR,
                    error_code=RetrievalErrorCode.FILTER_CONFIGURATION_INVALID,
                    strategy=fusion_mode.value,
                    channels_executed=[],
                    candidate_count_before_filter=0,
                    candidate_count_after_filter=0,
                    latency_ms=int((time.monotonic() - start) * 1000),
                ),
                grounding_pack=None,
            )

        as_of = request.effective_at.date()
        branch = request.branch_id or "*"
        common = dict(
            branch=branch,
            product_ids=request.product_ids or None,
            customer_id=request.customer_id,
            case_id=request.case_id,
            actor_role=request.actor_role,
            minimum_authority_tier=policy.minimum_authority_tier,
            minimum_verification_status=policy.minimum_verification_status,
            allowed_security_classifications=request.allowed_security_classifications,
            as_of=as_of,
        )

        total_before, eligible_after, blocked_reasons = self.index.eligibility_diagnostics(**common)

        exact_hits: List[RetrievalHit] = []
        channels_executed: List[RetrievalChannel] = []
        if policy.exact_lookup_first:
            channels_executed.append(RetrievalChannel.EXACT)
            for ref in request.exact_entity_refs:
                if ref.entity_type == "chunk_id":
                    chunk = self.index.exact_lookup_by_chunk_id(ref.entity_id)
                    if chunk is not None:
                        exact_hits.append(RetrievalHit(chunk=chunk, score=1.0, dense_score=0.0, sparse_score=0.0))
            for product_id in request.product_ids:
                chunks = self.index.exact_lookup_by_product_id(
                    product_id, as_of=as_of, branch=branch,
                    customer_id=request.customer_id, case_id=request.case_id, actor_role=request.actor_role,
                    minimum_authority_tier=policy.minimum_authority_tier,
                    minimum_verification_status=policy.minimum_verification_status,
                    allowed_security_classifications=request.allowed_security_classifications,
                )
                exact_hits.extend(
                    RetrievalHit(chunk=c, score=1.0, dense_score=0.0, sparse_score=0.0) for c in chunks
                )

        sparse_hits: List[RetrievalHit] = []
        dense_hits: List[RetrievalHit] = []
        if request.normalized_query.strip():
            # Query expansion only widens the SEARCH text (more matchable
            # tokens for BM25/dense) -- request.normalized_query itself is
            # left untouched, so GroundingItem/citation content always
            # traces back to what the user actually asked, never to a
            # synonym-injected version of it.
            search_query = expanded_query_text(request.normalized_query) if query_expansion_enabled else request.normalized_query
            sparse_hits = self.index.sparse_search_bm25(
                search_query, top_k=policy.maximum_candidates, **common
            )
            channels_executed.append(RetrievalChannel.SPARSE)
            dense_hits = self.index.dense_search(
                search_query, top_k=policy.maximum_candidates, **common
            )
            channels_executed.append(RetrievalChannel.DENSE)

        if fusion_mode == FusionMode.RRF:
            fusion = ReciprocalRankFusion(sparse_weight=policy.sparse_weight, dense_weight=policy.dense_weight)
        else:
            fusion = LinearSumFusion()
        fused: List[FusedCandidate] = fusion.fuse(sparse_hits, dense_hits, top_k=policy.maximum_candidates)
        if sparse_hits or dense_hits:
            channels_executed.append(RetrievalChannel.HYBRID)

        # NOT deriving MMR protected_chunk_ids from detect_slot_conflicts()
        # here -- found via real E2E testing (a "UBO" query against the
        # actual Legal corpus) that conflict_detection's (product_id,
        # section_path) identity key false-positives badly on this repo's
        # real data: several genuinely distinct rules cite the same
        # document chapter (e.g. three different PROD-WORKING-CAPITAL
        # rules all have source_location="Chương 5", see
        # data/synthetic/v2/eligibility_rules.json), so 5 of 9 real Legal
        # chunks get flagged as "conflicting" with each other. Wiring that
        # into MMR's protected set caused those 5 false positives to crowd
        # out the single genuinely relevant, non-conflicting result (the
        # UBO rule) from the top-5 entirely -- a materially worse outcome
        # than not protecting anything. Conflicts are still computed and
        # attached to the final GroundingPack.conflicts below (§ Conflict
        # Detection remains correct/informational there, and
        # claim_evidence_validator still marks any cited conflicting chunk
        # CONFLICTED) -- only the MMR-protection use of conflicts was
        # removed. See docs/RAG_GUARDRAIL_IMPLEMENTATION_REPORT.md Phase 3
        # "Known bug found via testing" for the full writeup.
        protected_chunk_ids: set[str] = set()

        # reranked_list (when the heuristic reranker runs) carries the REAL
        # rerank_score per candidate. MMR below must reuse it rather than
        # recomputing a trivial wrapper from the original fused_score --
        # doing so was a real bug found via manual E2E verification against
        # the "UBO" query: it silently discarded the reranker's reordering
        # because two candidates' *original* RRF scores were nearly
        # identical even though their rerank_scores were not, so MMR (which
        # only sees relative scores, not chunk_id identity) picked based on
        # the wrong signal and the correct UBO rule dropped out of top-5.
        reranked_list: Optional[List[RerankedCandidate]] = None
        if reranker_mode == RerankerMode.HEURISTIC:
            query_tokens = set(request.normalized_query.lower().split())
            reranked_list = HeuristicReranker().rerank(
                query_tokens=query_tokens, candidates=fused, top_n=policy.maximum_candidates,
                customer_id=request.customer_id, case_id=request.case_id, as_of=as_of,
            )
            fused = [r.fused for r in reranked_list]
        elif reranker_mode in (RerankerMode.CROSS_ENCODER, RerankerMode.LLM_RERANKER_EXPERIMENTAL):
            raise NotImplementedError(
                f"{reranker_mode.value} is NOT_IMPLEMENTED in this repo -- no cross-encoder "
                "dependency or LLM call site is wired into retrieval; use RerankerMode.HEURISTIC."
            )

        if mmr_enabled:
            if reranked_list is not None:
                as_reranked = reranked_list
            else:
                as_reranked = [RerankedCandidate(fused=c, rerank_score=c.fused_score, features={}) for c in fused]
            mmr_result = mmr_select(
                as_reranked, top_k=policy.maximum_candidates, lambda_relevance=mmr_lambda,
                protected_chunk_ids=protected_chunk_ids,
            )
            fused = [r.fused for r in mmr_result]

        seen: set[str] = set()
        ordered: List[tuple[KnowledgeChunk, RetrievalChannel, float]] = []
        for hit in exact_hits:
            if hit.chunk.chunk_id not in seen:
                seen.add(hit.chunk.chunk_id)
                ordered.append((hit.chunk, RetrievalChannel.EXACT, 1.0))
        for candidate in fused:
            if candidate.chunk.chunk_id in seen:
                continue
            seen.add(candidate.chunk.chunk_id)
            if candidate.sparse_rank and candidate.dense_rank:
                channel = RetrievalChannel.HYBRID
            elif candidate.sparse_rank:
                channel = RetrievalChannel.SPARSE
            else:
                channel = RetrievalChannel.DENSE
            ordered.append((candidate.chunk, channel, candidate.fused_score))

        selected = ordered[:top_k]

        conflicts = detect_slot_conflicts([chunk for chunk, _channel, _score in selected])

        namespace = self.index.namespace()
        items: List[GroundingItem] = []
        for i, (chunk, channel, score) in enumerate(selected):
            locator = SourceLocator(type=SourceLocatorType.DOCUMENT_SPAN, section=chunk.section_path)
            items.append(
                GroundingItem(
                    grounding_item_id=f"GI-{run_id}-{i}",
                    chunk_id=chunk.chunk_id,
                    source_id=chunk.document_id,
                    source_version=chunk.document_version,
                    content=chunk.text,
                    authority_tier=chunk.authority_tier,
                    verification_status=chunk.verification_status,
                    retrieval_channel=channel,
                    fused_score=score,
                    source_locator=locator,
                )
            )

        request_ref = MetadataRef(entity_type="retrieval_request", entity_id=request.request_id)
        pack_payload = "|".join(item.chunk_id + item.source_version for item in items)
        content_hash = hashlib.sha256(pack_payload.encode("utf-8")).hexdigest()
        grounding_pack = RetrievalGroundingPack(
            grounding_pack_id=f"GP-{run_id}",
            retrieval_run_id=run_id,
            agent_type=request.agent_type,
            request_ref=request_ref,
            items=items,
            conflicts=conflicts,
            content_hash=content_hash,
            created_at=datetime.now(timezone.utc),
        )

        status = RetrievalStatus.OK
        error_code: Optional[RetrievalErrorCode] = None
        if not selected:
            if policy.fail_closed:
                status = RetrievalStatus.ERROR
                error_code = RetrievalErrorCode.SOURCE_SCOPE_EMPTY
            else:
                error_code = RetrievalErrorCode.NO_RELEVANT_RESULT

        diagnostics = RetrievalDiagnostics(
            status=status,
            error_code=error_code,
            strategy=fusion_mode.value,
            channels_executed=channels_executed,
            candidate_count_before_filter=total_before,
            candidate_count_after_filter=eligible_after,
            filters_applied={
                "branch": branch, "customer_id": request.customer_id, "case_id": request.case_id,
                "minimum_authority_tier": policy.minimum_authority_tier.value,
                "minimum_verification_status": policy.minimum_verification_status.value,
            },
            blocked_candidate_reason_counts=blocked_reasons,
            index_version=namespace.corpus_version,
            representation_types=[namespace.representation_type.value],
            latency_ms=int((time.monotonic() - start) * 1000),
        )

        result = ControlledRetrievalResult(
            diagnostics=diagnostics,
            grounding_pack=grounding_pack if (status == RetrievalStatus.OK and selected) else None,
        )

        if observer is not None:
            observer(
                RetrievalEvent(
                    event_type="retrieval_completed", trace_id=request.trace_id, request_id=request.request_id,
                    retrieval_run_id=run_id, agent_type=request.agent_type.value, strategy=fusion_mode.value,
                    candidate_count_before_filter=total_before, candidate_count_after_filter=eligible_after,
                    blocked_reason_counts=blocked_reasons,
                    grounding_pack_id=result.grounding_pack.grounding_pack_id if result.grounding_pack else None,
                    selected_chunk_ids=[chunk.chunk_id for chunk, _c, _s in selected],
                    latency_ms=diagnostics.latency_ms,
                    error_code=error_code.value if error_code else None,
                )
            )

        return result
