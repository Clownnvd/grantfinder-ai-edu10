# AI Log Setup

## Ba lớp log

1. **LangGraph checkpoint:** lưu state sau mỗi superstep bằng `thread_id`.
2. **Tool trace:** API trả node/tool, input summary, output summary, trạng thái, latency và lỗi.
3. **Agent audit:** `artifacts/audit/agent_runs.jsonl` ghi run, graph, node, trạng thái và latency; không lưu nội dung nghiên cứu.
4. **LLM audit:** `artifacts/audit/llm_calls.jsonl` chỉ ghi metadata; không ghi API key.

## Local

```text
LANGGRAPH_CHECKPOINT_BACKEND=memory
LANGGRAPH_STRICT_MSGPACK=true
USE_LLM=0
```

Sau một lần gọi `/api/v1/match`, kiểm tra checkpoint:

```http
GET /api/v1/graph/runs/{run_id}
```

Response phải có `checkpoint_id`, `status`, `top_ids` và `tool_trace`.

## Production

```text
LANGGRAPH_CHECKPOINT_BACKEND=postgres
LANGGRAPH_CHECKPOINT_DATABASE_URL=postgresql://...
LANGGRAPH_STRICT_MSGPACK=true
```

Không commit URL production hoặc key. `PostgresSaver.setup()` tự tạo bảng checkpoint ở lần khởi động đầu.

## LangSmith tùy chọn

Theo sổ tay Phoenix, có thể bật tracing bằng biến môi trường:

```text
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=grantfinder-ai-edu10
LANGCHAIN_TRACING_V2=true
```

## Phoenix AI Logs

- Tạo Phoenix API key ở trang **API Keys** bằng tài khoản từng thành viên.
- Mỗi thành viên tự ghi log thật trong quá trình làm việc; không dùng chung key.
- Không đưa Phoenix key vào repo, screenshot hoặc output CI.
- Đối chiếu số log tại trang **AI Logs** trước checkpoint/Demo Day.
