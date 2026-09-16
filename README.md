# GrantFinder AI

> Đề số 10 · AI20K Build Phase Cohort 4 · đội kingpro

GrantFinder AI giúp nhà nghiên cứu tìm cơ hội tài trợ phù hợp, kiểm tra eligibility sơ bộ, xem căn cứ gốc và dựng proposal theo một workflow có Human-in-the-loop. Hard facts như deadline, ngân sách và điều kiện không do LLM tự tạo.

## Dành cho học tập

Repo public này là bản MVP của đề **EDU-10** để các nhóm khác có thể học cách xây một agent source-first: ingest dữ liệu công khai, hybrid retrieval, rule-based eligibility, citation, eval và hai cổng Human-in-the-loop. Mã nguồn dùng giấy phép MIT. Snapshot dữ liệu đi kèm chỉ phục vụ tái lập demo; khi làm sản phẩm thật cần kiểm tra lại điều khoản và độ mới của từng nguồn.

## Trạng thái chạy được

- 968 cơ hội mở trong snapshot 15/09/2026: 965 Grants.gov + 3 NAFOSTED đã kiểm tra nguồn.
- PostgreSQL 16 + pgvector đã nạp đủ 968 bản ghi.
- Hybrid retrieval: PostgreSQL full-text/BM25 signal + cosine pgvector + eligibility rules + rerank.
- Hai vai trò: `researcher` và `research_manager`.
- Agent trace có trạng thái và tool-use.
- Draft bắt buộc nhà nghiên cứu xác nhận; sau đó tiếp tục chờ phòng KHCN duyệt.
- Gemini chỉ diễn đạt draft khi bật; lỗi/key trống tự lùi về template tất định.
- Benchmark pgvector hiện tại: Recall@3 = 0,80; citation coverage = 1,00; median latency ≈120 ms. Thời gian tiết kiệm chưa được công bố vì chưa đo người dùng thật.

## Demo flow

1. Vai trò **Nhà nghiên cứu** nhập hướng nghiên cứu, từ khóa, thời lượng và ngân sách.
2. Agent chạy `search_opportunities → check_eligibility → rerank_candidates`.
3. Hệ thống trả top 3, score breakdown, deadline, funding, source URL và source span.
4. Nhà nghiên cứu chọn cơ hội và xác nhận đúng payload trước khi tạo draft.
5. Agent dựng bản `[DRAFT_ONLY]`, giữ `[NEEDS_INPUT]` cho dữ liệu chưa có.
6. Nhà nghiên cứu gửi review; vai trò **Quản lý phòng KHCN** phê duyệt hoặc yêu cầu sửa.
7. Hệ thống không có chức năng tự nộp hồ sơ.

## Kiến trúc

```mermaid
flowchart LR
  R[Researcher] --> UI[Next.js 16]
  M[Research manager] --> UI
  UI --> API[FastAPI BFF]
  API --> WF[Stateful grant workflow]
  WF --> S[search_opportunities]
  S --> PG[(PostgreSQL + pgvector)]
  WF --> E[deterministic eligibility]
  WF --> RR[reranker]
  WF --> H1[Researcher confirmation]
  H1 --> D[proposal draft]
  D -. optional .-> G[Gemini grounded rewrite]
  G --> NG[number/output guard]
  D --> H2[Research-office review]
  PG --> SRC[Grants.gov + NAFOSTED]
```

Nguyên tắc kế thừa từ Policy Radar: code quyết định hard facts và guard; LLM chỉ xử lý ngôn ngữ, bị kiểm tra trước khi output được sử dụng.

## Nguồn dữ liệu

| Nguồn | Vai trò | Phương thức |
|---|---|---|
| Grants.gov | Cơ hội quốc tế đang mở | Daily XML bulk + public API |
| NAFOSTED | Cơ hội Việt Nam | Public WordPress REST + source audit |
| OpenAlex | Hồ sơ công bố nhà nghiên cứu | REST on demand, giai đoạn tiếp theo |
| CORDIS | Dự án EU đã được tài trợ | Bulk CSV/JSON, giai đoạn tiếp theo |
| VBPL | Quy định được call Việt Nam dẫn chiếu | Compliance/citation layer |

