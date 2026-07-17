# 18 — Data Strategy, Market Data Landscape and Preparation

## 1. Objective

Xác định dữ liệu nào thực sự cần cho solution, dữ liệu nào hiện có và có quyền sử dụng, dữ liệu nào có thể lấy từ nguồn official/open/commercial trên thị trường, cách chuẩn bị dữ liệu thành domain model/RAG/rules/eval và quality gate nào phải đạt trước khi AI dùng dữ liệu để đề xuất hoặc quyết định.

Market scan được cập nhật ngày `2026-07-17`. Tên nhà cung cấp chỉ là ví dụ khảo sát, không phải khuyến nghị mua. Availability, coverage, API, giá và license phải được Procurement/Legal/Data Owner xác minh tại thời điểm ký hợp đồng.

## 2. Quy tắc nền tảng

- Dữ liệu nội bộ SHB là nguồn duy nhất cho product master, policy nội bộ, SOP, customer relationship, workspace, case/task, approval và action history.
- Dữ liệu official/commercial bên ngoài chỉ xác minh/làm giàu, trừ khi policy và data owner phê duyệt rõ vai trò quyết định.
- Không dùng public web scraping không có license/terms rõ làm dữ liệu production.
- Không đưa dữ liệu vào RAG chỉ vì “có file”; phải có owner, purpose, access, effective date, quality và lineage.
- Source availability không đồng nghĩa source phù hợp pháp lý hoặc đủ độ tin cậy.
- Mỗi source phải có `DataSourceCard` theo `contracts/data_source_card.schema.json`.

## 3. Phân tầng dữ liệu theo quyền sử dụng

| Tier | Loại | Ví dụ | Vai trò được phép |
|---|---|---|---|
| A | Internal authoritative | Product master, CRM, IAM, DMS, SOP, approved policy | Nguồn chính theo owner/version/freshness |
| A | Official authoritative | Đăng ký doanh nghiệp, văn bản pháp luật, official sanction list | Xác minh theo phạm vi và điều kiện khai thác |
| B | Licensed curated vendor | Business information, credit/risk, PEP/adverse media | Enrichment/screening theo contract và approved policy |
| C | Open/public | Macro/industry statistics, LEI/open company data | Enrichment, discovery, benchmarking; không tự quyết eligibility |
| D | Derived | Score, summary, entity match, embedding | Chỉ dùng khi có lineage, model/version và validation |
| E | Synthetic/labeled | Demo profiles, golden cases | Dev/test/eval; không trộn vào production facts |

Hard veto: source không có quyền truy cập, legal basis/license, owner hoặc provenance không được publish vào serving layer.

## 4. Dữ liệu cần cho solution và mức độ khả dụng

| Domain | Dữ liệu cần | Nguồn ưu tiên | Thị trường hiện có? | Quyết định sử dụng |
|---|---|---|---|---|
| Employee/workspace | Identity, role, permission, selected customer/case/task/screen | SSO/IAM/HRIS/UI nội bộ | Không thể mua ngoài | Bắt buộc internal, realtime/session |
| Customer/case | Customer master, relationship, products, interaction, case/task | CRM/DWH/task nội bộ | Vendor có thể enrich nhưng không thay CRM | Internal canonical customer ID |
| Documents | Hồ sơ pháp lý/tài chính, version, status, classification | DMS/customer upload | OCR/parser có thể mua | Raw file ở DMS; AI dùng sanitized extraction |
| Product | Catalog, product ID, segment, fees/limits, prerequisites | Product master/approved docs | Không có nguồn ngoài đáng tin cho chính sách SHB | Internal source of truth |
| Legal/SOP | Policy nội bộ, approval matrix, process, SLA | Legal/Compliance/Operations | Public law chỉ bổ sung | Version/effective owner bắt buộc |
| Business registry | Tên, mã số, địa chỉ, đại diện, legal status | Cổng ĐKDN quốc gia | Có public lookup và information services | Verify identity; terms/API phải xác nhận |
| Credit information | Credit history/report/score | CIC + internal credit systems | Có qua kênh được phép, không phải open data | Chỉ adapter được cấp quyền; fail closed |
| Corporate intelligence | Financials, ownership, risk score, industry benchmark | Internal + licensed provider | Có vendor Việt Nam/quốc tế | Enrichment; calibrate coverage/accuracy |
| KYC/AML | Sanctions, PEP, adverse media, watchlists | Internal compliance + official/vendor feeds | Official lists + licensed aggregators | Screening signal; human/compliance review |
| Legal/regulatory | Law, decree, circular, effective status | VBPL, SBV và cơ quan ban hành | Có nguồn official công khai | Legal RAG; rule owner vẫn nội bộ |
| Macro/industry | GDP, CPI, FX, trade, IIP, sector indicators | National Statistics Office/SBV | Có Excel/SDMX/public reports | Context/benchmark, không quyết customer eligibility |
| Global entity | LEI, parent/child, mapped identifiers | GLEIF | Free API/full/delta files | Enrichment cho entity có LEI |
| Cross-border company | Company registry aggregation | Official registry/OpenCorporates/vendor | Open/commercial API tùy license | Candidate/entity resolution, verify primary source |
| Eval/feedback | Intent examples, expected evidence/outcome, RM correction | Synthetic + de-identified approved samples | Không mua trực tiếp đủ sát SHB | SHB SMEs phải label/adjudicate |

