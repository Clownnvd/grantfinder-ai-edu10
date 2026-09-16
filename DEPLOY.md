# Deploy GrantFinder AI

## Thành phần

1. PostgreSQL có extension pgvector.
2. FastAPI BFF từ thư mục gốc.
3. Next.js frontend từ `frontend/`.

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
- Optional Gemini: `USE_LLM=1`, `GEMINI_API_KEY`, `GEMINI_MODEL`

Kiểm tra `/health` phải trả `service=grantfinder-bff` và `open_opportunities=968`.

## Frontend

- Root: `frontend`
- Build: `pnpm install --frozen-lockfile && pnpm build`
- Start: `pnpm start`
- Build-time env: `NEXT_PUBLIC_BFF_URL=https://<backend-domain>`

## Secret hygiene

Không commit `.env`, database URL production hoặc Gemini key. Demo chỉ dùng dữ liệu công khai/mô phỏng.
