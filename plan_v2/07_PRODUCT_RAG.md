# 07 — Product Knowledge and RAG

## 1. Objective

Tìm đúng sản phẩm/policy theo intent và customer context, chỉ dùng phiên bản còn hiệu lực, tôn trọng ACL và trả citation có thể xác minh.

## 2. Data sources

| Source | Format | Owner | Required metadata |
|---|---|---|---|
| Product catalog | PDF/Excel/DB | Product team | product_id, segment, version |
| Product policy | PDF/Word | Risk/Product | effective dates, status |
| Fee/limit tables | Excel/table | Product | currency, units, version |
| FAQ/Sales guide | Docs | Sales enablement | audience, scope |

MVP dùng synthetic documents; pilot yêu cầu data owner sign-off.

## 3. Ingestion pipeline

```text
File/API input
→ SHA-256 + document ID/version
→ MIME/type detection
→ parser/OCR router
→ text/table extraction
→ Unicode normalization
→ quality checks
→ product/domain classification
→ structure-aware chunking
→ metadata/ACL enrichment
→ embedding + sparse index
→ index manifest + ingest report
```

Ingestion idempotent theo `document_id + version + content_hash`.

## 4. Chunk model

Required fields:

```text
chunk_id, document_id, document_version, product_id
section_path, page, chunk_type
text_for_embedding, text_for_llm
effective_from, effective_to, active
segment, industry, access_scope
content_hash, parent_chunk_id, prev/next_chunk_id
```

Chunking:

- Product overview: theo product section.
- Eligibility: không tách rule khỏi product ID.
- Table: summary + row chunks, giữ units/header.
- FAQ: question + answer cùng chunk.
- Policy: heading hierarchy + parent reference.

## 5. Retrieval pipeline

```text
Intent/query normalizer
→ access + effective-date filters
→ query expansion from resolved slots
→ dense top 20
→ sparse/BM25 top 20
→ normalized weighted fusion
→ heuristic/domain rerank
→ dedup + source diversity
→ threshold/OOS gate
→ top 3–5 context chunks
```

Initial weights are config, not constants: dense 0.6, sparse 0.4. Tune from eval.

## 6. Metadata filters

Applied before or during retrieval:

- `active = true`.
- Effective date covers request date.
- Employee access scope permits document.
- Segment/industry when known.
- Product family if intent resolved.
- Language/version.

ACL filter must occur before context reaches model.

## 7. Product matching

RAG retrieves candidates; deterministic matcher calculates:

```text
intent fit
+ segment fit
+ size/revenue fit
+ workflow/customer signal
- missing prerequisites
- legal blocking (display separately, not silently remove)
```

Output per product:

- product ID/name.
- match score and score components.
- matching reason.
- prerequisites.
- source evidences.
- `eligible` must remain unknown until Eligibility module.

## 8. Grounded answer policy

- Product names only from controlled catalog.
- Fees, limits and conditions require exact evidence.
- Missing or conflicting context returns uncertainty.
- Superseded documents excluded and logged.
- Retrieval empty must not trigger hallucinated fallback.

## 9. Proposed code artifacts

| File | Responsibility |
|---|---|
| `app/knowledge/models.py` | Document/chunk/index models |
| `app/knowledge/ingest/pipeline.py` | Ingestion orchestration |
| `app/knowledge/ingest/parsers.py` | Parser router |
| `app/knowledge/chunking/product.py` | Product structure chunking |
| `app/knowledge/index/dense.py` | Dense index adapter |
| `app/knowledge/index/sparse.py` | BM25 adapter |
| `app/knowledge/retrieval/product.py` | Hybrid retrieval |
| `app/product/matcher.py` | Deterministic scoring |
| `app/product/service.py` | Product module facade |

## 10. Failure/fallback

| Failure | Behavior |
|---|---|
| Index unavailable | Circuit breaker; return source browser/manual path |
| No result above threshold | `no_grounded_product`; no recommendation |
| Conflicting policy versions | pending review; show both sources |
| Low extraction quality | exclude or mark needs human review |
| Stale index | alert; refuse time-sensitive policy claims |

## 11. Tests/eval

- Payroll query retrieves Payroll.
- Distributed cash flow + revenue retrieves Cash Management.
- Credit intent retrieves Working Capital policy.
- Exact product code found by sparse retrieval.
- Old policy version excluded.
- ACL-blocked chunk never returned.
- Out-of-scope weather query returns empty.
- Table unit/header preserved.
- Every recommendation has valid evidence.

Metrics: Hit@1/3/5, MRR, context precision/recall, source accuracy, OOS precision, latency.

## 12. Acceptance

- Retrieval Hit@5 ≥ 95% on product golden set before pilot.
- Unsupported product recommendation = 0.
- Superseded/unauthorized document exposure = 0.

