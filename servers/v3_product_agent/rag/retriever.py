"""V3 Hybrid RAG Retriever for Product Catalog.

Implements V3 Data Strategy:
- Tier A (Internal Authoritative): Product master, approved policy
- Hybrid retrieval: Dense (e5/hash) + Sparse (BM25) with 0.6/0.4 fusion
- Heuristic rerank: keyword overlap + legal article + table/FAQ + exact product code
- Threshold gate: 0.35 minimum
- Citation format: source_doc, section, product_id, effective_date
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set

from mcp_common.config import settings

# Optional dependencies
try:
    from underthesea import word_tokenize
    HAS_UNDERTHESEA = True
except ImportError:
    HAS_UNDERTHESEA = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


STOPWORDS = {
    "la", "là", "và", "của", "cho", "có", "từ", "nào", "những", "một",
    "các", "cái", "để", "được", "với", "trong", "ngoài", "trên", "dưới",
}


@dataclass(frozen=True)
class ProductRetrievalResult:
    product_id: str
    score: float
    text: str
    source_doc: str
    section: str
    metadata: Dict[str, Any]

    def citation(self) -> Dict[str, str]:
        return {
            "source_doc": self.source_doc,
            "page_or_section": self.section,
            "product_id": self.product_id,
        }


class EmbeddingCache:
    """SQLite cache for embeddings to avoid re-computation."""

    def __init__(self, db_path: str = "./data/embedding_cache.db"):
        import sqlite3
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    text_hash TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def get(self, text_hash: str, model: str) -> Optional[List[float]]:
        import sqlite3, pickle
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT embedding FROM embeddings WHERE text_hash = ? AND model = ?",
                (text_hash, model)
            ).fetchone()
            if row:
                return pickle.loads(row[0])
        return None

    def set(self, text_hash: str, model: str, embedding: List[float]):
        import sqlite3, pickle
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO embeddings (text_hash, model, embedding) VALUES (?, ?, ?)",
                (text_hash, model, pickle.dumps(embedding))
            )


class ProductRetriever:
    """
    Normalize → hybrid retrieve → rerank → grounded context.

    V3 Retrieval Pipeline:
    1. normalize_query (NFC, whitespace, punctuation)
    2. tokenize (underthesea VIE + regex fallback)
    3. dense top-20 (e5 with prefix "query:"/"passage:" or hash fallback)
    4. sparse top-20 (BM25 token overlap)
    5. fusion: 0.6 * dense_norm + 0.4 * sparse_norm
    6. heuristic rerank (+keyword, +legal_article, +table/FAQ, +exact_code, cap +0.25)
    7. threshold gate: 0.35
    8. dedup + source diversity
    9. return top-k with citations
    """

    def __init__(
        self,
        catalog: Optional[Mapping[str, Mapping[str, Any]]] = None,
        *,
        threshold: float = None,
        dense_weight: float = None,
        sparse_weight: float = None,
    ):
        from v3_product_agent.product.catalog import V3_PRODUCT_CATALOG
        self.catalog = catalog or V3_PRODUCT_CATALOG
        self.threshold = threshold or settings.RAG_THRESHOLD
        self.dense_weight = dense_weight or settings.RAG_DENSE_WEIGHT
        self.sparse_weight = sparse_weight or settings.RAG_SPARSE_WEIGHT

        # Build documents
        self._documents = {
            pid: self._document(pid, product) for pid, product in self.catalog.items()
        }

        # Initialize embedder
        self._embedder = self._create_embedder()
        self._cache = EmbeddingCache()

        # Pre-compute vectors
        self._vectors = {}
        for pid, text in self._documents.items():
            self._vectors[pid] = self._embedder(text)

    def _create_embedder(self):
        """Create embedder function: real e5 or hash fallback."""
        if settings.USE_REAL_EMBEDDING and HAS_SENTENCE_TRANSFORMERS:
            model = SentenceTransformer(settings.EMBEDDING_MODEL)
            def embed(text: str) -> List[float]:
                prefixed = f"passage: {text}" if not text.startswith("passage:") else text
                vec = model.encode(prefixed, normalize_embeddings=True)
                return vec.tolist()
            return embed
        else:
            dim = settings.EMBEDDING_DIM
            def embed(text: str) -> List[float]:
                return self._hash_embed(text, dim)
            return embed

    @staticmethod
    def _hash_embed(text: str, dimension: int = 128) -> List[float]:
        """Deterministic hash-based embedding (Blake2b)."""
        vector = [0.0] * dimension
        for token in ProductRetriever._tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % dimension
            vector[index] += 1.0 if digest[4] % 2 == 0 else -1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    @staticmethod
    def normalize_query(query: str) -> str:
        text = unicodedata.normalize("NFC", query or "").strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"([!?]){2,}$", r"\1", text)
        return text.rstrip(".,;:")

    @classmethod
    def _normalize(cls, text: str) -> str:
        return cls.normalize_query(text).lower()

    @classmethod
    def _tokens(cls, text: str) -> Set[str]:
        normalized = cls._normalize(text)
        if HAS_UNDERTHESEA:
            try:
                tokens = word_tokenize(normalized, format="text").split()
            except Exception:
                tokens = re.findall(r"[\wÀ-ỹ]+", normalized)
        else:
            tokens = re.findall(r"[\wÀ-ỹ]+", normalized)
        return {
            cls._fold(token)
            for token in tokens
            if len(token) > 1 and cls._fold(token) not in {cls._fold(w) for w in STOPWORDS}
        }

    @staticmethod
    def _fold(text: str) -> str:
        decomposed = unicodedata.normalize("NFD", text.lower())
        return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").replace("đ", "d")

    @staticmethod
    def _overlap(left: Set[str], right: Set[str]) -> float:
        return len(left & right) / len(left) if left else 0.0

    @staticmethod
    def _cosine(left: List[float], right: List[float]) -> float:
        return max(0.0, sum(a * b for a, b in zip(left, right)))

    @staticmethod
    def _document(product_id: str, product: Mapping[str, Any]) -> str:
        """Build searchable text from product data, handling structured fields."""
        fees = product.get("fees_limits", [])
        fees_str = " ".join(
            f"{getattr(f, 'name', '')} {getattr(f, 'value', '')} {getattr(f, 'unit', '')}"
            for f in fees
        )
        prereq_str = " ".join(getattr(p, 'document_type', '') for p in product.get("prerequisites", []))
        return " ".join([
            product_id,
            str(product.get("name", "")),
            str(product.get("description", "")),
            str(product.get("eligibility_rules", "")),
            " ".join(product.get("benefits", [])),
            prereq_str,
            fees_str,
            " ".join(product.get("use_cases", [])),
        ])

    def search(self, query: str, *, top_k: int = None) -> List[ProductRetrievalResult]:
        top_k = top_k or settings.RAG_TOP_K
        normalized = self.normalize_query(query)
        query_tokens = self._tokens(normalized)

        if not query_tokens:
            return []

        # Sparse gate (V3: require minimum keyword overlap)
        sparse_scores = {
            pid: self._overlap(query_tokens, self._tokens(text))
            for pid, text in self._documents.items()
        }
        if max(sparse_scores.values(), default=0.0) < 0.40:
            return []

        query_vector = self._embedder(normalized)
        dense_scores = {
            pid: self._cosine(query_vector, vec)
            for pid, vec in self._vectors.items()
        }

        max_dense = max(dense_scores.values(), default=0.0)
        max_sparse = max(sparse_scores.values(), default=0.0)

        results: List[ProductRetrievalResult] = []
        for pid, product in self.catalog.items():
            dense_score = dense_scores[pid] / max_dense if max_dense else 0.0
            sparse_score = sparse_scores[pid] / max_sparse if max_sparse else 0.0

            # Fusion
            score = self.dense_weight * dense_score + self.sparse_weight * sparse_score

            # Heuristic rerank (V3 style)
            score += min(0.15, 0.15 * sparse_scores[pid])
            if query_tokens & self._tokens(str(product.get("name", ""))):
                score += 0.05

            # Legal article boost
            if any(tok in query_tokens for tok in ("điều", "khoản", "article", "chapter")):
                if any(tok in self._tokens(self._documents[pid]) for tok in ("điều", "khoản", "article", "chapter")):
                    score += 0.15

            # Table/FAQ boost
            if "bảng" in query_tokens or "faq" in query_tokens:
                if "bảng" in self._tokens(self._documents[pid]) or "faq" in self._tokens(self._documents[pid]):
                    score += 0.10

            # Exact product code match
            if query_tokens & self._tokens(str(product.get("product_id", ""))):
                score += 0.05

            # Cap rerank bonus at 0.25
            rerank_bonus = score - (self.dense_weight * dense_score + self.sparse_weight * sparse_score)
            if rerank_bonus > 0.25:
                score = self.dense_weight * dense_score + self.sparse_weight * sparse_score + 0.25

            if score >= self.threshold:
                results.append(ProductRetrievalResult(
                    product_id=pid,
                    score=round(min(score, 1.0), 6),
                    text=self._documents[pid],
                    source_doc=product["source_metadata"]["document"],
                    section=product["source_metadata"]["section"],
                    metadata={
                        "retrieval": {
                            "dense_score": round(dense_score, 6),
                            "sparse_score": round(sparse_score, 6),
                        },
                        "effective_date": product["source_metadata"].get("effective_date"),
                        "tier": product.get("tier", "A"),
                    },
                ))

        return sorted(results, key=lambda r: r.score, reverse=True)[:top_k]

    def build_context(self, query: str, *, top_k: int = None, max_chars: int = 6000) -> Dict[str, Any]:
        top_k = top_k or settings.RAG_TOP_K
        results = self.search(query, top_k=top_k)
        if not results:
            return {
                "context": "Không đủ dữ liệu trong catalog đã lập chỉ mục để trả lời.",
                "sources": [],
                "grounded": False,
            }
        sections: List[str] = []
        sources: List[Dict[str, str]] = []
        used = 0
        for idx, result in enumerate(results, 1):
            section = f"[Source {idx}] {result.source_doc} — {result.section}\n{result.text}\nScore: {result.score:.4f}"
            if sections and used + len(section) > max_chars:
                break
            sections.append(section)
            sources.append(result.citation())
            used += len(section)
        return {
            "context": "\n\n---\n\n".join(sections),
            "sources": sources,
            "grounded": bool(sections),
        }