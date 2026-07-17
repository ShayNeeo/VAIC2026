"""Hybrid RAG Retriever for Product Catalog — port from app/rag/product_retriever.py with upgrades."""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set

try:
    from underthesea import word_tokenize
    UNDERTHESEA_AVAILABLE = True
except ImportError:
    UNDERTHESEA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from mcp_common.config import settings


STOPWORDS = {"la", "là", "và", "của", "cho", "có", "từ", "nào", "những", "một"}


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


class ProductRetriever:
    """Normalize → hybrid retrieve (dense+sparse) → heuristic rerank → threshold → citations."""

    def __init__(
        self,
        catalog: Optional[Mapping[str, Mapping[str, Any]]] = None,
        *,
        threshold: float = None,
        dense_weight: float = None,
        sparse_weight: float = None,
    ):
        from app.tools.product_tools import SHB_PRODUCT_CATALOG
        self.catalog = catalog or SHB_PRODUCT_CATALOG
        self.threshold = threshold or settings.RAG_THRESHOLD
        self.dense_weight = dense_weight or settings.RAG_DENSE_WEIGHT
        self.sparse_weight = sparse_weight or settings.RAG_SPARSE_WEIGHT

        # Build documents
        self._documents = {pid: self._document(pid, prod) for pid, prod in self.catalog.items()}

        # Embeddings
        if settings.USE_REAL_EMBEDDING and SENTENCE_TRANSFORMERS_AVAILABLE:
            self._embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
            self._use_real_embedding = True
        else:
            self._embedder = None
            self._use_real_embedding = False

        self._vectors = {pid: self._embed(text) for pid, text in self._documents.items()}

    def search(self, query: str, *, top_k: int = None) -> List[ProductRetrievalResult]:
        top_k = top_k or settings.RAG_TOP_K
        normalized = self.normalize_query(query)
        query_tokens = self._tokens(normalized)

        if not query_tokens:
            return []

        query_vector = self._embed(normalized)

        # Dense scores
        dense_scores = {
            pid: self._cosine(query_vector, vec) for pid, vec in self._vectors.items()
        }

        # Sparse scores (BM25-style token overlap)
        sparse_scores = {
            pid: self._overlap(query_tokens, self._tokens(text))
            for pid, text in self._documents.items()
        }

        # OOS gate: if sparse max < 0.40, return empty (RAG_VSF behavior)
        if max(sparse_scores.values(), default=0.0) < 0.40:
            return []

        max_dense = max(dense_scores.values(), default=0.0)
        max_sparse = max(sparse_scores.values(), default=0.0)

        results: List[ProductRetrievalResult] = []
        for pid, prod in self.catalog.items():
            d_score = dense_scores[pid] / max_dense if max_dense else 0.0
            s_score = sparse_scores[pid] / max_sparse if max_sparse else 0.0

            # Hybrid fusion
            score = self.dense_weight * d_score + self.sparse_weight * s_score

            # Heuristic rerank (RAG_VSF style)
            score += min(0.15, 0.15 * sparse_scores[pid])

            # Exact keyword boosts
            if query_tokens & self._tokens(str(prod.get("name", ""))):
                score += 0.05

            # Legal article boost
            if any(tok in query_tokens for tok in ("điều", "chương", "khoản")):
                if any(tok in self._tokens(self._documents[pid]) for tok in ("điều", "chương", "khoản")):
                    score += 0.15

            # Table/FAQ boost
            if "bảng" in query_tokens or "faq" in query_tokens:
                if "bảng" in self._tokens(self._documents[pid]) or "faq" in self._tokens(self._documents[pid]):
                    score += 0.10

            # OCR low confidence penalty (not applicable for synthetic catalog)
            # Cap rerank bonus at 0.25
            rerank_bonus = score - (self.dense_weight * d_score + self.sparse_weight * s_score)
            if rerank_bonus > 0.25:
                score = self.dense_weight * d_score + self.sparse_weight * s_score + 0.25

            if score >= self.threshold:
                results.append(
                    ProductRetrievalResult(
                        product_id=pid,
                        score=round(min(score, 1.0), 6),
                        text=self._documents[pid],
                        source_doc=prod["source_metadata"]["document"],
                        section=prod["source_metadata"]["section"],
                        metadata={
                            "retrieval": {
                                "dense_score": round(d_score, 6),
                                "sparse_score": round(s_score, 6),
                            },
                            "effective_date": prod["source_metadata"].get("effective_date"),
                        },
                    )
                )

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
        for idx, res in enumerate(results, 1):
            section = f"[Source {idx}] {res.source_doc} — {res.section}\n{res.text}\nScore: {res.score:.4f}"
            if sections and used + len(section) > max_chars:
                break
            sections.append(section[:max_chars] if not sections else section)
            sources.append(res.citation())
            used += len(section)
        return {"context": "\n\n---\n\n".join(sections), "sources": sources, "grounded": bool(sections)}

    @staticmethod
    def normalize_query(query: str) -> str:
        text = unicodedata.normalize("NFC", query or "").strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"([!?]){2,}$", r"\1", text)
        return text.rstrip(".,;:")

    def _normalize(self, text: str) -> str:
        return self.normalize_query(text).lower()

    def _tokens(self, text: str) -> Set[str]:
        normalized = self._normalize(text)
        if UNDERTHESEA_AVAILABLE:
            try:
                tokens = word_tokenize(normalized, format="text").split()
            except Exception:
                tokens = re.findall(r"[\wÀ-ỹ]+", normalized)
        else:
            tokens = re.findall(r"[\wÀ-ỹ]+", normalized)
        return {
            self._fold(tok)
            for tok in tokens
            if len(tok) > 1 and self._fold(tok) not in {self._fold(w) for w in STOPWORDS}
        }

    @staticmethod
    def _fold(text: str) -> str:
        decomposed = unicodedata.normalize("NFD", text.lower())
        return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn").replace("đ", "d")

    @staticmethod
    def _overlap(left: Set[str], right: Set[str]) -> float:
        return len(left & right) / len(left) if left else 0.0

    def _document(self, pid: str, prod: Mapping[str, Any]) -> str:
        return " ".join([
            pid,
            str(prod.get("name", "")),
            str(prod.get("description", "")),
            str(prod.get("eligibility_rules", "")),
            " ".join(prod.get("benefits", [])),
            " ".join(prod.get("required_documents", [])),
        ])

    def _embed(self, text: str) -> List[float]:
        if self._use_real_embedding and self._embedder:
            vec = self._embedder.encode(f"passage: {text}", normalize_embeddings=True)
            return vec.tolist()

        # Hash embedding fallback (deterministic, no model needed)
        dim = settings.EMBEDDING_DIM
        vector = [0.0] * dim
        for token in self._tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % dim
            vector[index] += 1.0 if digest[4] % 2 == 0 else -1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    @staticmethod
    def _cosine(left: List[float], right: List[float]) -> float:
        return max(0.0, sum(a * b for a, b in zip(left, right)))