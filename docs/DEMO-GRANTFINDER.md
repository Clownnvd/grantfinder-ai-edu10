# Demo guide

## Tài khoản mô phỏng

Không cần mật khẩu. Dùng bộ chọn vai trò trên giao diện:

- `Nhà nghiên cứu`: tìm kiếm, chọn cơ hội, xác nhận và gửi draft.
- `Quản lý phòng KHCN`: xem review queue và ghi quyết định.

Đây là role simulation cho demo, chưa phải hệ thống authentication production.

## Kịch bản chính

1. Giữ profile mặc định về AI trong giáo dục.
2. Bấm **Tìm 3 cơ hội phù hợp**.
3. Chỉ tool trace: search, eligibility, rerank và human checkpoint.
4. Mở source span và link nguồn gốc.
5. Chọn một cơ hội, tích xác nhận, tạo `[DRAFT_ONLY]`.
6. Gửi review, đổi role sang quản lý và phê duyệt.

## Kịch bản lỗi

- Tạo draft khi chưa tích xác nhận → API 409, không tạo draft.
- Researcher gọi endpoint quyết định review → API 403.
- Tắt PostgreSQL khi `USE_PGVECTOR=1` → workflow fallback và trace có warning.
- Gemini chưa có key/lỗi → deterministic template, không mất workflow.
- Opportunity ID không tồn tại → API 404.

## Câu pitching

“GrantFinder không để vector search quyết định nhà nghiên cứu đủ điều kiện. Retrieval chỉ tạo shortlist; rule kiểm tra hard fields, nguồn gốc đi kèm từng kết quả và hai checkpoint của con người kiểm soát trước draft lẫn phê duyệt.”
