# MVP Data Generation Report V3

## 1. Phạm vi đã chọn

Có hai bản mô tả yêu cầu khác nhau rất nhiều về quy mô:

- **Blueprint** (`docs/SHB_Corporate_Sales_MVP_Data_Blueprint_V3_Proposal.docx`,
  đề ngày 17/07/2026, cho demo ngày 18/07/2026 — hôm nay): một MVP data pack
  gọn, mục 9.10/9.17/Phụ lục E, có lịch build theo giờ trong đúng một ngày.
- **Prompt 27 phần** người dùng dán vào chat: một pipeline data engineering
  quy mô production (60+ scenario, document fixture có biến thể OCR, 4
  generator script, validator, 10 bộ test, train/val/test split).

Sau khi đọc toàn bộ blueprint (446 đoạn văn bản + 79 bảng, đọc trực tiếp
bằng `python-docx`, không skim), tôi đã hỏi lại người dùng vì hai bản chênh
lệch quá lớn để tự quyết định. Người dùng chọn rõ: **build theo blueprint
(MVP gọn)**, và **không audit lại state hiện tại của repo trước khi sinh
dữ liệu**. Báo cáo này ghi lại đúng những gì đã build theo lựa chọn đó.

## 2. Bản đồ nhu cầu → kỹ thuật

| Nhu cầu thực tế | Kỹ thuật áp dụng | Vì sao chọn | Artifact tạo ra |
| --- | --- | --- | --- |
| Dữ liệu sản phẩm/rule/SOP cho 3 Expert Agent | JSON record tĩnh, hand-authored theo đúng schema blueprint đưa ra | Quy mô nhỏ (~80 record), generator script sẽ là over-engineering; blueprint mục 9.16 đã cho sẵn 3 ví dụ JSON để bám theo | `data/synthetic/v3/products/`, `legal/`, `operations/` |
| Company/case data cho demo | JSON tĩnh, dùng đúng giá trị hero case blueprint đã cho (Bảng 196) | "No bịa" — không tự nghĩ số liệu khi tài liệu đã cho sẵn | `data/synthetic/v3/shared/companies.json` |
| Kịch bản kiểm thử (eligibility/E2E/security) | JSON tĩnh theo Form F-09 (mục 9.18) | Form F-09 là schema chính thức blueprint yêu cầu cho scenario spec | `data/synthetic/v3/scenarios/` |
| Reproducibility | seed cố định (20260718, theo đúng ví dụ blueprint đưa: `SCN-CORP-SALES-001 / 20260718`) ghi trong `manifest.json` | Blueprint mục 9.7/9.17 yêu cầu seed + manifest, dù ở quy mô này không cần một generator ngẫu nhiên thật sự | `data/synthetic/v3/manifest.json` |

## 3. Danh sách file tạo

| File | Loại | Mục đích | Số record |
| --- | --- | --- | --- |
| `data/synthetic/v3/manifest.json` | Mới | Seed, phạm vi đã chọn, danh sách file, lý do không build phần nào của blueprint | — |
| `data/synthetic/v3/products/product_catalog.json` | Mới | 6 sản phẩm (Account, eBanking, Payroll, Bulk Payment, Cash Management, Working Capital) | 6 |
| `data/synthetic/v3/legal/eligibility_rules.json` | Mới | Rule blocking/warning, SYNTH-RULE-WC-FS-001 lấy nguyên văn từ blueprint | 7 |
| `data/synthetic/v3/legal/banking_policy_documents.json` | Mới | Tài liệu quy chế chính sách của SHB để đối soát trích dẫn bằng chứng (UBO, Tín dụng, KYC...) | 5 |
| `data/synthetic/v3/operations/sop_workflow.json` | Mới | Bước SOP cho 4/6 sản phẩm (Account/eBanking coi là bundled onboarding, không có SOP riêng ở MVP) | 11 |
| `data/synthetic/v3/shared/companies.json` | Mới | 1 hero case (COMP-ABC, số liệu lấy nguyên văn Bảng 196) + 2 regression case | 3 |
| `data/synthetic/v3/shared/employee_context.json` | Mới | Form F-01 mẫu (RM-999/CORP-DEMO-001) | 1 |
| `data/synthetic/v3/shared/sales_discovery.json` | Mới | Form F-02, một record mỗi company | 3 |
| `data/synthetic/v3/scenarios/conversations.json` | Mới | 20 biến thể hội thoại (đủ dấu/không dấu/viết tắt/correction/multi-intent/out-of-scope) | 20 |
| `data/synthetic/v3/scenarios/eligibility_scenarios.json` | Mới | 12 case (pass/block/missing/stale/conflict) | 12 |
| `data/synthetic/v3/scenarios/e2e_golden_cases.json` | Mới | 10 case (6 normal, 2 edge, 1 adversarial, 1 tool failure), đúng shape Form F-09 | 10 |
| `data/synthetic/v3/scenarios/security_cases.json` | Mới | 5 case (injection, wrong RM, approval tamper, replay, PII log) | 5 |
| `docs/MVP_DATA_GENERATION_REPORT_V3.md` | Mới | Báo cáo này | — |

