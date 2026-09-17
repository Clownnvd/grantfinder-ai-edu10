# Brief — GrantFinder AI (Đề 10)

## Lát cắt một câu

Một **nhà nghiên cứu tại Việt Nam** nhập hướng nghiên cứu và hồ sơ cơ bản, để **LangGraph agent chọn và giải thích ba cơ hội tài trợ phù hợp**, giúp họ tạo được một shortlist có nguồn kiểm chứng trong **dưới 5 phút**.

## Vấn đề

Nguồn tài trợ nằm rải rác trên nhiều website. Deadline, eligibility, mức tài trợ và biểu mẫu thường nằm trong HTML/PDF dài. Tìm kiếm bằng từ khóa tạo nhiều kết quả nhiễu và không giải thích được tại sao một call phù hợp.

## Quyết định AI trung tâm

Xếp hạng cơ hội theo bốn tín hiệu:

1. Khớp từ khóa/BM25.
2. Tương đồng ngữ nghĩa từ pgvector.
3. Eligibility tất định từ hard fields.
4. Độ mới và deadline.

Embedding chỉ tạo shortlist. Code quyết định hard facts; người phụ trách xác minh eligibility cuối cùng.

## Kết quả đo được

- Trả đúng 3 cơ hội kèm score breakdown và citations.
- Recall@3 mục tiêu ≥ 0,80.
- Citation coverage của hard facts = 1,00.
- Mọi draft cần nhà nghiên cứu xác nhận và phòng KHCN duyệt.
- Không có chức năng tự nộp hồ sơ.

## Phạm vi MVP

- Nguồn: Grants.gov và NAFOSTED đã source-audit.
- Hai vai trò: `researcher`, `research_manager`.
- Next.js frontend, FastAPI BFF, LangGraph, PostgreSQL + pgvector.
- Gemini chỉ viết lại phần diễn đạt khi được bật; template tất định luôn là fallback.
- Sáu màn hình: khám phá, soạn hồ sơ, giám sát hiệu lực, hàng chờ duyệt, nguồn/đánh giá và tài khoản.

## Ngoài phạm vi

- Không xác nhận eligibility pháp lý cuối cùng.
- Không crawl nguồn có license hạn chế.
- Không lưu CV hoặc dữ liệu nghiên cứu chưa công bố thật.
- Không tự gửi proposal đến funder.
