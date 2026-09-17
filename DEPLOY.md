# Deploy GrantFinder AI

## Thành phần

1. PostgreSQL có extension pgvector.
2. FastAPI BFF từ thư mục gốc.
3. Next.js frontend từ `frontend/`.

## Chạy đủ stack bằng Docker

```powershell
docker compose -f docker-compose.full.yml up --build
```

Frontend ở `http://127.0.0.1:3002`, API ở `http://127.0.0.1:8000`.

## PostgreSQL

Tạo database PostgreSQL 16 trên Railway/Supabase/Neon có hỗ trợ `CREATE EXTENSION vector`, sau đó:

```powershell
$env:DATABASE_URL='<postgres-url>'
python scripts/init_pgvector.py --database-url $env:DATABASE_URL
python scripts/ingest_grants_pgvector.py --database-url $env:DATABASE_URL
```

## Backend Railway

- Root: `.`
- Build: `pip install -r requirements.txt`
- Start: đọc `Procfile`
- Env: `DATABASE_URL`, `USE_PGVECTOR=1`, `USE_LLM=0`
- LangGraph production: `LANGGRAPH_CHECKPOINT_BACKEND=postgres`, `LANGGRAPH_CHECKPOINT_DATABASE_URL=<postgres-url>`, `LANGGRAPH_STRICT_MSGPACK=true`
- Review queue production: `REVIEW_STORE_BACKEND=postgres`
- Optional Gemini: `USE_LLM=1`, `GEMINI_API_KEY`, `GEMINI_MODEL`

Kiểm tra `/health` phải trả `service=grantfinder-bff`, `open_opportunities=968`, `orchestration=langgraph` và `checkpointing=postgres`.

Sau một lần match, gọi `/api/v1/graph/runs/{run_id}` và xác nhận response có `checkpoint_id`.

## Frontend

- Root: `frontend`
- Build: `pnpm install --frozen-lockfile && pnpm build`
- Start: `pnpm start`
- Build-time env: `NEXT_PUBLIC_BFF_URL=https://<backend-domain>`

## Secret hygiene

Không commit `.env`, database URL production hoặc Gemini key. Demo chỉ dùng dữ liệu công khai/mô phỏng.
