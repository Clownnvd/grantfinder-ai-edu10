# Evaluation Evidence

## Cách tái lập

```powershell
$env:USE_PGVECTOR='0'
$env:USE_LLM='0'
python -m grantfinder.test_core
python -m grantfinder.test_api
python -m grantfinder.test_langgraph
python -m grantfinder.eval
```

## Kết quả gần nhất

| Metric | Kết quả | Ngưỡng |
|---|---:|---:|
| Recall@3 | 0,80 | ≥0,80 |
| Citation coverage | 1,00 | 1,00 |
| Provider error cases | 0 | 0 |

Median latency thay đổi theo máy và retrieval backend; số chính xác nằm trong `artifacts/eval/grantfinder_eval.json` được sinh lại sau mỗi lần chạy.

## Bằng chứng LangGraph

- Hai compiled graph: matching và drafting.
- Conditional edge cho no-grounding, confirmation và output guard.
- Checkpoint có `thread_id` và `checkpoint_id`.
- Tool trace kết thúc ở `waiting_for_human` tại cả hai cổng duyệt.

## Giới hạn

- Gold set mới có 10 query; cần mở rộng trước pilot.
- Chưa có user study để khẳng định giảm ≥50% thời gian.
- Hash embedding chỉ là fallback tái lập; production phải đánh giá embedding đa ngôn ngữ trên cùng gold set.
