# ADR-001: LangGraph làm bộ điều phối workflow

**Ngày:** 2026-09-17  
**Trạng thái:** Accepted

## Bối cảnh

Workflow đề 10 có nhiều nhánh: pgvector có thể lỗi, retrieval có thể không có căn cứ, nhà nghiên cứu phải xác nhận trước khi draft, output guard có thể chặn kết quả và phòng KHCN phải duyệt. Một chuỗi hàm tuần tự khó biểu diễn checkpoint và khó kiểm tra nhánh lỗi.

## Lựa chọn

1. Python service tuần tự: ít dependency nhưng state/checkpoint không rõ.
2. LangChain chain: phù hợp luồng tuyến tính, khó mô tả HITL và conditional routing.
3. LangGraph `StateGraph`: state typed, conditional edges, checkpoint và trace rõ ràng.

## Quyết định

Chọn LangGraph với hai graph độc lập: `match_graph` và `draft_graph`.

## Lý do

- Thể hiện trực tiếp các nhánh no-grounding, confirmation và output guard.
- Mỗi node trả partial state và một `ToolEvent` kiểm chứng được.
- Checkpoint hỗ trợ inspect/replay; local dùng memory, production dùng PostgreSQL.
- LLM vẫn bị giới hạn ở node diễn đạt; hard facts do code quyết định.

## Hệ quả

- Thêm dependency LangGraph và checkpoint PostgreSQL.
- Cần `thread_id` duy nhất cho mọi run.
- State chứa Pydantic models nên serializer phải có allowlist rõ ràng.
- Review queue dùng PostgreSQL trong deploy; memory backend chỉ dành cho test/local.
