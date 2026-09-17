# Policy Radar → GrantFinder AI

Policy Radar được dùng làm nguồn pattern kỹ thuật. Repo Policy Radar không bị sửa trong đợt triển khai này.

## Pattern được tái sử dụng

| Policy Radar | GrantFinder AI |
|---|---|
| Corpus pháp lý giữ `doc_id`, điều khoản và URL | Opportunity giữ `source_id`, source span và canonical URL |
| Matcher tất định kiểm tra điều kiện doanh nghiệp | Eligibility rules kiểm tra deadline, applicant type và budget ceiling |
| Semantic retrieval chỉ hỗ trợ tìm tài liệu | pgvector chỉ tạo shortlist, không kết luận eligibility |
| Guard chặn số/hard fact do LLM bịa | Number/output guard chặn draft không grounded |
| Write gate trước khi sinh hồ sơ | Researcher confirmation trước khi tạo draft |
| Con người duyệt trước hành động có hậu quả | Research manager approve/request changes |
| BFF tách UI khỏi matcher/retrieval | FastAPI tách Next.js khỏi LangGraph và data layer |
| Eval artifact có thể chạy lại | Recall@3, citation coverage, latency và failure tests |

## Điều chỉnh cho đề 10

- Đối tượng chuyển từ doanh nghiệp/chính sách sang nhà nghiên cứu/cơ hội tài trợ.
- VBPL không còn là corpus chính; Grants.gov và NAFOSTED là corpus cơ hội.
- LangGraph thay workflow tuần tự để thể hiện nhánh no-grounding và hai checkpoint.
- PostgreSQL vừa lưu hard fields vừa chạy full-text, pgvector và checkpoint production.

## Phần không mang sang

- Không dùng model/guard chuyên biệt cho văn bản pháp luật nếu không có nhu cầu.
- Không copy UI, tên sản phẩm hoặc corpus pháp lý vào luồng chính.
- Không dùng eligibility semantic để thay thế điều kiện gốc của funder.
