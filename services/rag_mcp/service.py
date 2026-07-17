"""Least-privilege authorization, hybrid retrieval, citation checks and sanitized audit."""

from __future__ import annotations

import json
import uuid
from datetime import date
from time import perf_counter
from typing import Any, Dict, Iterable, List, Optional

from services.rag_mcp.config import RagMCPSettings, settings as default_settings
from services.rag_mcp.embedding import EmbeddingProvider, cosine, create_embedding_provider, tokens
from services.rag_mcp.ingestion import BuiltinCorpusIngestor
from services.rag_mcp.schemas import (
    CallerPrincipal,
    ChunkCitation,
    CitationVerificationRequest,
    CitationVerificationResponse,
    ExpertListSourcesRequest,
    ExpertSearchRequest,
    GetChunkRequest,
    GetChunkResponse,
    HealthResponse,
    IngestSummary,
    KnowledgeSource,
    ListSourcesRequest,
    ListSourcesResponse,
    RetrievedChunk,
    SearchFilters,
    SearchKnowledgeRequest,
    SearchKnowledgeResponse,
)
from services.rag_mcp.store import RagStore, SCHEMA_VERSION
from services.rag_mcp.tool_policy import POLICY_VERSION, PROFILE_ENDPOINTS, TOOL_RULES, authorize_tool


UNSAFE_QUERY_MARKERS = (
    "ignore previous instructions",
    "bỏ qua chỉ dẫn trước",
    "reveal system prompt",
    "bypass approval",
    "call crm tool",
)


class RagServiceError(RuntimeError):
    code = "RAG_SERVICE_ERROR"


class AccessDenied(RagServiceError):
    code = "RAG_ACCESS_DENIED"


class ToolAccessDenied(AccessDenied):
    code = "RAG_TOOL_ACCESS_DENIED"


class UnsafeQuery(RagServiceError):
    code = "RAG_UNSAFE_QUERY"


class ChunkNotFound(RagServiceError):
    code = "RAG_CHUNK_NOT_FOUND"


