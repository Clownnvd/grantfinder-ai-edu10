# Bản 01 — Nguyễn Văn Duy — Màn chính/Khám phá cơ hội

## 1. Mục tiêu

Cho phép một nhà nghiên cứu nhập hồ sơ tối thiểu, chạy LangGraph matching, hiểu vì sao từng cơ hội phù hợp và chọn đúng một cơ hội để chuyển sang soạn hồ sơ.

## 2. Phạm vi file

- Chính: `frontend/components/GrantFinderApp.tsx`.
- Component liên quan:
  - `frontend/components/GrantSidebar.tsx`
  - `frontend/components/GrantChatInput.tsx`
  - `frontend/components/GrantChatMessage.tsx`
  - `frontend/components/ResearchProfilePanel.tsx`
  - `frontend/components/GrantOpportunityCard.tsx`
  - `frontend/components/AgentTrace.tsx`
- API đã có: `POST /api/v1/match`.
- Không sửa logic eligibility trong `grantfinder/catalog.py` nếu chưa thống nhất với nhóm.

## 3. Thành phần nhỏ nhất

### 3.1 Header

- Logo/tên sản phẩm.
- Tên màn: “Tìm quỹ phù hợp”.
- Bộ chọn vai trò.
- Trên mobile phải có cách mở navigation.

### 3.2 Form hồ sơ nghiên cứu

- Hướng nghiên cứu — bắt buộc, tối thiểu 3 ký tự.
- Từ khóa — danh sách, tách bằng dấu phẩy.
- Giai đoạn nghề nghiệp.
- Thời lượng dự án — 1 đến 120 tháng.
- Ngân sách — số không âm.
- Nút “Tìm 3 cơ hội phù hợp”.

### 3.3 Khu vực shortlist

- Trạng thái chưa chạy.
- Loading khi agent đang chạy.
- Tối đa 3 `OpportunityCard`.
- Mỗi thẻ có:
  - nguồn;
  - verdict eligibility;
  - tổng điểm;
  - tiêu đề/cơ quan;
  - deadline;
  - trần tài trợ;
  - quốc gia;
  - matched terms;
  - score breakdown BM25/vector/eligibility;
  - source span;
  - nút mở nguồn;
  - nút chọn cơ hội.

### 3.4 Agent trace

- Badge `LangGraph`.
- Từng node theo thứ tự:
  1. `search_opportunities`
  2. `check_eligibility`
  3. `rerank_candidates`
  4. `request_human_review`
- Hiện trạng thái, latency và lỗi/fallback nếu có.

## 4. Luồng chi tiết

### Luồng A — Vào màn lần đầu

1. Gọi `GET /api/v1/sources`.
2. Điền profile mẫu không chứa dữ liệu thật.
3. Hiện empty state “Chạy matching để bắt đầu”.
4. Agent trace hiển thị hướng dẫn, chưa có node.
5. Nút tìm kiếm chỉ bật khi hướng nghiên cứu hợp lệ.

### Luồng B — Validation thất bại

1. Người dùng xóa hướng nghiên cứu hoặc nhập dưới 3 ký tự.
2. Nút tìm kiếm bị vô hiệu hóa.
3. Hiện trợ giúp ngay dưới field, không gửi request.
4. Nếu tháng ngoài 1–120 hoặc ngân sách âm, giữ focus tại field lỗi.
5. Không xóa dữ liệu hợp lệ ở field khác.

### Luồng C — Matching thành công

1. Người dùng bấm tìm kiếm.
2. Khóa nút và đổi nhãn thành “Agent đang chạy…”.
3. Gửi role, profile và `top_k=3`.
4. Nhận response có `orchestration=langgraph`.
5. Hiện 1–3 kết quả đúng thứ tự score.
6. Chọn sẵn thẻ đầu về mặt state nhưng chưa tự chuyển màn.
7. Trace kết thúc ở `request_human_review` với `waiting_for_human`.
8. Người dùng vẫn phải chủ động bấm “Chọn cơ hội này”.

### Luồng D — Người dùng chọn cơ hội

1. Bấm “Chọn cơ hội này”.
2. Lưu toàn bộ `MatchItem`, không chỉ ID.
3. Chuyển tab `draft`.
4. Draft screen hiện đúng title, source và deadline của thẻ đã chọn.
5. Nếu quay lại, thẻ đã chọn có viền/ring rõ ràng.

