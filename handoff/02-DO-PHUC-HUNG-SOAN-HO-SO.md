# Bản 02 — Đỗ Phúc Hưng — Soạn hồ sơ/proposal

## 1. Mục tiêu

Sau khi nhà nghiên cứu chọn một cơ hội, màn soạn hồ sơ phải buộc họ kiểm tra nguồn, xác nhận lựa chọn, tạo draft có citation, bổ sung phần còn thiếu và gửi phòng KHCN duyệt. Hệ thống không tự nộp proposal.

## 2. Phạm vi file

- Chính: `frontend/components/ProposalWorkspace.tsx`.
- Có thể tách tiếp khi mở rộng:
  - `frontend/components/ConfirmationGate.tsx`
  - `frontend/components/DraftSections.tsx`
- API:
  - `POST /api/v1/proposals/draft`
  - `POST /api/v1/reviews`
  - `GET /api/v1/reviews`
- Không sửa matching/rerank.

## 3. Thành phần nhỏ nhất

### 3.1 Selected opportunity summary

- Source, title, issuer, deadline.
- Link mở nguồn gốc.
- Nhãn eligibility sơ bộ.
- Cảnh báo không phải quyết định đủ điều kiện cuối cùng.

### 3.2 Research question editor

- Textarea bắt buộc, tối thiểu 5 ký tự.
- Không tự thay câu hỏi khi user đã sửa.
- Giữ nội dung sau lỗi API.

### 3.3 Confirmation gate

- Checkbox xác nhận đúng cơ hội.
- Nút draft bị khóa nếu chưa xác nhận.
- Giải thích rõ draft vẫn cần phòng KHCN duyệt.

### 3.4 Draft sections

- Banner `[DRAFT_ONLY]`.
- Tám section theo template.
- Field thiếu giữ `[NEEDS_INPUT]`.
- Citation/source span.
- Không cho hiểu nhầm đây là hồ sơ đã nộp.

### 3.5 Send-to-review

- Nút gửi phòng KHCN.
- Loading khi gửi.
- Success message và review ID.
- Tránh gửi trùng khi double-click.

### 3.6 Revision loop

- Manager approve → khóa phiên bản đã duyệt, hiện thời điểm và ghi chú.
- Manager từ chối/yêu cầu sửa → hiện ghi chú, mở lại section cần sửa.
- Researcher sửa → tạo version mới hoặc resend cùng draft với audit.

## 4. Luồng chi tiết

### Luồng A — Chưa chọn cơ hội

1. User mở tab draft trực tiếp.
2. Hiện empty state “Chưa chọn cơ hội”.
3. Nút quay lại “Khám phá cơ hội”.
4. Không hiển thị checkbox hoặc nút tạo draft.
5. Không gửi API với opportunity ID rỗng.

### Luồng B — Đã chọn nhưng chưa xác nhận

1. Hiện đầy đủ summary và nguồn.
2. Checkbox mặc định chưa chọn.
3. Nút tạo draft disabled.
4. Nếu cố gọi API thủ công, backend trả HTTP 409.
5. UI dịch lỗi 409 thành hướng dẫn xác nhận, không hiện JSON thô.

### Luồng C — Xác nhận rồi tạo draft thành công

1. User mở source và kiểm tra.
2. User nhập câu hỏi nghiên cứu.
3. User tích xác nhận.
4. Nút bật; bấm một lần.
5. UI chuyển loading, khóa checkbox/nút.
6. LangGraph chạy:
   - `load_grounded_opportunity`
   - `check_researcher_confirmation`
   - `build_proposal_draft`
   - `optional_grounded_llm_rewrite`
   - `validate_draft_output`
   - `request_research_office_review`
7. Hiện banner và sections.
8. Trace dừng ở `waiting_for_human`.

### Luồng D — Gemini tắt hoặc lỗi

1. `llm_info.mode` là `deterministic_template` hoặc `deterministic_fallback`.
2. Draft vẫn hiển thị đầy đủ template.
3. Hiện nhãn “Bản nháp tất định”.
4. Không báo tác vụ thất bại nếu guard pass.
5. Không tự gọi lại Gemini liên tục.

### Luồng E — Output guard từ chối