Dữ liệu mẫu có URL gốc, source ID, snapshot date và source spans. NAFOSTED chỉ đánh dấu `open` sau khi deadline được kiểm tra; các bài chưa review không được đưa vào 3 cơ hội mở.

## Chạy local

Yêu cầu: Python 3.11, Node 22, pnpm 9, Docker Desktop.

```powershell
# 1. PostgreSQL + pgvector
docker compose up -d
python -m pip install -r requirements.txt
python scripts/init_pgvector.py
python scripts/ingest_grants_pgvector.py

# 2. Backend
$env:USE_PGVECTOR='1'
$env:DATABASE_URL='postgresql://grantfinder:grantfinder_local@127.0.0.1:54329/grantfinder'
python -m uvicorn bff.grant_main:app --host 127.0.0.1 --port 8000

# 3. Frontend
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

Mở `http://127.0.0.1:3002`.

## Gemini tùy chọn

Core matching, eligibility, pgvector và draft template không cần LLM. Để Gemini viết lại phần diễn đạt:

```text
USE_LLM=1
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.7-flash
```

Không đưa key vào Git. Nếu Gemini lỗi, draft deterministic vẫn chạy và trace ghi rõ fallback.

## API chính

| Method | Endpoint | Tác dụng |
|---|---|---|
| GET | `/health` | trạng thái và số opportunity |
| GET | `/api/v1/sources` | dữ liệu, deadline gần nhất, retrieval mode |
| POST | `/api/v1/match` | chạy workflow tìm top 3 |
| POST | `/api/v1/proposals/draft` | tạo draft sau researcher confirmation |
| POST | `/api/v1/reviews` | gửi phòng KHCN duyệt |
| POST | `/api/v1/reviews/{id}/decision` | manager approve/request changes |
| GET | `/api/v1/evaluation` | metric có artifact; không có thì nói chưa chạy |

## Kiểm thử

```powershell
python -m grantfinder.test_core
python -m grantfinder.eval
python -m grantfinder.test_pgvector
cd frontend
pnpm typecheck
pnpm build
```

CI dựng pgvector service, ingest lại dữ liệu, chạy core/eval/pgvector và build frontend.

## Mapping yêu cầu đề

- Web app deploy: Next.js + FastAPI, cấu hình Docker/Railway.
- ≥2 vai trò: researcher và research manager.
- Agentic workflow có state/tool-use: trace bốn bước và checkpoint.
- HITL: xác nhận trước draft và phê duyệt của phòng KHCN.
- Error/limit: provider fallback, role gate, source audit, không tự submit.
- Dữ liệu: công khai, snapshot có provenance; không chứa CV/dữ liệu nhạy cảm thật.
- Eval: retrieval, citation coverage, latency, failure cases; không bịa time saving.
- Hồ sơ bàn giao: source, setup, schema DB, sample data, architecture, CI, eval artifact và demo guide.

## Giới hạn được công bố

- 80% Recall@3 mới là benchmark kỹ thuật 10 query; cần mở rộng gold set và đánh giá chuyên gia.
- Eligibility trả `needs_review` khi thiếu căn cứ; không coi semantic match là đủ điều kiện.
- Local vector hiện là hash embedding 256 chiều để tái lập không cần key. Trước production cần đánh giá multilingual embedding riêng trên cùng gold set.
- Chưa đo giảm ≥50% thời gian với người dùng thật.
- Review queue hiện lưu trong memory cho demo; schema PostgreSQL đã có để chuyển sang persistence.
- Chưa tự động cập nhật hàng ngày trong bản MVP; source sync sẽ chạy theo lịch ở giai đoạn tiếp theo.

## Đội

- Nguyễn Văn Duy — nhóm trưởng
- Đỗ Phúc Hưng
- Dương Thị Ngân
- Nguyễn Quang Duy

Bổ sung MSSV, GitHub và contribution thật trong `TEAMMATES.md` trước khi nộp.
