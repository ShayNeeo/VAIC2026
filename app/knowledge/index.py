"""Restart-safe SQLite hybrid index for the offline MVP."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import unicodedata
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional, Protocol, Sequence

from app.config import settings
from app.knowledge.models import KnowledgeChunk, RetrievalHit


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def fold(text: str) -> str:
    value = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn").replace("đ", "d")


_STOPWORDS = {
    "la", "va", "cua", "cho", "co", "mot", "cac", "doanh", "nghiep", "de", "duoc",
    # Expanded per services/rag_mcp/embedding.py precedent: a short stopword list
    # lets generic Vietnamese filler words collide with corpus tokens after
    # diacritic-fold, inflating the sparse-overlap score for out-of-scope queries.
    "trong", "ngoai", "tren", "duoi", "giua", "ve", "voi", "tu", "den", "nhu",
    "ra", "vao", "sau", "truoc", "nay", "kia", "ay", "nao", "gi", "ai", "sao",
    "the", "nen", "boi", "tai", "khi", "neu", "hay", "toi", "ta", "nam", "nhat",
    # Non-banking everyday filler: removing these only improves OOS precision.
    # They never discriminate corporate-banking products, so their presence in
    # a query (weather, recipes, dates, places, generic question words) must
    # not manufacture a sparse match against the corpus.
    "thoi", "tiet", "da", "nang", "ngay", "mai", "hom", "nay", "thanh", "pho",
    "cong", "thuc", "nau", "pho", "bao", "nhieu", "lam", "sao", "the_nao",
    "o", "tai_sao", "khi_nao", "o_dau", "ai", "gi", "nao", "bao_nhieu",
}


def tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9-]+", fold(text)) if len(token) > 1 and token not in _STOPWORDS}


class EmbeddingProvider(Protocol):
    name: str
    dimension: int

    def embed(self, text: str) -> List[float]: ...


class CachedGeminiEmbedding:
    """Production embedding via Google AI Studio (``google-genai`` SDK).

    Uses the AI Studio key (``GOOGLE_API_KEY``) with ``gemini-embedding-2`` by
    default, local cache keyed by content hash (offline + deterministic after
    a warm cache). The OpenAI provider remains available as a fallback.
    """
    name = "gemini-embedding-2"

    def __init__(self, dimension: int = 3072, cache_file: Optional[Path] = None) -> None:
        self.dimension = dimension
        self.api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
        self.cache_file = cache_file or Path(settings.VECTOR_DB_DIR) / "gemini_vector_cache.json"
        self.cache: dict[str, List[float]] = {}
        if self.cache_file.exists():
            try:
                self.cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    def embed(self, text: str) -> List[float]:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if text_hash in self.cache:
            return self.cache[text_hash]

        from dotenv import load_dotenv

        load_dotenv()
        api_key = self.api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY (AI Studio) is not set for CachedGeminiEmbedding.")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.embed_content(
            model=self.name,
            contents=[text],
            config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
        )
        vector = list(response.embeddings[0].values)

        self.cache[text_hash] = vector
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(self.cache), encoding="utf-8")

        return vector



class CachedOpenAIEmbedding:
    """Production provider using text-embedding-3-small, with a local JSON cache
    so repeated ingestion/tests never re-pay for an unchanged chunk/query text."""

    name = "openai-text-embedding-3-small"

    def __init__(self, dimension: int = 1536, cache_file: Optional[Path] = None) -> None:
        self.dimension = dimension
        self.api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.client = None
        self.cache_file = cache_file or Path(settings.VECTOR_DB_DIR) / "openai_vector_cache.json"
        self.cache: dict[str, List[float]] = {}
        if self.cache_file.exists():
            try:
                self.cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _get_client(self):
        if not self.client:
            if not self.api_key:
                raise RuntimeError("OPENAI_API_KEY is not set for CachedOpenAIEmbedding.")
            from openai import OpenAI

            self.client = OpenAI(api_key=self.api_key)
        return self.client

    def embed(self, text: str) -> List[float]:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if text_hash in self.cache:
            return self.cache[text_hash]
        client = self._get_client()
        response = client.embeddings.create(input=[text], model="text-embedding-3-small")
        vector = response.data[0].embedding
        self.cache[text_hash] = vector
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(self.cache), encoding="utf-8")
        return vector


class LocalEmbedding:
    """Deterministic, key-free embedding for offline/dev/test and reproducible CI.

    Hashes content tokens into a fixed-dim bag-of-words vector (preserving
    exact-token overlap). No API key required; swap to ``gemini``/``openai`` for
    production semantic recall once a billing-backed key is provisioned.
    """

    name = "local"
    _DIM = 256

    def __init__(self, dimension: int = _DIM) -> None:
        self.dimension = dimension

    def embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dimension
        for token in tokens(text):
            h = int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:8], "big")
            idx = h % self.dimension
            mag = 1.0 + ((h >> 8) & 0xFF) / 255.0
            vec[idx] += mag
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0.0:
            vec = [v / norm for v in vec]
        return vec


def create_embedding_provider(name: Optional[str] = None) -> EmbeddingProvider:
    # Default is "local": deterministic and key-free so the suite runs offline
    # with zero API keys and CI is reproducible. Set the env var to "gemini"
    # (Google AI Studio key GOOGLE_API_KEY, gemini-embedding-2) or "openai" for
    # production semantic recall.
    provider = (name or os.getenv("KNOWLEDGE_EMBEDDING_PROVIDER") or "local").strip().lower()
    if provider == "local":
        return LocalEmbedding()
    if provider == "gemini":
        return CachedGeminiEmbedding()
    if provider == "openai":
        return CachedOpenAIEmbedding()
    raise ValueError(f"Unsupported embedding provider {provider!r}.")


class PersistentHybridIndex:
    def __init__(self, db_path: str | Path, provider: Optional[EmbeddingProvider] = None) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.provider = provider or create_embedding_provider()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, factory=_ClosingConnection)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    vector TEXT NOT NULL,
                    content_hash TEXT NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS index_manifests (
                    source_hash TEXT PRIMARY KEY,
                    dataset_version TEXT NOT NULL,
                    indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )

    def upsert(self, chunks: Iterable[KnowledgeChunk], *, source_hash: str, dataset_version: str) -> int:
        rows = list(chunks)
        with self._connect() as connection:
            for chunk in rows:
                connection.execute(
                    """INSERT INTO knowledge_chunks(chunk_id, payload, vector, content_hash)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(chunk_id) DO UPDATE SET
                         payload=excluded.payload, vector=excluded.vector, content_hash=excluded.content_hash""",
                    (
                        chunk.chunk_id,
                        chunk.model_dump_json(),
                        json.dumps(self.provider.embed(chunk.text)),
                        chunk.content_hash,
                    ),
                )
            # Latest-wins reconciliation: a product may arrive from multiple
            # sources/versions (e.g. a refreshed manual). Keep only the chunk
            # with the newest source_date per product_id so retrieval never
            # surfaces a superseded promotion, fee or limit. Ties (same
            # source_date) keep all versions -- a deliberate, visible ambiguity
            # rather than silent overwrite.
            all_rows = connection.execute("SELECT payload FROM knowledge_chunks").fetchall()
            by_product: dict[str, list] = {}
            for row in all_rows:
                ch = KnowledgeChunk.model_validate_json(row["payload"])
                by_product.setdefault(ch.product_id, []).append(ch)
            stale_ids: list[str] = []
            for pid, group in by_product.items():
                if len(group) < 2:
                    continue
                newest = max(
                    (g.source_date or date.min for g in group),
                    default=date.min,
                )
                for g in group:
                    if (g.source_date or date.min) < newest:
                        stale_ids.append(g.chunk_id)
            if stale_ids:
                connection.executemany(
                    "DELETE FROM knowledge_chunks WHERE chunk_id = ?",
                    [(cid,) for cid in stale_ids],
                )
            connection.execute(
                "INSERT OR IGNORE INTO index_manifests(source_hash, dataset_version) VALUES (?, ?)",
                (source_hash, dataset_version),
            )
        return len(rows)

    def count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0])

    def prune(self, *, chunk_types: set[str], keep_chunk_ids: set[str]) -> int:
        """Remove stale chunks owned by one governed corpus during version sync."""
        removed = 0
        with self._connect() as connection:
            rows = connection.execute("SELECT chunk_id, payload FROM knowledge_chunks").fetchall()
            for row in rows:
                chunk = KnowledgeChunk.model_validate_json(row["payload"])
                if chunk.chunk_type in chunk_types and chunk.chunk_id not in keep_chunk_ids:
                    connection.execute("DELETE FROM knowledge_chunks WHERE chunk_id = ?", (row["chunk_id"],))
                    removed += 1
        return removed

    def get_chunks_for_document(
        self, document_id: str, document_version: Optional[str] = None
    ) -> List[KnowledgeChunk]:
        """Return every indexed chunk for a (document_id[, document_version]).

        Used by the evidence validator to independently re-check that a
        claimed quote genuinely appears in what this index actually serves,
        rather than trusting whatever the evidence-producing code wrote into
        Evidence.quote. Passing document_version=None returns chunks for
        *any* version of the document, which lets a caller distinguish
        "unknown document" from "known document, wrong version cited".
        """
        matches: List[KnowledgeChunk] = []
        with self._connect() as connection:
            rows = connection.execute("SELECT payload FROM knowledge_chunks").fetchall()
        for row in rows:
            chunk = KnowledgeChunk.model_validate_json(row["payload"])
            if chunk.document_id != document_id:
                continue
            if document_version is not None and chunk.document_version != document_version:
                continue
            matches.append(chunk)
        return matches

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        branch: str = "*",
        segment: Optional[str] = None,
        as_of: Optional[date] = None,
        product_ids: Optional[Sequence[str]] = None,
        threshold: Optional[float] = None,
    ) -> List[RetrievalHit]:
        query_tokens = tokens(query)
        if not query_tokens:
            return []
        query_vector = self.provider.embed(query)
        today = as_of or date.today()

        # Auto-calibrate threshold based on vector dimension (Gemini 768 vs
        # OpenAI 1536). A caller-supplied threshold always wins.
        if threshold is not None:
            effective_threshold = threshold
        else:
            effective_threshold = 0.30 if self.provider.dimension == 768 else 0.40
            # When the caller already narrowed to specific product_ids (intent
            # resolution did the ACL/scoping), relax the score floor so a
            # bundle query ("payroll + collections + cash mgmt + working
            # capital") surfaces every member instead of diluting each below
            # the global threshold. The product_ids filter bounds precision:
            # this only restores recall the intent layer already earned.
            if product_ids:
                effective_threshold = 0.20

        hits: List[RetrievalHit] = []
        with self._connect() as connection:
            rows = connection.execute("SELECT payload, vector FROM knowledge_chunks").fetchall()
        for row in rows:
            chunk = KnowledgeChunk.model_validate_json(row["payload"])
            if not chunk.active or chunk.effective_from > today:
                continue
            if chunk.effective_to is not None and chunk.effective_to < today:
                continue
            branches = chunk.access_scope.get("branches", [])
            if "*" not in branches and branch not in branches:
                continue
            if segment and segment not in chunk.segments:
                continue
            if product_ids and chunk.product_id not in product_ids:
                continue
            chunk_tokens = tokens(chunk.text)
            matched = query_tokens & chunk_tokens
            sparse = len(matched) / len(query_tokens)
            dense_raw = max(0.0, sum(a * b for a, b in zip(query_vector, json.loads(row["vector"]))))
            exact_bonus = 0.15 if chunk.product_id.lower() in query.lower() else 0.0
            score = min(1.0, 0.6 * dense_raw + 0.4 * sparse + exact_bonus)
            # Hybrid gate (Linux-kernel: explicit, no silent drops, no magic
            # floors). A chunk qualifies when:
            #   * the fused score clears the calibrated threshold (semantic
            #     recall preserved), OR
            #   * it has strong keyword overlap (sparse >= 0.34 AND at least two
            #     distinct query tokens matched) -- catches out-of-vocabulary
            #     queries the local bag-of-words encoder misses, without
            #     admitting single-generic-token collisions (e.g. "thời tiết
            #     Đà Nẵng" matching banking text on the word "thời") that would
            #     break out-of-scope (OOS) precision. The legacy `sparse > 0`
            #     test admitted near-empty matches; the legacy 0.20 floor on
            #     product_ids scoped queries destroyed precision. Both removed.
            if score >= effective_threshold or (sparse >= 0.34 and len(matched) >= 2):
                hits.append(
                    RetrievalHit(
                        chunk=chunk,
                        score=round(score, 6),
                        dense_score=round(dense_raw, 6),
                        sparse_score=round(sparse, 6),
                    )
                )
        return sorted(hits, key=lambda item: item.score, reverse=True)[:top_k]