### Luồng E — Người dùng mở nguồn

1. Bấm “Kiểm tra nguồn”.
2. Mở `canonical_url` ở tab mới.
3. Không kích hoạt hành động chọn thẻ.
4. Nếu URL trống, ẩn nút và hiện “Chưa có URL kiểm chứng”.

### Luồng F — Không tìm thấy căn cứ

1. API trả `state=needs_profile_refinement`, `top_matches=[]`.
2. Không render thẻ giả.
3. Hiện gợi ý: bổ sung từ khóa, lĩnh vực hoặc phạm vi.
4. Giữ nguyên form để người dùng sửa.
5. Trace hiển thị `handle_no_results` và lý do.

### Luồng G — pgvector lỗi nhưng fallback thành công

1. Response vẫn có shortlist.
2. `search_opportunities.output_summary.warning` có cảnh báo.
3. Hiện banner nhẹ “Đang dùng tìm kiếm dự phòng”.
4. Không hiển thị lỗi đỏ vì tác vụ vẫn hoàn thành.
5. Không gọi lại tự động vô hạn.

### Luồng H — Backend lỗi hoàn toàn

1. Mở banner lỗi phía trên nội dung.
2. Giữ dữ liệu form.
3. Mở lại nút “Thử lại”.
4. Không giữ kết quả cũ dưới trạng thái loading mới.
5. Không hiển thị stack trace hoặc secret.

## 5. API contract cần kiểm tra

```json
{
  "role": "researcher",
  "profile": {
    "research_interests": "artificial intelligence in education",
    "keywords": ["machine learning"],
    "career_stage": "faculty",
    "institution_type": "private_university",
    "country": "Vietnam",
    "requested_budget": 200000,
    "project_duration_months": 24
  },
  "top_k": 3
}
```

Response tối thiểu: `run_id`, `state`, `top_matches`, `tool_trace`, `limitations`, `orchestration`, `graph_nodes`.

## 6. Test case bắt buộc

1. Hướng nghiên cứu rỗng → không gửi API.
2. Nhập hợp lệ → hiện đúng 3 thẻ.
3. Mỗi thẻ có citation và URL.
4. Chọn thẻ số 2 → draft nhận đúng thẻ số 2.
5. Mở nguồn → tab mới, không đổi lựa chọn.
6. Response rỗng → hiện no-grounding.
7. API 500 → form không mất dữ liệu.
8. pgvector fallback → cảnh báo, vẫn dùng được.
9. Màn 390px không tràn ngang.
10. Keyboard tab tới được mọi input và button.

## 7. Definition of Done

- [ ] Form có label, validation và trạng thái disabled/loading.
- [ ] Không gửi request khi dữ liệu không hợp lệ.
- [ ] Hiện tối đa 3 kết quả, không tự bịa kết quả.
- [ ] Mỗi hard fact có source hoặc nhãn cần xác minh.
- [ ] Trace thể hiện đúng 4 node LangGraph.
- [ ] Có đủ empty, success, no-grounding, fallback và hard-error.
- [ ] Chọn cơ hội chuyển đúng sang draft.
- [ ] Responsive desktop/tablet/mobile.
- [ ] Không có lỗi console.
- [ ] `pnpm typecheck`, `pnpm lint`, `pnpm build` đều pass.
- [ ] Có screenshot desktop và mobile.
- [ ] PR mô tả before/after và test đã chạy.

## 8. Các bước làm nhỏ nhất

1. Tạo branch `feature/duy-main-discovery`.
2. Hoàn thiện `ResearchProfilePanel`.
3. Hoàn thiện `GrantOpportunityCard`.
4. Hoàn thiện `AgentTrace` và lịch sử phiên.
5. Thêm validation field.
6. Thêm loading/disabled.
7. Thêm empty/no-grounding.
8. Thêm fallback warning.
9. Kiểm tra selection state.
10. Kiểm tra source link không bubble click.
11. Kiểm tra responsive 390/768/1440.
12. Chạy test/build.
13. Chụp ảnh.
14. Commit và push.

```powershell
git checkout -b feature/duy-main-discovery
cd frontend
pnpm typecheck
pnpm lint
pnpm build
cd ..
git add frontend/components frontend/lib/session.ts docs/PRD-GRANTFINDER.md
git commit -m "feat: complete main grant discovery flow"
git push -u origin feature/duy-main-discovery
```