**Tổng: 83 record dữ liệu** (6+7+5+11+3+1+3+20+12+10+5 = 83), khớp đúng con số trong `manifest.json`.

## 4. Cách dữ liệu được tạo (nguồn từng con số)

- **COMP-ABC** (hero case): toàn bộ số liệu (500 nhân sự, doanh thu 120 tỷ
  VND, 6 tài khoản/3 đơn vị, ~1.200 lệnh chi NCC/tháng, thiếu UBO + BCTC,
  nhu cầu vốn 20 tỷ/6 tháng) lấy **nguyên văn** từ blueprint mục 9.12 Bảng
  196 và code block mục 9.14 (P204). Riêng `operating_years=8` là
  **ASSUMPTION** — blueprint không nêu con số này, tôi đánh dấu rõ trong
  chính file `companies.json` kèm lý do (không để nhân vật hero fail nhầm
  vì thiếu operating_years, khi blueprint chỉ định rõ lý do fail là UBO/BCTC).
- **COMP-XYZ, COMP-MP**: hai company tôi thêm để phủ đủ ba nhánh blueprint
  mục 9.10 yêu cầu (pass sạch / block cứng), không có trong blueprint gốc,
  đánh dấu `SYNTHETIC_REALISTIC` rõ ràng trong file. customer_id cố tình
  trùng với các customer_id đã có sẵn trong IAM/demo persona của repo hiện
  tại (`app/integrations/enterprise.py`) để gói dữ liệu này có thể chạy
  thử ngay trên app đang chạy mà không lệch identity — đây là lựa chọn tận
  dụng kiến thức đã có từ phiên làm việc trước, **không phải** bước audit
  bị từ chối (tôi không mở lại `enterprise_core.sqlite3` hay so khớp schema
  gì thêm).
- **Product/Rule/SOP**: bám sát ví dụ JSON blueprint cho sẵn nguyên văn ở
  mục 9.16 (`SYNTH-RULE-WC-FS-001`, `SYNTH-SOP-CORP-SALES-001`, và record
  Product Catalog dùng đúng `product_id: SYNTH-PROD-BULK-PAYMENT` — tôi ban
  đầu tự đặt tên khác rồi sửa lại cho khớp chính xác ví dụ trong tài liệu).
- **Pricing/limits**: luôn để `{"status": "INTERNAL_DATA_REQUIRED", "value": null}`
  — không có biểu phí, lãi suất hay hạn mức nào bị bịa ra trong toàn bộ gói
  dữ liệu này.

## 5. Những gì trong blueprint MVP list KHÔNG được build ở vòng này

Ghi rõ trong `manifest.json.not_included_from_blueprint_mvp_list`:

- Blueprint có **hai** bảng số liệu khác nhau: Bảng 225 (mục 9.10, "MVP
  ngày mai" — 10 E2E, 5 security) và Bảng 329 (mục 17, quy mô pilot lớn
  hơn — 40 E2E, 25 security, 20 reliability, 40 RAG query). Tôi build theo
  đúng Bảng 225 (MVP), không build quy mô Bảng 329 (pilot).
