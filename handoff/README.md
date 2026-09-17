# Handoff — 4 phần việc wireframe GrantFinder AI

## Phân công cố định

| Gói | Người phụ trách | Phần việc |
|---|---|---|
| 01 | Nguyễn Văn Duy | Màn chính — Khám phá cơ hội |
| 02 | Đỗ Phúc Hưng | Soạn hồ sơ/proposal và vòng sửa |
| 03 | Nguyễn Quang Duy | Giám sát call còn hiệu lực/hết hiệu lực |
| 04 | Dương Thị Ngân | Đăng nhập, đăng ký và trạng thái tài khoản |

## Quy tắc làm việc

1. Mỗi người tạo branch riêng theo hướng dẫn trong bản của mình.
2. Chỉ sửa file thuộc phạm vi; nếu cần sửa file chung, báo nhóm trưởng trước khi commit.
3. Mỗi trạng thái giao diện phải có dữ liệu mock hoặc API response để tái hiện.
4. Không dùng API key thật, mật khẩu thật hoặc dữ liệu cá nhân thật.
5. Chạy typecheck, lint và build trước khi push.
6. Mỗi người tự commit bằng GitHub của mình; không nhờ người khác commit hộ.
7. PR phải kèm ít nhất một ảnh và checklist DoD đã tích.

## Thứ tự merge

1. Nguyễn Quang Duy — component giám sát độc lập.
2. Dương Thị Ngân — component tài khoản độc lập.
3. Đỗ Phúc Hưng — draft flow và vòng sửa.
4. Nguyễn Văn Duy — màn chính, ghép navigation và integration cuối.

## Kiểm tra tích hợp sau merge

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm typecheck
pnpm lint
pnpm build
cd ..
$env:USE_PGVECTOR='0'
$env:USE_LLM='0'
$env:LANGGRAPH_STRICT_MSGPACK='true'
$env:REVIEW_STORE_BACKEND='memory'
python -m grantfinder.test_core
python -m grantfinder.test_api
python -m grantfinder.test_langgraph
```