## 5. Market data landscape hiện tại

### 5.1. Nguồn official/public tại Việt Nam

| Source | Dữ liệu phù hợp | Access/format quan sát được | Cách dùng trong solution |
|---|---|---|---|
| [Cổng thông tin quốc gia về đăng ký doanh nghiệp](https://dangkykinhdoanh.gov.vn/vn/pages/trangchu.aspx) | Tên/mã số/địa chỉ/đại diện/legal status; information services có báo cáo | Web/public lookup; một số dịch vụ thông tin có tài khoản/phí | Verify entity và resolver candidate; không scrape production nếu chưa có quyền/API |
| [CSDL quốc gia về văn bản pháp luật](https://vbpl.vn/Pages/portal.aspx) | Văn bản trung ương/địa phương, thuộc tính, hiệu lực, bản hợp nhất | Web/document download | Legal ingestion; cần effective/version monitor |
| [Ngân hàng Nhà nước Việt Nam](https://www.sbv.gov.vn/) | Circular/decision/guidance và một số statistics | Web/PDF/official publications | Regulatory source; map document owner/scope |
| [CIC](https://cic.gov.vn/) | Credit report, credit information/rating products | Dịch vụ được kiểm soát, không phải open bulk data | Chỉ tích hợp qua agreement/authorized API hoặc workflow hiện có |
| [National Statistics Office – NSDP](https://nsdp.nso.gov.vn/) | GDP, CPI, government, trade, FX, IIP, industrial/labor indicators | Excel, SDMX, metadata | Industry/macro context, trend and benchmark |

### 5.2. Nguồn global official/open

| Source | Dữ liệu phù hợp | Availability | Giới hạn |
|---|---|---|---|
| [GLEIF API/Data](https://www.gleif.org/en/lei-data/access-and-use-lei-data) | LEI Level 1, parent/child Level 2, mapped IDs | Free search/API/full/delta files | Chỉ entities có LEI; không thay registry Việt Nam |
| [UN Consolidated Sanctions List](https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list) | Individuals/entities chịu UN measures | XML/HTML/PDF | Cần matching, updates, false-positive workflow |
| [OFAC Sanctions List Service](https://ofac.treasury.gov/sanctions-list-service) | US sanctions lists/downloads | Downloadable data | Chỉ một jurisdiction; policy applicability phải xác nhận |
| [World Bank Debarred Firms](https://www.worldbank.org/en/projects-operations/procurement/debarred-firms) | Firms/individuals bị World Bank debar | Search/list cập nhật thường xuyên | Enrichment cho procurement/risk, không thay AML program |
| [OpenCorporates API](https://api.opencorporates.com/) | Company data từ primary public sources, provenance | Open/share-alike hoặc commercial, versioned API | Coverage/license theo jurisdiction/use case |

### 5.3. Nguồn licensed/commercial có thể khảo sát

| Nhóm | Ví dụ thị trường | Dữ liệu/capability | Due diligence bắt buộc |
|---|---|---|---|
| Vietnam business/credit/industry | [FiinGroup](https://fiingroup.vn/) | Corporate reports, business information/API, risk score, industry/trade analysis | Coverage SME, field lineage, update SLA, score validation, license/retention |
| Global KYC/AML/risk | [LSEG World-Check](https://www.lseg.com/en/risk-intelligence) và vendor tương đương | Sanctions, PEP/RCA, adverse media, watchlists, matching/case workflow | Jurisdiction coverage, source transparency, false positives, PII transfer, audit, SLA |
| OCR/document AI | Approved on-prem/cloud vendors | OCR, table/layout extraction, document classification | Vietnamese accuracy, data residency/egress, deletion, model training opt-out |
| Market/industry research | Licensed data/report providers | Industry size, benchmark, transaction/market intelligence | Reproduction rights, API vs report-only, refresh, field-level citation |

Không hard-code vendor vào core domain. Tất cả provider dùng port/adapter và trả về internal model có `provider`, `retrieved_at`, `source_record_id`, `license_scope`, `confidence`.

## 6. Data fitness score và quyết định mua/tích hợp

### 6.1. Hard gates

- Purpose và use case được owner phê duyệt.
- Có legal basis, terms/license và data processing assessment.
- Có stable identifier/provenance hoặc cách reconciliation rõ.
- Có access method hợp lệ; không dựa vào UI scraping mong manh.
- Có owner, SLA/update cadence và incident/contact.
- Không vi phạm data residency, retention, consent hoặc cross-border policy.

### 6.2. Weighted score sau hard gates

| Dimension | Weight | Câu hỏi |
|---|---:|---|
| Legal/license fit | 20 | Được phép ingest, cache, derive, show citation và dùng cho AI? |
| Availability/integration | 15 | API/file/event, auth, quota, sandbox, uptime? |
| Accuracy/provenance | 15 | Primary source, evidence, correction process? |
| Freshness | 15 | Update cadence phù hợp decision window? |
| Coverage | 15 | Bao phủ segment, SME, Việt Nam, historical depth? |
| Joinability | 10 | Tax ID/registration ID/LEI/other stable identifiers? |
| Cost/latency | 5 | Cost/case, bulk/API pricing, P95? |
| Operational fit | 5 | Monitoring, support, version/changelog, exit/export? |

Score chỉ dùng shortlist; bất kỳ hard gate fail đều loại source dù tổng điểm cao.

### 6.3. POC vendor/source

1. Chọn 100–500 synthetic/de-identified entities đại diện segment.
2. Định nghĩa expected fields, freshness và ground truth mẫu.
3. Đo coverage, match precision/recall, stale rate, missing rate, latency và cost.
4. Red-team false positives cho tên Việt Nam, viết tắt, không dấu, địa chỉ thay đổi.
5. Kiểm license cho caching, embeddings, derived scores và retention.
6. Chạy shadow mode; không dùng kết quả để auto-block/pass.
7. SME/Compliance review và ký Data Source Acceptance Record.

## 7. Data inventory và Source Card

Mỗi source phải đăng ký:

- `source_id`, domain, owner, steward, provider, tier.
- Purpose, allowed/prohibited uses, decision role.
- Legal basis/license/DPA, residency, retention/deletion.
- Access method, auth, quota, SLA, cost model.
- Schema/format, primary identifiers, join keys.
- Update cadence, effective/version semantics, late data behavior.
- Quality dimensions, thresholds, sample report.
- PII/sensitivity/classification, ACL/ABAC policy.
- Lineage, ingestion job, serving tables/index/rules/eval dependencies.
- Incident, correction, deprecation và exit plan.

Schema: `contracts/data_source_card.schema.json`.

## 8. Data architecture và preparation pipeline

```text
Discover/Register Source
→ owner/legal/license/privacy assessment
→ raw acquisition to quarantine
→ malware/type/schema/manifest validation
→ parse/OCR/table extraction
→ normalize encoding, units, dates, identifiers
→ entity resolution against internal canonical IDs
→ quality profiling + reconciliation
→ PII classification, minimization, masking, ACL
→ version/effective-date/change detection
→ publish Silver normalized domain data
→ publish Gold product/rule/context/eval artifacts
→ chunk/index or compile rules
→ acceptance tests + source owner sign-off
→ Serving with trace/lineage/monitoring
```

### 8.1. Data layers

| Layer | Nội dung | Quy tắc |
|---|---|---|
| Quarantine/Raw | File/API payload bất biến + manifest/hash | Không đưa model sử dụng trực tiếp |
| Silver | Parsed, normalized, typed, canonical IDs, quality flags | Giữ source record + lineage |
| Gold | Approved product/policy/rules/context features/eval labels | Owner/version/effective/ACL bắt buộc |
| Serving | API tables, vector/sparse indexes, rule registry, feature views | Chỉ publish artifacts pass gate |
| Audit | Ingest report, change log, decisions, failures | Append-only/retention controlled |

### 8.2. Xử lý theo loại dữ liệu

| Type | Preparation |
|---|---|
| PDF/Word policy | SHA-256, parser/OCR, preserve heading/page/table, effective dates, structure chunks, citation QA |
| Excel/catalog | Schema/unit/currency validation, product ID mapping, effective rows, duplicate/conflict checks |
| CRM/API records | Adapter normalization, canonical ID, freshness, field-level provenance, CDC/event or TTL |
| KYC/vendor responses | Store source record/reference, match features/score, review status, expiry; không log raw PII |
| Conversation | Segment by message, extract confirmed facts/corrections, redact PII, retention; không lưu raw forever |
| Tasks/artifacts | Canonical dedup key, input/output hash, version, supersedes/reuse links |
| Eval labels | Dataset version, expected behavior/evidence, reviewer/adjudication, no production facts |

## 9. Entity resolution

- `customer_id` nội bộ là canonical ID trong workflow.
- Business registration/tax ID, LEI và vendor IDs là external identifiers có source/version.
- Exact stable-ID match ưu tiên; tên/địa chỉ fuzzy match chỉ tạo candidate.
- High-impact merge/switch phải có confirmation hoặc steward review.
- Lưu match method, score, normalized fields và evidence; không overwrite source record.
- Không join cross-customer chỉ bằng tên viết tắt.

## 10. Data quality gates

| Dimension | Check | Failure behavior |
|---|---|---|
| Completeness | Required fields theo artifact/stage | Quarantine hoặc pending information |
| Validity | Type, enum, unit, date/effective range | Reject row/document version |
| Uniqueness | Product/rule/document/entity keys | Conflict report; không silently pick |
| Consistency | CRM vs DMS vs registry; currency/unit | Precedence policy hoặc pending review |
| Freshness | TTL/effective/update SLA | Mark stale; block time-sensitive decision |
| Provenance | Source/record/location/hash/version | Không publish claim/index/rule |
| Access | ACL/employee/customer scope | Fail closed |
| Extraction quality | OCR/table/heading/citation sample | Human review/exclude low-quality chunks |
| Drift | Schema/coverage/value/rank changes | Alert, canary/re-index/recalibrate |

Threshold cụ thể phải cấu hình theo source/artifact; không dùng một threshold chung cho mọi domain.

## 11. Data preparation theo module

| Consumer | Gold artifact cần | Acceptance chính |
|---|---|---|
| Context Engine | Canonical customer/case/task/doc metadata + provenance | Cross-customer leak=0; auto-fill ≥98% |
| Intent | Versioned taxonomy, aliases, annotated conversations | Intent/multi-intent thresholds |
| Product RAG | Product master + approved documents/chunks/index manifest | Hit@5, version/ACL/citation gates |
| Eligibility | Versioned executable rules + legal evidence mapping | Unsafe pass=0; every block has source |
| Operations | Controlled document taxonomy, SOP/SLA/templates | Checklist/dedup/draft gates |
| Safety | Tool contract, PII policy, injection/security dataset | Deterministic deny/allow and audit |
| Eval | Golden records with expected IDs/outcomes | Reproducible versioned reports |

## 12. MVP data pack

Minimum synthetic pack để build end-to-end:

- 10 doanh nghiệp thuộc 4–5 segment/industry, có stable IDs và permission scopes.
- 8–12 products thuộc payroll, collection/payment, cash management, credit/trade.
- 20–30 product/legal/SOP documents có version/effective dates, gồm superseded/conflict cases.
- 5–10 rules blocking/warning/missing với source mapping.
- 50 intent conversations có workspace context, abbreviations, corrections và multi-intent.
- 40 product RAG queries; 40 eligibility cases; 40 E2E cases; 25 security; 20 reliability.
- 1 vendor/official-source adapter POC ở shadow mode, không bắt buộc cho MVP offline.

Không dùng dữ liệu khách hàng thật trong hackathon. Pilot data phải de-identify/minimize và có approval trước ingestion.

## 13. Data lifecycle

```text
Proposed → Assessed → Contracted/Approved → Onboarding
→ Shadow → Active → Degraded/Stale → Deprecated → Deleted/Archived
```

- Version/index/rule dependency phải biết source đang Active hay Stale.
- Source schema/license/owner change tạo impact event.
- Deprecation phải có consumer inventory, migration và re-index/re-eval plan.
- Delete/retention phải xóa hoặc tombstone đúng raw, derived, cache, embedding và artifact theo policy.

## 14. Security/privacy/legal

- Luật Bảo vệ dữ liệu cá nhân số `91/2025/QH15` có hiệu lực từ `2026-01-01`; Legal/Privacy phải xác nhận nghĩa vụ cụ thể cho từng source và flow.
- Không coi dữ liệu public là tự do ingest/reuse; vẫn kiểm terms, purpose, retention và quyền chủ thể dữ liệu.
- PEP/adverse media có thể chứa dữ liệu nhạy cảm; cần policy, access, review và false-positive remediation.
- Dữ liệu raw PII không đưa vào log/prompt/index nếu summary/feature đủ dùng.
- Model/vendor không được train trên dữ liệu SHB nếu chưa có quyền rõ ràng.
- Cross-border processing, subprocessors, deletion evidence và incident SLA phải nằm trong due diligence.

## 15. Proposed code/data artifacts

| Artifact | Responsibility |
|---|---|
| `contracts/data_source_card.schema.json` | Source inventory/governance contract |
| `app/data_catalog/models.py` | Source/card/dataset/version models |
| `app/data_catalog/registry.py` | Register, approve, lifecycle, consumers |
| `app/data_quality/profiling.py` | Completeness/validity/uniqueness/freshness |
| `app/data_quality/gates.py` | Publish/quarantine/block decisions |
| `app/entity_resolution/service.py` | Canonical ID and candidate matching |
| `app/ingestion/manifest.py` | Hash, lineage, ingest report |
| `data/catalog/source_cards/` | Versioned source card instances |
| `data/contracts/` | Expected schemas/sample payloads |
| `tests/data/` | Schema drift, quality, ACL, lineage tests |

## 16. Build sequence

1. Inventory internal sources and data owners.
2. Create Source Cards and classify Tier/sensitivity/decision role.
3. Build synthetic MVP pack and expected contracts.
4. Implement manifest/quarantine/quality gates before RAG ingestion.
5. Build canonical IDs/entity resolution and data conflict policy.
6. Publish Product/Legal/Context Gold artifacts.
7. Build index/rules/eval from Gold only.
8. POC official/vendor adapters in shadow mode.
9. Run source acceptance and cost/quality/coverage report.
10. Pilot only after legal/privacy/security/data-owner sign-off.

## 17. Acceptance

- 100% serving sources có valid Source Card, owner, purpose, lineage và version.
- 100% Product/Legal important claims trace về Gold → Silver → raw/official source.
- Unauthorized/unlicensed source exposure = 0.
- Stale/expired policy used for time-sensitive decision = 0.
- Entity merge false positive trên high-risk golden set = 0.
- Data quality gate deterministic và có ingest report tái lập được.
- Vendor/source failure có fallback hoặc pending behavior; không làm hệ thống tự pass eligibility.