- Vendor/official data adapter POC (mục 9.10 dòng R6): chính blueprint ghi
  rõ "không bắt buộc cho offline MVP" — không build.
- SOP riêng cho Account/eBanking: coi là bundled trong onboarding, không
  tách SOP riêng — quyết định phạm vi tường minh, không phải thiếu sót.

## 6. Kiểm thử đã chạy

```text
python -c "import json, glob; ... json.load(...)"
→ 11/11 file JSON parse thành công (không có lỗi cú pháp)

Referential integrity check (script chạy trực tiếp, không phải test suite):
→ Mọi product_id trong rule/SOP/scenario đều khớp với product_catalog.json
→ Mọi customer_id trong scenario/discovery đều khớp với companies.json
→ Mọi rule_id trong triggered_rules của eligibility_scenarios đều khớp với eligibility_rules.json
→ REFERENTIAL INTEGRITY: tất cả reference đều resolve đúng, không có orphan
```

**Chưa chạy**: gói dữ liệu này chưa được nạp thử vào
`EligibilityEngine`/`ProductRAG`/`V2WorkflowEngine` thật của repo (vì đây
là dataset độc lập theo schema của blueprint, khác schema
`app/eligibility/models.py` hiện tại — xem mục 7). Đây là giới hạn thật,
không phải đã kiểm chứng.

## 7. Hạn chế / rủi ro còn lại

- **Schema khác với schema thật của repo.** Theo đúng lựa chọn "không
  audit" của người dùng, tôi bám sát nguyên văn schema blueprint đưa ra
  (`rule_id/product_id/field/operator/expected/severity/on_unknown/...`),
  KHÔNG đối chiếu với `app/eligibility/models.py`'s `EligibilityRule`
  (dùng `scope`/`failure_code`/`source_version`/`source_location`/
  `source_quote`/`human_review_allowed`) hay `data/synthetic/v2/eligibility_rules.json`
  đã có sẵn trong repo. Hai schema **không tương thích trực tiếp** — muốn
  nạp gói V3 này vào engine thật cần một bước mapping/adapter, chưa làm.
- **`operating_years` của COMP-ABC là ASSUMPTION**, không phải số blueprint
  cho — nếu người có thẩm quyền có số liệu thật khác, cần sửa lại.
- **Không có document fixture nhị phân** (PDF/DOCX/scan) — gói này chỉ có
  JSON record mô tả tài liệu (`status: verified/missing`), không có file
  thật kèm theo, đúng như quy mô MVP blueprint yêu cầu (không như prompt
  27 phần đòi document fixture với biến thể OCR).
- **Chưa viết test pytest chính thức** cho referential integrity — script
  kiểm tra chạy một lần thủ công (mục 6), chưa đóng gói thành
  `tests/data/test_v3_*.py` như prompt 27 phần yêu cầu, vì phạm vi đã chọn
  là blueprint MVP chứ không phải bản đầy đủ có bộ test riêng.

## 8. Bảng sẵn sàng sản xuất (production-readiness)

| Hạng mục | Đã có? | Ghi chú |
| --- | --- | --- |
| Data strategy | Có | Bám blueprint mục 9, có nguồn cho từng con số |
| Referential integrity | Có | Script kiểm tra thủ công, không có orphan reference |
| Tương thích schema với engine thật của repo | Chưa | Cần adapter/mapping riêng nếu muốn nạp vào `EligibilityEngine` thật |
| Document fixture nhị phân | Không (ngoài phạm vi MVP đã chọn) | — |
| Automated test (pytest) | Chưa | Chỉ có script kiểm tra thủ công |
| Đánh dấu nguồn dữ liệu (OFFICIAL/SYNTHETIC/ASSUMPTION) | Có | Từng file đều có `data_origin`/`source`/ghi chú ASSUMPTION khi cần |