class RagKnowledgeService:
    def __init__(
        self,
        *,
        settings: RagMCPSettings = default_settings,
        store: Optional[RagStore] = None,
        embedding: Optional[EmbeddingProvider] = None,
    ) -> None:
        self.settings = settings
        self.settings.validate_runtime()
        self.store = store or RagStore(settings.db_path)
        self.embedding = embedding or create_embedding_provider(settings.embedding_provider)
        self.ingestor = BuiltinCorpusIngestor(self.store, self.embedding)
        self._seed_checked = False

    def ensure_seeded(self) -> IngestSummary:
        source_count, chunk_count, by_domain = self.store.counts()
        if (self.settings.auto_seed and not self._seed_checked) or source_count == 0 or chunk_count == 0:
            summary = self.ingestor.seed()
            self._seed_checked = True
            return summary
        last = self.store.last_ingestion()
        quality = json.loads(last.get("quality_json", "{}")) if last else {}
        return IngestSummary(
            run_id=str(last.get("run_id", "RAG-ING-UNKNOWN")),
            status="passed",
            corpus_version=self.store.schema_value("corpus_version", "unknown"),
            source_count=source_count,
            chunk_count=chunk_count,
            chunks_by_domain=by_domain,
            source_hashes={},
            quality_checks=quality,
            rejected_chunk_count=int(last.get("rejected_chunk_count", 0)) if last else 0,
            warnings=[],
        )

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return max(0, round((perf_counter() - started) * 1000))

    @staticmethod
    def _authorize_tool(principal: CallerPrincipal, tool_name: str, domain: str) -> None:
        try:
            rule = authorize_tool(principal, tool_name)
        except PermissionError as exc:
            raise ToolAccessDenied(str(exc)) from exc
        if rule.domain != "all" and rule.domain != domain:
            raise ToolAccessDenied(
                f"tool {tool_name} is fixed to {rule.domain}, requested domain={domain}"
            )

    @staticmethod
    def _screen_query(query: str) -> None:
        lowered = query.lower()
        if any(marker in lowered for marker in UNSAFE_QUERY_MARKERS):
            raise UnsafeQuery("query was rejected by prompt-injection guardrail")

    @staticmethod
    def _row_allowed(
        row: Dict[str, Any], principal: CallerPrincipal, as_of: date, requested_segments: Iterable[str]
    ) -> bool:
        if date.fromisoformat(str(row["effective_from"])) > as_of:
            return False
        if row.get("effective_to") and date.fromisoformat(str(row["effective_to"])) < as_of:
            return False
        branches = set(json.loads(row["branches_json"]))
        is_steward = "DataSteward" in principal.roles or "KnowledgeAdmin" in principal.roles
        if not is_steward and "*" not in branches and principal.branch not in branches:
            return False
        requested = set(requested_segments)
        chunk_segments = set(json.loads(row["segments_json"]))
        if requested and chunk_segments and not requested.intersection(chunk_segments):
            return False
        return True

    @staticmethod
    def _filters_for_log(request: SearchKnowledgeRequest) -> Dict[str, Any]:
        return {
            "domain": request.filters.domain,
            "product_ids": request.filters.product_ids,
            "document_ids": request.filters.document_ids,
            "segments": request.filters.segments,
            "chunk_types": request.filters.chunk_types,
            "document_version": request.filters.document_version,
            "as_of": str(request.filters.as_of or date.today()),
            "branch": request.principal.branch,
            "top_k": request.top_k,
            "min_score": request.min_score,
        }

    @staticmethod
    def _audit_agent(principal: CallerPrincipal) -> str:
        return principal.agent_type

    def _to_chunk(
        self,
        row: Dict[str, Any],
        *,
        score: float,
        dense_score: float,
        sparse_score: float,
    ) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id=row["chunk_id"],
            domain=row["domain"],
            chunk_type=row["chunk_type"],
            text=row["text"],
            product_id=row.get("product_id"),
            score=round(min(1.0, max(0.0, score)), 6),
            dense_score=round(min(1.0, max(0.0, dense_score)), 6),
            sparse_score=round(min(1.0, max(0.0, sparse_score)), 6),
            effective_from=date.fromisoformat(str(row["effective_from"])),
            effective_to=date.fromisoformat(str(row["effective_to"])) if row.get("effective_to") else None,
            segments=list(json.loads(row["segments_json"])),
            citation=ChunkCitation(
                document_id=row["document_id"],
                document_version=row["document_version"],
                section_path=row["section_path"],
                source_id=row["source_id"],
                content_hash=row["content_hash"],
            ),
            metadata=dict(json.loads(row["metadata_json"])),
        )

    @staticmethod
    def _pack_context(chunks: List[RetrievedChunk], max_chars: int) -> str:
        sections: List[str] = []
        used = 0
        for item in chunks:
            section = (
                f"[CHUNK {item.chunk_id}]\n"
                f"Domain: {item.domain}; Product: {item.product_id or '-'}\n"
                f"Source: {item.citation.document_id} v{item.citation.document_version} — "
                f"{item.citation.section_path}\n"
                f"Content: {item.text}\n"
                f"Retrieval score: {item.score:.4f}"
            )
            if sections and used + len(section) > max_chars:
                break
            sections.append(section)
            used += len(section)
        return "\n\n---\n\n".join(sections)

    def expert_search(
        self, request: ExpertSearchRequest, *, tool_name: str, domain: str
    ) -> SearchKnowledgeResponse:
        admin_contract = SearchKnowledgeRequest(
            query=request.query,
            principal=request.principal,
            filters=SearchFilters(
                domain=domain,
                product_ids=request.filters.product_ids,
                document_ids=request.filters.document_ids,
                segments=request.filters.segments,
                chunk_types=request.filters.chunk_types,
                document_version=request.filters.document_version,
                as_of=request.filters.as_of,
            ),
            top_k=request.top_k,
            min_score=request.min_score,
            max_context_chars=request.max_context_chars,
            trace_id=request.trace_id,
        )
        return self.search(admin_contract, tool_name=tool_name)

    def search(
        self, request: SearchKnowledgeRequest, *, tool_name: str = "rag_search"
    ) -> SearchKnowledgeResponse:
        started = perf_counter()
        filters_log = self._filters_for_log(request)
        try:
            self._authorize_tool(request.principal, tool_name, request.filters.domain)
            self._screen_query(request.query)
            self.ensure_seeded()
            as_of = request.filters.as_of or date.today()
            query_tokens = tokens(request.query)
            query_vector = self.embedding.embed(request.query)
            rows = self.store.candidate_rows(
                domain=request.filters.domain,
                product_ids=request.filters.product_ids,
                document_ids=request.filters.document_ids,
                document_version=request.filters.document_version,
            )
            ranked: List[RetrievedChunk] = []
            requested_types = set(request.filters.chunk_types)
            for row in rows:
                if requested_types and row["chunk_type"] not in requested_types:
                    continue
                if not self._row_allowed(row, request.principal, as_of, request.filters.segments):
                    continue
                chunk_tokens = tokens(row["text"])
                sparse = len(query_tokens.intersection(chunk_tokens)) / len(query_tokens) if query_tokens else 0.0
                dense = cosine(query_vector, list(json.loads(row["vector_json"])))
                exact_product = bool(row.get("product_id") and row["product_id"].lower() in request.query.lower())
                score = min(1.0, 0.6 * dense + 0.4 * sparse + (0.15 if exact_product else 0.0))
                if sparse >= 0.2 and score >= request.min_score:
                    ranked.append(self._to_chunk(row, score=score, dense_score=dense, sparse_score=sparse))
            chunks = sorted(ranked, key=lambda item: item.score, reverse=True)[: request.top_k]
            latency = self._elapsed_ms(started)
            audit_id = self.store.append_audit(
                trace_id=request.trace_id,
                employee_id=request.principal.employee_id,
                tool_name=tool_name,
                query=request.query,
                domain=request.filters.domain,
                filters=filters_log,
                result_count=len(chunks),
                latency_ms=latency,
                status="success",
                agent_type=self._audit_agent(request.principal),
                policy_decision="allow",
            )
            return SearchKnowledgeResponse(
                query_id=f"RAG-Q-{uuid.uuid4().hex.upper()}",
                trace_id=request.trace_id,
                grounded=bool(chunks),
                retrieval_mode="hybrid_dense_sparse_metadata_filter",
                embedding_provider=self.embedding.name,
                filters_applied=filters_log,
                chunks=chunks,
                context_text=self._pack_context(chunks, request.max_context_chars),
                latency_ms=latency,
                audit_event_id=audit_id,
                safety={
                    "acl_filtered": True,
                    "effective_date_filtered": True,
                    "agent_tool_policy_enforced": True,
                    "raw_query_logged": False,
                },
            )
        except RagServiceError as exc:
            self.store.append_audit(
                trace_id=request.trace_id,
                employee_id=request.principal.employee_id,
                tool_name=tool_name,
                query=request.query,
                domain=request.filters.domain,
                filters=filters_log,
                result_count=0,
                latency_ms=self._elapsed_ms(started),
                status="denied",
                agent_type=self._audit_agent(request.principal),
                policy_decision="deny",
                error_code=exc.code,
            )
            raise

    def get_chunk(
        self,
        request: GetChunkRequest,
        *,
        tool_name: str = "rag_get_chunk",
        expected_domain: str | None = None,
    ) -> GetChunkResponse:
        started = perf_counter()
        row = self.store.get_chunk(request.chunk_id)
        domain = str(row["domain"]) if row else (expected_domain or "all")
        try:
            self._authorize_tool(request.principal, tool_name, expected_domain or domain)
            if expected_domain and row and row["domain"] != expected_domain:
                raise ChunkNotFound("chunk does not exist or is outside tool domain")
            if row is None or not self._row_allowed(row, request.principal, request.as_of or date.today(), []):
                raise ChunkNotFound("chunk does not exist or is outside caller scope")
            chunk = self._to_chunk(row, score=1.0, dense_score=1.0, sparse_score=1.0)
            latency = self._elapsed_ms(started)
            audit_id = self.store.append_audit(
                trace_id=request.trace_id,
                employee_id=request.principal.employee_id,
                tool_name=tool_name,
                query=None,
                domain=domain,
                filters={"chunk_id": request.chunk_id, "branch": request.principal.branch},
                result_count=1,
                latency_ms=latency,
                status="success",
                agent_type=self._audit_agent(request.principal),
                policy_decision="allow",
            )
            return GetChunkResponse(trace_id=request.trace_id, chunk=chunk, audit_event_id=audit_id)
        except RagServiceError as exc:
            self.store.append_audit(
                trace_id=request.trace_id,
                employee_id=request.principal.employee_id,
                tool_name=tool_name,
                query=None,
                domain=domain,
                filters={"chunk_id": request.chunk_id, "branch": request.principal.branch},
                result_count=0,
                latency_ms=self._elapsed_ms(started),
                status="denied",
                agent_type=self._audit_agent(request.principal),
                policy_decision="deny",
                error_code=exc.code,
            )
            raise

    def expert_list_sources(
        self, request: ExpertListSourcesRequest, *, tool_name: str, domain: str
    ) -> ListSourcesResponse:
        return self.list_sources(
            ListSourcesRequest(principal=request.principal, domain=domain, trace_id=request.trace_id),
            tool_name=tool_name,
        )

    def list_sources(
        self, request: ListSourcesRequest, *, tool_name: str = "rag_list_sources"
    ) -> ListSourcesResponse:
        started = perf_counter()
        try:
            self._authorize_tool(request.principal, tool_name, request.domain)
            self.ensure_seeded()
            sources = [
                KnowledgeSource(
                    source_id=row["source_id"],
                    name=row["name"],
                    domain=row["domain"],
                    tier=row["tier"],
                    sensitivity=row["sensitivity"],
                    owner=json.loads(row["owner_json"]),
                    dataset_version=row["dataset_version"],
                    source_hash=row["source_hash"],
                    active=bool(row["active"]),
                    chunk_count=int(row["chunk_count"]),
                    indexed_at=row["indexed_at"],
                )
                for row in self.store.list_sources(request.domain)
            ]
            audit_id = self.store.append_audit(
                trace_id=request.trace_id,
                employee_id=request.principal.employee_id,
                tool_name=tool_name,
                query=None,
                domain=request.domain,
                filters={"domain": request.domain},
                result_count=len(sources),
                latency_ms=self._elapsed_ms(started),
                status="success",
                agent_type=self._audit_agent(request.principal),
                policy_decision="allow",
            )
            return ListSourcesResponse(trace_id=request.trace_id, sources=sources, audit_event_id=audit_id)
        except RagServiceError as exc:
            self.store.append_audit(
                trace_id=request.trace_id,
                employee_id=request.principal.employee_id,
                tool_name=tool_name,
                query=None,
                domain=request.domain,
                filters={"domain": request.domain},
                result_count=0,
                latency_ms=self._elapsed_ms(started),
                status="denied",
                agent_type=self._audit_agent(request.principal),
                policy_decision="deny",
                error_code=exc.code,
            )
            raise

    def verify_citation(self, request: CitationVerificationRequest) -> CitationVerificationResponse:
        started = perf_counter()
        tool_name = "evidence_verify_citation"
        row = self.store.get_chunk(request.chunk_id)
        domain = str(row["domain"]) if row else "all"
        try:
            self._authorize_tool(request.principal, tool_name, "all")
            if row is None or not self._row_allowed(row, request.principal, date.today(), []):
                raise ChunkNotFound("citation chunk does not exist or is outside caller scope")
            citation = ChunkCitation(
                document_id=row["document_id"],
                document_version=row["document_version"],
                section_path=row["section_path"],
                source_id=row["source_id"],
                content_hash=row["content_hash"],
            )
            mismatches: List[str] = []
            if request.expected_content_hash != citation.content_hash:
                mismatches.append("content_hash")
            if request.expected_document_id and request.expected_document_id != citation.document_id:
                mismatches.append("document_id")
            if request.expected_document_version and request.expected_document_version != citation.document_version:
                mismatches.append("document_version")
            audit_id = self.store.append_audit(
                trace_id=request.trace_id,
                employee_id=request.principal.employee_id,
                tool_name=tool_name,
                query=None,
                domain=domain,
                filters={"chunk_id": request.chunk_id, "fields_checked": 3},
                result_count=1,
                latency_ms=self._elapsed_ms(started),
                status="success",
                agent_type=self._audit_agent(request.principal),
                policy_decision="allow",
            )
            return CitationVerificationResponse(
                trace_id=request.trace_id,
                valid=not mismatches,
                chunk_id=request.chunk_id,
                actual_citation=citation,
                mismatches=mismatches,
                audit_event_id=audit_id,
            )
        except RagServiceError as exc:
            self.store.append_audit(
                trace_id=request.trace_id,
                employee_id=request.principal.employee_id,
                tool_name=tool_name,
                query=None,
                domain=domain,
                filters={"chunk_id": request.chunk_id},
                result_count=0,
                latency_ms=self._elapsed_ms(started),
                status="denied",
                agent_type=self._audit_agent(request.principal),
                policy_decision="deny",
                error_code=exc.code,
            )
            raise

    def health(self) -> HealthResponse:
        self.ensure_seeded()
        source_count, chunk_count, by_domain = self.store.counts()
        quick_check = self.store.quick_check()
        last = self.store.last_ingestion()
        return HealthResponse(
            status="ok" if quick_check == "ok" and chunk_count > 0 and last.get("status") == "passed" else "degraded",
            service="shb-rag-mcp",
            version="2.0.0",
            protocol="MCP Streamable HTTP (official Python SDK 1.x)",
            schema_version=SCHEMA_VERSION,
            embedding_provider=self.embedding.name,
            source_count=source_count,
            chunk_count=chunk_count,
            chunks_by_domain=by_domain,
            db_quick_check=quick_check,
            auth_required=self.settings.require_auth,
            data_mode="SHB_ENTERPRISE_DATA",
            corpus_version=self.store.schema_value("corpus_version", "unknown"),
            last_ingestion_status=str(last.get("status", "missing")),
            last_ingestion_run_id=last.get("run_id"),
            tool_policy_version=POLICY_VERSION,
            agent_profiles=sorted(PROFILE_ENDPOINTS),
        )
