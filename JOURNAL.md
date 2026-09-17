# Weekly Journal

## Tuần 1 — Dữ liệu và source-first architecture

- Mục tiêu: tìm nguồn tài trợ chính thức có thể tải và tái lập.
- Hoàn thành: Grants.gov snapshot, NAFOSTED source audit, provenance manifest.
- Khó khăn: phân biệt call thật đang mở với bài tin/candidate post.
- Bài học: deadline và eligibility phải là hard fields kèm source span.

## Tuần 2 — Retrieval, pgvector và evaluation

- Mục tiêu: hybrid retrieval và benchmark tối thiểu.
- Hoàn thành: BM25/full-text + pgvector + rule eligibility + rerank.
- Kết quả: Recall@3 = 0,80; citation coverage = 1,00 trên gold set 10 query.
- Bài học: vector similarity chỉ phù hợp để shortlist, không đủ để kết luận eligibility.

## Tuần 3 — LangGraph và HITL

- Mục tiêu: thay workflow tuần tự bằng state graph kiểm chứng được.
- Hoàn thành: match graph, draft graph, conditional edges, checkpoint, graph inspection API, hai human gates.
- Khó khăn: checkpoint Pydantic state cần serializer allowlist.
- Bài học: state graph làm rõ no-grounding, correction và output guard hơn chuỗi hàm tuần tự.
