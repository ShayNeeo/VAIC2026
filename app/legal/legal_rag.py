"""Legal RAG Service (L4).

Retrieval-Augmented Generation cho các chính sách và văn bản pháp luật.
Hybrid retrieval: dense (hash-based cho demo) + sparse (token match).
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from .knowledge_base import LEGAL_KNOWLEDGE_CHUNKS

logger = logging.getLogger(__name__)


class LegalRAGService:
    """Service tìm kiếm các điều khoản pháp lý và policies."""

    def __init__(self, data_dir: str = "data/legal/policies/"):
        self.data_dir = Path(data_dir)
        self.chunks: List[Dict[str, Any]] = []
        self._load_knowledge()

    def _load_knowledge(self) -> None:
        """Load data từ JSON files, fallback về in-memory KB."""
        self.chunks = []
        try:
            if self.data_dir.exists():
                for file_path in self.data_dir.glob("*.json"):
                    if file_path.name == "shb_product_eligibility_rules.json":
                        continue # Skip rules, only load policies
                        
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self._process_policy_document(data)
                
            if not self.chunks:
                logger.warning(f"No policy data found in {self.data_dir}. Using built-in chunks.")
                self.chunks = LEGAL_KNOWLEDGE_CHUNKS
            else:
                logger.info(f"Loaded {len(self.chunks)} policy chunks from {self.data_dir}")
                
        except Exception as e:
            logger.error(f"Failed to load legal knowledge: {e}")
            self.chunks = LEGAL_KNOWLEDGE_CHUNKS

    def _process_policy_document(self, data: Dict[str, Any]) -> None:
        """Chuyển đổi hierarchical policy document thành flat chunks."""
        doc_id = data.get("document_id", "Unknown")
        doc_title = data.get("title", "Unknown Policy")
        effective_from = data.get("effective_from")
        
        for chapter in data.get("chapters", []):
            chap_title = chapter.get("title", "")
            for article in chapter.get("articles", []):
                art_id = article.get("article_id", "")
                art_title = article.get("title", "")
                art_text = article.get("text", "")
                
                # Gom clauses vào chung chunk của article (hoặc tách riêng nếu muốn mịn hơn)
                clauses_text = ""
                rule_refs = []
                for clause in article.get("clauses", []):
                    clauses_text += " " + clause.get("text", "")
                    rule_refs.extend(clause.get("rule_refs", []))
                    
                full_text = f"{art_text}{clauses_text}".strip()
                
                chunk = {
                    "chunk_id": f"{doc_id}-{art_id}",
                    "document_id": doc_id,
                    "document_title": doc_title,
                    "chapter": chap_title,
                    "article": art_title,
                    "article_id": art_id,
                    "text": full_text,
                    "effective_from": effective_from,
                    "rule_refs": list(set(rule_refs)),
                    "keywords": self._extract_keywords(full_text)
                }
                self.chunks.append(chunk)

    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction (cho sparse retrieval)."""
        # Đây là mock cho demo. Thực tế dùng nlp tokenizer.
        words = text.lower().replace(",", "").replace(".", "").split()
        return [w for w in words if len(w) > 3]

    def _hash_embedding(self, text: str) -> int:
        """Deterministic hash-based dense embedding mock."""
        return int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Hybrid search (sparse + dense mock)."""
        if not query or not self.chunks:
            return []

        query_lower = query.lower()
        query_words = self._extract_keywords(query_lower)
        query_hash = self._hash_embedding(query_lower)
        
        scored_chunks = []
        for chunk in self.chunks:
            score = 0.0
            
            # 1. Sparse matching (keyword overlap)
            chunk_keywords = chunk.get("keywords", [])
            overlap = len(set(query_words).intersection(set(chunk_keywords)))
            if overlap > 0:
                score += overlap * 0.2
                
            # Exact phrase match boost
            if query_lower in chunk.get("text", "").lower():
                score += 1.0
                
            # Rule ref match boost
            if query.upper() in chunk.get("rule_refs", []):
                score += 1.5
                
            # 2. Dense matching (mock hash distance)
            # Trong thực tế, dùng cosine similarity. Ở đây dùng fake distance.
            chunk_hash = self._hash_embedding(chunk.get("text", ""))
            hash_dist = abs(query_hash - chunk_hash) / (16**8)  # normalize 0-1
            dense_score = 1.0 - hash_dist
            score += dense_score * 0.3
            
            if score > 0.3:
                scored_chunks.append((score, chunk))
                
        # Sort by score desc
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Return top_k chunks
        return [chunk for score, chunk in scored_chunks[:top_k]]

    def build_context(self, queries: List[str], top_k_per_query: int = 2) -> Dict[str, Any]:
        """Tổng hợp context từ nhiều query."""
        all_chunks = []
        seen_chunk_ids = set()
        
        for q in queries:
            results = self.search(q, top_k=top_k_per_query)
            for r in results:
                cid = r.get("chunk_id")
                if cid not in seen_chunk_ids:
                    seen_chunk_ids.add(cid)
                    all_chunks.append(r)
                    
        # Format lại cho dễ đọc trong prompt LLM
        formatted_context = ""
        sources = []
        
        for c in all_chunks:
            formatted_context += f"\n--- {c['document_title']} | {c['chapter']} | {c['article']} ---\n"
            formatted_context += f"{c['text']}\n"
            
            sources.append({
                "document_id": c["document_id"],
                "article": c["article"],
                "chunk_id": c["chunk_id"]
            })
            
        return {
            "context_text": formatted_context,
            "sources": sources,
            "grounded": len(all_chunks) > 0
        }
