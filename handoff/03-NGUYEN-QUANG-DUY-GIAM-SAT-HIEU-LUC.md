# Bản 03 — Nguyễn Quang Duy — Giám sát hiệu lực

## 1. Mục tiêu

Cho phép nhóm nghiên cứu và phòng KHCN biết call nào còn hiệu lực, sắp đóng, đã hết hạn hoặc thiếu deadline cần xác minh; mọi trạng thái phải dựa trên ngày và URL nguồn.

## 2. Phạm vi file

- Frontend: `frontend/components/MonitoringView.tsx`.
- API client/type:
  - `frontend/lib/grant-api.ts`
  - `frontend/lib/grant-types.ts`
- Backend: `GET /api/v1/monitoring` trong `bff/grant_main.py`.
- Test: `grantfinder/test_api.py` hoặc file test monitoring riêng.
- Không sửa matching score.

## 3. Thành phần nhỏ nhất

### 3.1 Summary cards

- Còn hiệu lực.
- Sắp hết hạn trong 30 ngày.
- Hết hiệu lực.
- Cần xác minh vì thiếu deadline.

### 3.2 Monitoring table/list

- Status badge.
- Title.
- Source + source ID.
- Close date.
- Link mở nguồn.
- Sắp xếp ưu tiên: sắp hết hạn → cần xác minh → còn hiệu lực → hết hạn.

### 3.3 Filter/search

- Filter theo status.
- Filter theo source.
- Search title/source ID.
- Nút xóa filter.

### 3.4 Source sync state

- Lần kiểm tra gần nhất.
- Snapshot date.
- Loading.
- Đồng bộ thành công.
- Đồng bộ lỗi/nguồn không phản hồi.

## 4. Quy tắc trạng thái

Với ngày hiện tại `today`:

- `close_date` rỗng → `needs_review`.
- `close_date < today` → `expired`.
- `today <= close_date <= today + 30 ngày` → `closing_soon`.
- `close_date > today + 30 ngày` → `active`.

Không dùng LLM để suy luận deadline.

## 5. Luồng chi tiết

### Luồng A — Tải thành công

1. Mở tab giám sát.
2. Gọi `GET /api/v1/monitoring`.
3. Hiện skeleton cho card và list.
4. Nhận counts, items, checked_at và snapshot_date.
5. Render bốn card.
6. Render danh sách đã sort.
7. Tắt loading.

### Luồng B — Call còn hiệu lực

1. `close_date` cách hiện tại trên 30 ngày.
2. Gắn badge xanh “Còn hiệu lực”.
3. Call vẫn được phép tham gia matching.
4. Source link luôn hiển thị nếu có URL.

### Luồng C — Call sắp hết hạn

1. `close_date` trong 30 ngày.
2. Gắn badge vàng “Sắp hết hạn”.
3. Đưa lên đầu danh sách.
4. Hiện số ngày còn lại.
5. Nếu còn ≤7 ngày, dùng cảnh báo mạnh hơn nhưng vẫn không tuyên bố đã hết hạn.

### Luồng D — Call hết hiệu lực

1. `close_date` nhỏ hơn ngày hiện tại.
2. Gắn badge đỏ “Hết hiệu lực”.
3. Không đưa call vào matching mới.
4. Không xóa record; giữ để audit/lịch sử.
5. Nếu user đang có draft từ call này, thông báo và chặn gửi review mới.

### Luồng E — Thiếu deadline

1. `close_date=null`.
2. Gắn badge xám “Cần xác minh”.
3. Không tự đoán ngày.
4. Nút mở nguồn nổi bật.
5. Manager có thể đánh dấu đã kiểm tra, nhưng phải lưu URL/ghi chú.

### Luồng F — Người dùng xác nhận trạng thái đúng

1. Mở nguồn.
2. Bấm “Xác nhận đã kiểm tra”.
3. Hộp thoại hiển thị source ID, URL và trạng thái chuẩn bị ghi.
4. User bấm xác nhận.
5. Lưu actor, timestamp và ghi chú.
6. UI hiện badge “Đã kiểm tra thủ công”.

### Luồng G — Người dùng từ chối trạng thái do hệ thống tính