1. `validate_draft_output` phát hiện section rỗng hoặc thiếu citation.
2. Graph chuyển `draft_failed`.
3. API không trả draft dùng được.
4. UI hiện “Bản nháp bị chặn vì thiếu căn cứ”.
5. Cho phép quay lại cơ hội hoặc thử lại sau khi dữ liệu được sửa.
6. Không hiển thị output bị guard chặn như kết quả hợp lệ.

### Luồng F — Gửi review thành công

1. User đọc draft và bấm gửi.
2. Disable nút ngay khi request bắt đầu.
3. API tạo `review_id`, status `pending`.
4. Hiện success message.
5. Có nút chuyển sang “Hàng chờ phê duyệt”.
6. Không gửi lần hai nếu draft đã có review pending.

### Luồng G — Manager phê duyệt

1. Manager mở review pending.
2. Mở lại source và draft.
3. Bấm “Phê duyệt”.
4. Hiện hộp xác nhận cuối: hành động ghi trạng thái.
5. Gửi `approved=true` và ghi chú.
6. Response status `approved`.
7. UI thay nút bằng badge “Đã phê duyệt”.
8. Hiện thời điểm, người duyệt và ghi chú.

### Luồng H — Manager từ chối/yêu cầu sửa

1. Manager bấm “Yêu cầu sửa”.
2. Bắt buộc nhập lý do; không cho gửi lý do rỗng.
3. Gửi `approved=false`.
4. Response status `changes_requested`.
5. Researcher nhìn thấy ghi chú ở đầu draft.
6. Section liên quan được đánh dấu cần sửa.
7. User sửa và gửi lại.
8. Lịch sử không xóa bản cũ.

### Luồng I — Opportunity hết hạn trong lúc soạn

1. Trước khi gửi review, backend kiểm tra deadline mới nhất.
2. Nếu đã hết hạn, chặn gửi và trả mã lỗi rõ ràng.
3. UI hiện banner đỏ và link nguồn.
4. Cho phép lưu nội dung làm bản nháp cá nhân nhưng không đưa vào queue nộp.

## 5. Test case bắt buộc

1. Draft tab không có selection.
2. Chưa confirm → button disabled.
3. Gọi API chưa confirm → 409.
4. Question dưới 5 ký tự → không gửi.
5. Draft success → đủ section/citation/banner.
6. LLM off → deterministic template.
7. LLM lỗi → fallback không crash.
8. Guard fail → không hiển thị output như success.
9. Gửi review → pending.
10. Double-click → chỉ một review.
11. Manager approve → approved.
12. Manager reject không lý do → validation fail.
13. Manager reject có lý do → changes_requested.
14. Researcher không được gọi decision endpoint → 403.

## 6. Definition of Done

- [ ] Empty state khi chưa chọn cơ hội.
- [ ] Source summary khớp lựa chọn từ màn chính.
- [ ] Confirmation gate chặn đúng.
- [ ] Draft có banner, citations và `[NEEDS_INPUT]`.
- [ ] Hiện đủ 6 node LangGraph trong trace.
- [ ] LLM fallback được diễn giải đúng.
- [ ] Guard fail không rò output không hợp lệ.
- [ ] Gửi review có loading, success và chống duplicate.
- [ ] Approve và reject có confirmation.
- [ ] Reject bắt buộc lý do và tạo vòng sửa.
- [ ] Role gate 403 được xử lý thân thiện.
- [ ] Không có nút tự nộp hồ sơ.
- [ ] Typecheck/lint/build pass.
- [ ] Có ảnh: unconfirmed, draft success, changes requested.

## 7. Các bước làm nhỏ nhất

1. Tạo branch `feature/hung-proposal-workspace`.
2. Tách component summary.
3. Tách confirmation gate.
4. Tách section renderer.
5. Xử lý HTTP 409.
6. Thêm trạng thái LLM fallback.
7. Thêm trạng thái guard fail.
8. Chống double submit.
9. Thêm approve confirmation.
10. Thêm reject modal + required reason.
11. Thêm revision banner.
12. Test role gate.
13. Chụp ba ảnh.
14. Commit và push.

```powershell
git checkout -b feature/hung-proposal-workspace
cd frontend
pnpm typecheck
pnpm lint
pnpm build
cd ..
python -m grantfinder.test_api
git add frontend grantfinder bff
git commit -m "feat: complete proposal drafting and revision flow"
git push -u origin feature/hung-proposal-workspace
```
