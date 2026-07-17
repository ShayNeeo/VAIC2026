"""Small local-first hybrid RAG pipeline for the synthetic product catalog.

Inspired by RAG_VSF's separation of query normalization, retrieval, fusion,
reranking and context building. It intentionally has no network/model call:
the deterministic hash embedding is a safe fallback until a real embedding
provider and persistent index are configured.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

from app.tools.product_tools import SHB_PRODUCT_CATALOG


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


class ProductRAGService:
    """Normalize → hybrid retrieve → rerank → grounded context."""

    def __init__(self, catalog: Optional[Mapping[str, Mapping[str, Any]]] = None, *, threshold: float = 0.35):
        self.catalog = catalog or SHB_PRODUCT_CATALOG
        self.threshold = threshold
        self._documents = {product_id: self._document(product_id, product) for product_id, product in self.catalog.items()}
        self._vectors = {product_id: self._embed(text) for product_id, text in self._documents.items()}

    def search(self, query: str, *, top_k: int = 5) -> List[ProductRetrievalResult]:
        normalized = self.normalize_query(query)
        query_tokens = self._tokens(normalized)
        if not query_tokens:
            return []
        query_vector = self._embed(normalized)
        dense = {product_id: self._cosine(query_vector, vector) for product_id, vector in self._vectors.items()}
        sparse = {product_id: self._overlap(query_tokens, self._tokens(text)) for product_id, text in self._documents.items()}
        # Dense/hash similarity alone is not evidence for a domain answer.
        if max(sparse.values(), default=0.0) < 0.40:
            return []
        max_dense = max(dense.values(), default=0.0)
        max_sparse = max(sparse.values(), default=0.0)
        results: List[ProductRetrievalResult] = []
        for product_id, product in self.catalog.items():
            dense_score = dense[product_id] / max_dense if max_dense else 0.0
            sparse_score = sparse[product_id] / max_sparse if max_sparse else 0.0
            score = 0.6 * dense_score + 0.4 * sparse_score
            score += min(0.15, 0.15 * sparse[product_id])
            # RAG_VSF-style exact keyword reranking; preserve source metadata.
            if query_tokens & self._tokens(str(product.get("name", ""))):
                score += 0.05
            if score >= self.threshold:
                results.append(
                    ProductRetrievalResult(
                        product_id=product_id,
                        score=round(min(score, 1.0), 6),
                        text=self._documents[product_id],
                        source_doc=product["source_metadata"]["document"],
                        section=product["source_metadata"]["section"],
                        metadata={
                            "retrieval": {"dense_score": round(dense_score, 6), "sparse_score": round(sparse_score, 6)},
                            "effective_date": product["source_metadata"].get("effective_date"),
                        },
                    )
                )
        return sorted(results, key=lambda result: result.score, reverse=True)[:top_k]

    def build_context(self, query: str, *, top_k: int = 5, max_chars: int = 6000) -> Dict[str, Any]:
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
        for index, result in enumerate(results, start=1):
            section = f"[Source {index}] {result.source_doc} — {result.section}\n{result.text}\nScore: {result.score:.4f}"
            if sections and used + len(section) > max_chars:
                break
            sections.append(section[:max_chars] if not sections else section)
            sources.append(result.citation())
            used += len(section)
        return {"context": "\n\n---\n\n".join(sections), "sources": sources, "grounded": bool(sections)}

    @staticmethod
    def normalize_query(query: str) -> str:
        text = unicodedata.normalize("NFC", query or "").strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"([!?]){2,}$", r"\1", text)
        return text.rstrip(".,;:")

    @staticmethod
    def _normalize(text: str) -> str:
        return ProductRAGService.normalize_query(text).lower()

    @classmethod
    def _tokens(cls, text: str) -> set[str]:
        return {
            cls._fold(token)
            for token in re.findall(r"[\wÀ-ỹ]+", cls._normalize(text))
            if len(token) > 1 and cls._fold(token) not in {cls._fold(word) for word in STOPWORDS}
        }

    @staticmethod
    def _fold(text: str) -> str:
        decomposed = unicodedata.normalize("NFD", text.lower())
        return "".join(char for char in decomposed if unicodedata.category(char) != "Mn").replace("đ", "d")

    @staticmethod
    def _overlap(left: set[str], right: set[str]) -> float:
        return len(left & right) / len(left) if left else 0.0

    @staticmethod
    def _document(product_id: str, product: Mapping[str, Any]) -> str:
        return " ".join(
            [
                product_id,
                str(product.get("name", "")),
                str(product.get("description", "")),
                str(product.get("eligibility_rules", "")),
                " ".join(product.get("benefits", [])),
                " ".join(product.get("required_documents", [])),
            ]
        )

    @staticmethod
    def _embed(text: str, dimension: int = 128) -> List[float]:
        vector = [0.0] * dimension
        for token in ProductRAGService._tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % dimension
            vector[index] += 1.0 if digest[4] % 2 == 0 else -1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    @staticmethod
    def _cosine(left: List[float], right: List[float]) -> float:
        return max(0.0, sum(a * b for a, b in zip(left, right)))