1. Bấm “Báo trạng thái chưa đúng”.
2. Bắt buộc chọn lý do:
   - nguồn đã gia hạn;
   - nguồn đã đóng sớm;
   - deadline trong trang/PDF khác metadata;
   - URL lỗi;
   - lý do khác.
3. Bắt buộc nhập URL hoặc ghi chú bằng chứng.
4. Không sửa thẳng hard field từ frontend.
5. Tạo review item `status_dispute` cho manager.
6. Trong lúc chờ, gắn `needs_review` và không khẳng định active/expired.
7. Manager duyệt → cập nhật snapshot kế tiếp.
8. Manager từ chối dispute → giữ trạng thái cũ và lưu lý do.

### Luồng H — Nguồn gia hạn deadline

1. Sync phát hiện cùng source ID nhưng close date mới.
2. Không tạo duplicate.
3. Cập nhật record, document hash và updated_at.
4. Ghi diff `old_close_date → new_close_date`.
5. Chuyển status theo ngày mới.
6. Thông báo các draft liên quan.

### Luồng I — API monitoring lỗi

1. Hiện error state trong khu vực monitoring.
2. Không thay counts bằng 0 vì dễ hiểu nhầm.
3. Giữ dữ liệu lần tải trước nếu có và gắn “Có thể đã cũ”.
4. Có nút thử lại.
5. Không làm hỏng các tab khác.

### Luồng J — Filter không có kết quả

1. Hiện empty state theo filter.
2. Hiện nút xóa filter.
3. Không nói corpus không có dữ liệu nếu chỉ vì filter.

## 6. API response tối thiểu

```json
{
  "checked_at": "2026-09-17",
  "snapshot_date": "2026-09-15",
  "counts": {
    "active": 900,
    "closing_soon": 50,
    "expired": 0,
    "needs_review": 18
  },
  "items": [],
  "limitations": "Corpus chính chỉ chứa call đang mở tại snapshot..."
}
```

Số trên chỉ là ví dụ schema. UI phải dùng response thật, không hardcode.

## 7. Test case bắt buộc

1. Deadline >30 ngày → active.
2. Deadline đúng 30 ngày → closing_soon.
3. Deadline hôm nay → closing_soon.
4. Deadline hôm qua → expired.
5. Deadline null → needs_review.
6. Tổng counts bằng tổng corpus.
7. Sort closing soon lên trước.
8. Mở source đúng URL.
9. API lỗi → không hiện counts 0 giả.
10. Filter rỗng → empty theo filter.
11. Dispute thiếu lý do → không gửi.
12. Dispute bị từ chối → status gốc giữ nguyên.

## 8. Definition of Done

- [ ] Bốn status dùng quy tắc ngày tất định.
- [ ] Card counts lấy từ API.
- [ ] List sort đúng ưu tiên.
- [ ] Có source ID, URL và close date.
- [ ] Có loading, success, stale/error và filtered-empty.
- [ ] Có flow xác nhận thủ công.
- [ ] Có flow báo sai/từ chối trạng thái.
- [ ] Không sửa hard field trực tiếp từ client.
- [ ] Expired call không đi vào matching mới.
- [ ] Responsive và keyboard accessible.
- [ ] API test đủ boundary ngày.
- [ ] Typecheck/lint/build pass.
- [ ] Có screenshot overview và dispute state.

## 9. Các bước làm nhỏ nhất

1. Tạo branch `feature/quangduy-deadline-monitor`.
2. Viết helper phân loại ngày và unit test.
3. Hoàn thiện endpoint monitoring.
4. Hoàn thiện types/API client.
5. Dựng summary cards.
6. Dựng list/table.
7. Thêm filter/search.
8. Thêm loading/error/stale.
9. Thêm confirmation/dispute dialog.
10. Test boundary ngày.
11. Test responsive.
12. Chụp ảnh.
13. Commit và push.

```powershell
git checkout -b feature/quangduy-deadline-monitor
python -m grantfinder.test_api
cd frontend
pnpm typecheck
pnpm lint
pnpm build
cd ..
git add bff grantfinder frontend/components/MonitoringView.tsx frontend/lib
git commit -m "feat: add grounded deadline monitoring flow"
git push -u origin feature/quangduy-deadline-monitor
```
