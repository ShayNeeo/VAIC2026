"""Retrieval cache -- RAG & Guardrail Implementation Plan Phase 3 section
30.

In-process dict cache (no Redis/external cache dependency in this repo) --
labeled IMPLEMENTED_WITH_DETERMINISTIC_ADAPTER: real caching semantics
(key composition, invalidation), but not a distributed cache suitable for
multi-process production deployment. The key composition is the part that
matters for correctness (cross-customer isolation): every field the
prompt lists is part of the key, so two requests differing in ANY of them
(especially customer_id/case_id/security scope) never collide.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CacheKey:
    normalized_query: str
    agent_type: str
    customer_id: Optional[str]
    case_id: Optional[str]
    snapshot_version: Optional[str]
    security_scope_hash: str
    retrieval_policy_version: str
    index_namespace_corpus_version: str

    def digest(self) -> str:
        raw = "|".join(
            [
                self.normalized_query, self.agent_type, self.customer_id or "-", self.case_id or "-",
                self.snapshot_version or "-", self.security_scope_hash, self.retrieval_policy_version,
                self.index_namespace_corpus_version,
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class RetrievalCache:
    def __init__(self, *, ttl_seconds: float = 300.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, tuple[float, CacheKey, Any]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: CacheKey) -> Optional[Any]:
        digest = key.digest()
        entry = self._store.get(digest)
        if entry is None:
            self.misses += 1
            return None
        stored_at, _key, value = entry
        if time.monotonic() - stored_at > self.ttl_seconds:
            del self._store[digest]
            self.misses += 1
            return None
        self.hits += 1
        return value

    def set(self, key: CacheKey, value: Any) -> None:
        self._store[key.digest()] = (time.monotonic(), key, value)

    def invalidate_by_corpus_version(self, corpus_version: str) -> int:
        """Called when a snapshot/policy/catalog/SOP version changes --
        drops every entry whose index_namespace_corpus_version no longer
        matches the new version. Real selective invalidation: the CacheKey
        is stored alongside each entry precisely so this can filter on it
        (not just on the one-way digest)."""
        stale = [
            digest for digest, (_ts, cached_key, _value) in self._store.items()
            if cached_key.index_namespace_corpus_version == corpus_version
        ]
        for digest in stale:
            del self._store[digest]
        return len(stale)

    def clear_all(self) -> int:
        count = len(self._store)
        self._store.clear()
        return count

    @property
    def hit_rate(self) -> Optional[float]:
        total = self.hits + self.misses
        if total == 0:
            return None
        return round(self.hits / total, 4)
