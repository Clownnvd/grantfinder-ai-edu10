# Nguồn dữ liệu và provenance

## Snapshot đang dùng

- Grants.gov bulk extract ngày 14/09/2026: 83.394 records; 965 open theo ngày trong snapshot.
- API live ngày 15/09/2026: 964 `posted`; chênh một record vì bulk chậm hơn API một ngày.
- NAFOSTED: 44 candidate posts; chỉ 3 call còn hạn đã source-audit được đưa vào open corpus.
- Corpus ứng dụng: 968 open opportunities.

## Quy tắc ingest

1. Lưu URL, source ID, ngày snapshot và document hash.
2. Tách hard fields khỏi text dùng embedding.
3. Deadline, funding, eligibility dùng cột quan hệ/JSONB và source span.
4. Embedding chỉ hỗ trợ retrieval; không quyết định hard facts.
5. Bản ghi thiếu deadline/eligibility được đánh dấu review, không tự điền.
6. Incremental sync đối chiếu source ID + modified date; không tạo duplicate.

## Tệp

- `data/grants/grants_gov_open_2026-09-15.json`
- `data/grants/nafosted_open_curated_2026-09-15.json`
- `data/grants/nafosted_candidate_posts_2026-09-15.json`
- `data/grants/grants_gov_processing_summary.json`

## License/terms

Nguồn là public official data, nhưng production vẫn phải rà điều khoản sử dụng, attribution và rate limit của từng nguồn. Pivot-RP chỉ dùng làm benchmark sản phẩm, không làm corpus nếu chưa có quyền bằng văn bản.
