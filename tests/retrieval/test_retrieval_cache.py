"""Phase 3 section 30: cache key composition must isolate cross-customer
requests -- this is the hard requirement the prompt calls out explicitly
("Test cross-customer cache isolation bắt buộc")."""

from __future__ import annotations

from app.knowledge.retrieval_cache import CacheKey, RetrievalCache


def _key(**overrides) -> CacheKey:
    base = dict(
        normalized_query="von luu dong", agent_type="legal_policy", customer_id=None, case_id=None,
        snapshot_version=None, security_scope_hash="scope-1", retrieval_policy_version="v1",
        index_namespace_corpus_version="corpus-1",
    )
    base.update(overrides)
    return CacheKey(**base)


def test_same_key_is_a_cache_hit():
    cache = RetrievalCache()
    cache.set(_key(), "result-A")
    assert cache.get(_key()) == "result-A"
    assert cache.hits == 1
    assert cache.misses == 0


def test_different_customer_id_is_never_a_cache_hit_for_the_others_entry():
    cache = RetrievalCache()
    cache.set(_key(customer_id="COMP-ABC"), "result-for-ABC")
    assert cache.get(_key(customer_id="COMP-XYZ")) is None
    assert cache.get(_key(customer_id="COMP-ABC")) == "result-for-ABC"


def test_different_case_id_is_never_a_cache_hit_for_the_others_entry():
    cache = RetrievalCache()
    cache.set(_key(case_id="CASE-001"), "result-for-001")
    assert cache.get(_key(case_id="CASE-002")) is None


def test_different_security_scope_hash_is_never_a_cache_hit():
    cache = RetrievalCache()
    cache.set(_key(security_scope_hash="scope-A"), "result-A")
    assert cache.get(_key(security_scope_hash="scope-B")) is None


def test_ttl_expiry_evicts_stale_entry():
    # ttl_seconds=-1 (not 0.0): guarantees "elapsed > ttl_seconds" holds
    # for ANY non-negative elapsed time, including 0 -- a real flake was
    # found here using ttl_seconds=0.0 + time.sleep(0.01): Windows'
    # time.monotonic() granularity can occasionally report 0.0 elapsed for
    # a 10ms sleep under load, so "elapsed > 0.0" intermittently failed.
    cache = RetrievalCache(ttl_seconds=-1.0)
    cache.set(_key(), "result-A")
    assert cache.get(_key()) is None


def test_invalidate_by_corpus_version_only_drops_matching_entries():
    cache = RetrievalCache()
    cache.set(_key(index_namespace_corpus_version="v1"), "old")
    cache.set(_key(normalized_query="other", index_namespace_corpus_version="v2"), "new")
    dropped = cache.invalidate_by_corpus_version("v1")
    assert dropped == 1
    assert cache.get(_key(index_namespace_corpus_version="v1")) is None
    assert cache.get(_key(normalized_query="other", index_namespace_corpus_version="v2")) == "new"


def test_hit_rate_is_none_before_any_access():
    cache = RetrievalCache()
    assert cache.hit_rate is None
