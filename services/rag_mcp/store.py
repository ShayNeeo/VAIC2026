"""Persistent SQLite repository owned exclusively by the RAG MCP service."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


SCHEMA_VERSION = 2


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


class RagStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10, factory=_ClosingConnection)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    sensitivity TEXT NOT NULL,
                    owner_json TEXT NOT NULL,
                    dataset_version TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    active INTEGER NOT NULL,
                    indexed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL REFERENCES sources(source_id),
                    domain TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    document_version TEXT NOT NULL,
                    product_id TEXT,
                    section_path TEXT NOT NULL,
                    chunk_type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    effective_from TEXT NOT NULL,
                    effective_to TEXT,
                    active INTEGER NOT NULL,
                    segments_json TEXT NOT NULL,
                    branches_json TEXT NOT NULL,
                    sensitivity TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    source_tier TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    vector_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    indexed_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_chunks_domain ON chunks(domain);
                CREATE INDEX IF NOT EXISTS idx_chunks_product ON chunks(product_id);
                CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id, document_version);
                CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id);
                CREATE TABLE IF NOT EXISTS retrieval_audit (
                    event_id TEXT PRIMARY KEY,
                    at TEXT NOT NULL,
                    trace_id TEXT NOT NULL,
                    caller_hash TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    query_hash TEXT,
                    domain TEXT,
                    filters_json TEXT NOT NULL,
                    result_count INTEGER NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    error_code TEXT,
                    agent_type TEXT NOT NULL DEFAULT 'unknown',
                    policy_decision TEXT NOT NULL DEFAULT 'legacy'
                );
                CREATE INDEX IF NOT EXISTS idx_retrieval_audit_trace ON retrieval_audit(trace_id, at);
                CREATE TABLE IF NOT EXISTS ingestion_runs (
                    run_id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    corpus_version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    rejected_chunk_count INTEGER NOT NULL,
                    quality_json TEXT NOT NULL,
                    error_message TEXT
                );
                """
            )
            columns = {
                str(row[1])
                for row in connection.execute("PRAGMA table_info(retrieval_audit)").fetchall()
            }
            if "agent_type" not in columns:
                connection.execute(
                    "ALTER TABLE retrieval_audit ADD COLUMN agent_type TEXT NOT NULL DEFAULT 'unknown'"
                )
            if "policy_decision" not in columns:
                connection.execute(
                    "ALTER TABLE retrieval_audit ADD COLUMN policy_decision TEXT NOT NULL DEFAULT 'legacy'"
                )
            connection.execute(
                "INSERT INTO schema_meta(key, value) VALUES ('schema_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(SCHEMA_VERSION),),
            )

    @staticmethod
    def _upsert_source_on_connection(
        connection: sqlite3.Connection,
        source: Dict[str, Any],
        rows: List[Dict[str, Any]],
        now: str,
    ) -> int:
        connection.execute(
            """INSERT INTO sources(
                   source_id,name,domain,tier,sensitivity,owner_json,dataset_version,
                   source_hash,active,indexed_at
               ) VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(source_id) DO UPDATE SET
                   name=excluded.name,domain=excluded.domain,tier=excluded.tier,
                   sensitivity=excluded.sensitivity,owner_json=excluded.owner_json,
                   dataset_version=excluded.dataset_version,source_hash=excluded.source_hash,
                   active=excluded.active,indexed_at=excluded.indexed_at""",
            (
                source["source_id"], source["name"], source["domain"], source["tier"],
                source["sensitivity"], json.dumps(source["owner"], ensure_ascii=False, sort_keys=True),
                source["dataset_version"], source["source_hash"], int(source.get("active", True)), now,
            ),
        )
        chunk_ids: List[str] = []
        for chunk in rows:
            chunk_ids.append(chunk["chunk_id"])
            connection.execute(
                """INSERT INTO chunks(
                       chunk_id,source_id,domain,document_id,document_version,product_id,
                       section_path,chunk_type,text,effective_from,effective_to,active,
                       segments_json,branches_json,sensitivity,owner,source_tier,
                       content_hash,vector_json,metadata_json,indexed_at
                   ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(chunk_id) DO UPDATE SET
                       source_id=excluded.source_id,domain=excluded.domain,
                       document_id=excluded.document_id,document_version=excluded.document_version,
                       product_id=excluded.product_id,section_path=excluded.section_path,
                       chunk_type=excluded.chunk_type,text=excluded.text,
                       effective_from=excluded.effective_from,effective_to=excluded.effective_to,
                       active=excluded.active,segments_json=excluded.segments_json,
                       branches_json=excluded.branches_json,sensitivity=excluded.sensitivity,
                       owner=excluded.owner,source_tier=excluded.source_tier,
                       content_hash=excluded.content_hash,vector_json=excluded.vector_json,
                       metadata_json=excluded.metadata_json,indexed_at=excluded.indexed_at""",
                (
                    chunk["chunk_id"], chunk["source_id"], chunk["domain"], chunk["document_id"],
                    chunk["document_version"], chunk.get("product_id"), chunk["section_path"],
                    chunk["chunk_type"], chunk["text"], str(chunk["effective_from"]),
                    str(chunk["effective_to"]) if chunk.get("effective_to") else None,
                    int(chunk.get("active", True)), json.dumps(chunk.get("segments", [])),
                    json.dumps(chunk.get("branches", [])), chunk["sensitivity"], chunk["owner"],
                    chunk["source_tier"], chunk["content_hash"], json.dumps(chunk["vector"]),
                    json.dumps(chunk.get("metadata", {}), ensure_ascii=False, sort_keys=True), now,
                ),
            )
        if chunk_ids:
            placeholders = ",".join("?" for _ in chunk_ids)
            connection.execute(
                f"DELETE FROM chunks WHERE source_id=? AND chunk_id NOT IN ({placeholders})",
                [source["source_id"], *chunk_ids],
            )
        else:
            connection.execute("DELETE FROM chunks WHERE source_id=?", (source["source_id"],))
        return len(rows)

    def upsert_source(self, source: Dict[str, Any], chunks: Iterable[Dict[str, Any]]) -> int:
        rows = list(chunks)
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            return self._upsert_source_on_connection(connection, source, rows, now)

    def replace_corpus(
        self,
        packages: Iterable[tuple[Dict[str, Any], List[Dict[str, Any]]]],
        *,
        run_id: str,
        corpus_version: str,
        quality: Dict[str, Any],
        started_at: str,
    ) -> None:
        """Atomically publish a fully validated corpus; old serving data survives any failure."""

        staged = list(packages)
        now = datetime.now(timezone.utc).isoformat()
        source_ids = [source["source_id"] for source, _ in staged]
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            for source, chunks in staged:
                self._upsert_source_on_connection(connection, source, chunks, now)
            if source_ids:
                placeholders = ",".join("?" for _ in source_ids)
                connection.execute(
                    f"DELETE FROM chunks WHERE source_id NOT IN ({placeholders})", source_ids
                )
                connection.execute(
                    f"DELETE FROM sources WHERE source_id NOT IN ({placeholders})", source_ids
                )
            connection.execute(
                """INSERT INTO ingestion_runs(
                       run_id,started_at,completed_at,corpus_version,status,source_count,
                       chunk_count,rejected_chunk_count,quality_json,error_message
                   ) VALUES (?,?,?,?,?,?,?,?,?,NULL)""",
                (
                    run_id, started_at, now, corpus_version, "passed", len(staged),
                    sum(len(chunks) for _, chunks in staged), 0,
                    json.dumps(quality, ensure_ascii=False, sort_keys=True),
                ),
            )
            for key, value in {
                "corpus_version": corpus_version,
                "last_ingestion_run_id": run_id,
                "last_ingestion_status": "passed",
            }.items():
                connection.execute(
                    "INSERT INTO schema_meta(key,value) VALUES (?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, value),
                )

    def record_ingestion_failure(
        self,
        *,
        run_id: str,
        corpus_version: str,
        started_at: str,
        quality: Dict[str, Any],
        error_message: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO ingestion_runs(
                       run_id,started_at,completed_at,corpus_version,status,source_count,
                       chunk_count,rejected_chunk_count,quality_json,error_message
                   ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    run_id, started_at, now, corpus_version, "failed", 0, 0, 0,
                    json.dumps(quality, ensure_ascii=False, sort_keys=True), error_message[:1000],
                ),
            )
            connection.execute(
                "INSERT INTO schema_meta(key,value) VALUES ('last_ingestion_run_id',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (run_id,),
            )
            connection.execute(
                "INSERT INTO schema_meta(key,value) VALUES ('last_ingestion_status','failed') "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value"
            )

    def last_ingestion(self) -> Dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM ingestion_runs ORDER BY completed_at DESC LIMIT 1"
            ).fetchone()
        return dict(row) if row else {}

    def schema_value(self, key: str, default: str = "") -> str:
        with self._connect() as connection:
            row = connection.execute("SELECT value FROM schema_meta WHERE key=?", (key,)).fetchone()
        return str(row[0]) if row else default

    def candidate_rows(
        self,
        *,
        domain: str,
        product_ids: Sequence[str],
        document_ids: Sequence[str],
        document_version: Optional[str],
    ) -> List[Dict[str, Any]]:
        clauses = ["c.active=1", "s.active=1"]
        values: List[Any] = []
        if domain != "all":
            clauses.append("c.domain=?")
            values.append(domain)
        if product_ids:
            placeholders = ",".join("?" for _ in product_ids)
            clauses.append(f"(c.product_id IS NULL OR c.product_id IN ({placeholders}))")
            values.extend(product_ids)
        if document_ids:
            placeholders = ",".join("?" for _ in document_ids)
            clauses.append(f"c.document_id IN ({placeholders})")
            values.extend(document_ids)
        if document_version:
            clauses.append("c.document_version=?")
            values.append(document_version)
        sql = (
            "SELECT c.* FROM chunks c JOIN sources s ON s.source_id=c.source_id WHERE "
            + " AND ".join(clauses)
        )
        with self._connect() as connection:
            return [dict(row) for row in connection.execute(sql, values).fetchall()]

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT c.* FROM chunks c JOIN sources s ON s.source_id=c.source_id "
                "WHERE c.chunk_id=? AND c.active=1 AND s.active=1",
                (chunk_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_sources(self, domain: str = "all") -> List[Dict[str, Any]]:
        values: List[Any] = []
        where = "WHERE s.active=1"
        if domain != "all":
            where += " AND s.domain=?"
            values.append(domain)
        sql = f"""SELECT s.*, COUNT(c.chunk_id) AS chunk_count
                  FROM sources s LEFT JOIN chunks c ON c.source_id=s.source_id AND c.active=1
                  {where} GROUP BY s.source_id ORDER BY s.domain, s.source_id"""
        with self._connect() as connection:
            return [dict(row) for row in connection.execute(sql, values).fetchall()]

    def counts(self) -> tuple[int, int, Dict[str, int]]:
        with self._connect() as connection:
            source_count = int(connection.execute("SELECT COUNT(*) FROM sources WHERE active=1").fetchone()[0])
            chunk_count = int(connection.execute("SELECT COUNT(*) FROM chunks WHERE active=1").fetchone()[0])
            rows = connection.execute(
                "SELECT domain, COUNT(*) AS count FROM chunks WHERE active=1 GROUP BY domain"
            ).fetchall()
        return source_count, chunk_count, {str(row["domain"]): int(row["count"]) for row in rows}

    def quick_check(self) -> str:
        with self._connect() as connection:
            return str(connection.execute("PRAGMA quick_check").fetchone()[0])

    def append_audit(
        self,
        *,
        trace_id: str,
        employee_id: str,
        tool_name: str,
        query: Optional[str],
        domain: Optional[str],
        filters: Dict[str, Any],
        result_count: int,
        latency_ms: int,
        status: str,
        agent_type: str,
        policy_decision: str,
        error_code: Optional[str] = None,
    ) -> str:
        event_id = f"RAG-AUD-{uuid.uuid4().hex.upper()}"
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest() if query else None
        caller_hash = hashlib.sha256(employee_id.encode("utf-8")).hexdigest()[:20]
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO retrieval_audit(
                       event_id,at,trace_id,caller_hash,tool_name,query_hash,domain,
                       filters_json,result_count,latency_ms,status,error_code,agent_type,policy_decision
                   ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    event_id, datetime.now(timezone.utc).isoformat(), trace_id, caller_hash,
                    tool_name, query_hash, domain,
                    json.dumps(filters, ensure_ascii=False, sort_keys=True, default=str),
                    result_count, latency_ms, status, error_code, agent_type, policy_decision,
                ),
            )
        return event_id

    def audit_events(self, trace_id: str) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM retrieval_audit WHERE trace_id=? ORDER BY at", (trace_id,)
                ).fetchall()
            ]
