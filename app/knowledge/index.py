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
}


def tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9-]+", fold(text)) if len(token) > 1 and token not in _STOPWORDS}


class EmbeddingProvider(Protocol):
    name: str
    dimension: int

    def embed(self, text: str) -> List[float]: ...


class CachedGeminiEmbedding:
    """Production provider using gemini-embedding-001, with local cache for offline tests.

    "text-embedding-004" (the model this class originally called) has been
    retired: calling it now returns 404 NOT_FOUND. Verified against the live
    API on 2026-07-18: `GET v1beta/models` lists gemini-embedding-001,
    gemini-embedding-2-preview and gemini-embedding-2 as the models this key
    can actually call. gemini-embedding-001 defaults to a 3072-dim output;
    outputDimensionality truncates it (Matryoshka-style) to match the
    dimension declared here so cosine() in this module never silently
    compares mismatched-length vectors.
    """
    name = "gemini-embedding-001"

    def __init__(self, dimension: int = 768, cache_file: Optional[Path] = None) -> None:
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

        import urllib.error
        import urllib.request
        import json as json_lib

        api_key = self.api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set for CachedGeminiEmbedding.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.name}:embedContent?key={api_key}"
        data = json_lib.dumps({
            "model": f"models/{self.name}",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": self.dimension,
        }).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req) as response:
                resp_body = response.read().decode('utf-8')
                result = json_lib.loads(resp_body)
                vector = result["embedding"]["values"]
        except urllib.error.HTTPError as e:
            # Surface Google's actual error body (e.g. "RESOURCE_EXHAUSTED:
            # prepayment credits depleted") instead of a bare "HTTP Error nnn"
            # -- that body is what actually explains failures like billing.
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini Embedding API call failed ({e.code}): {body}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to call Gemini Embedding API: {e}") from e

        self.cache[text_hash] = vector
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json_lib.dumps(self.cache), encoding="utf-8")

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


def create_embedding_provider(name: Optional[str] = None) -> EmbeddingProvider:
    # Default is "openai", not "gemini": verified live on 2026-07-18 that the
    # configured GOOGLE_API_KEY's Gemini project has its prepayment credits
    # depleted (429 RESOURCE_EXHAUSTED on every embedContent call), so Gemini
    # cannot actually serve requests right now even though the model name/
    # request shape are now fixed. Set KNOWLEDGE_EMBEDDING_PROVIDER=gemini
    # once billing is restored to switch back.
    provider = (name or os.getenv("KNOWLEDGE_EMBEDDING_PROVIDER") or "openai").strip().lower()
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
            connection.execute(
                "INSERT OR IGNORE INTO index_manifests(source_hash, dataset_version) VALUES (?, ?)",
                (source_hash, dataset_version),
            )
        return len(rows)

    def count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0])

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
        
        # Auto-calibrate threshold based on vector dimension (Gemini 768 vs OpenAI 1536)
        if threshold is not None:
            actual_threshold = threshold
        else:
            actual_threshold = 0.30 if self.provider.dimension == 768 else 0.40

        effective_threshold = min(actual_threshold, 0.20) if product_ids else actual_threshold
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
            sparse = len(query_tokens & chunk_tokens) / len(query_tokens)
            dense_raw = max(0.0, sum(a * b for a, b in zip(query_vector, json.loads(row["vector"]))))
            exact_bonus = 0.15 if chunk.product_id.lower() in query.lower() else 0.0
            score = min(1.0, 0.6 * dense_raw + 0.4 * sparse + exact_bonus)
            if sparse > 0 and score >= effective_threshold:
                hits.append(
                    RetrievalHit(
                        chunk=chunk,
                        score=round(score, 6),
                        dense_score=round(dense_raw, 6),
                        sparse_score=round(sparse, 6),
                    )
                )
        return sorted(hits, key=lambda item: item.score, reverse=True)[:top_k]
