# Wireframe và UI Flow

## Phân chia ownership

| Màn hình | Người phụ trách | File/route |
|---|---|---|
| Màn chính — Trợ lý tìm quỹ | Nguyễn Văn Duy | `GrantFinderApp`, `GrantChat*`, `ResearchProfilePanel`, `GrantOpportunityCard` |
| Soạn hồ sơ/proposal | Đỗ Phúc Hưng | `frontend/components/ProposalWorkspace.tsx` |
| Giám sát hiệu lực | Nguyễn Quang Duy | `frontend/components/MonitoringView.tsx` |
| Đăng nhập/Đăng ký | Dương Thị Ngân | `frontend/components/AuthWireframe.tsx` |

Ownership dùng để chia việc và commit. Mỗi thành viên phải tự hoàn thiện, test và commit phần được giao trước khi ghi nhận contribution.

## Design system

Wireframe dùng lại khung UX đã kiểm chứng của Policy Radar: sidebar/rail thu gọn, lịch sử phiên, chat trung tâm, profile context bên phải, design tokens theo trạng thái, dark mode và mobile overlay. Nội dung, data model và toàn bộ nghiệp vụ đã đổi sang đề 10.

## Vai trò 1 — Nhà nghiên cứu

```text
[Hồ sơ nghiên cứu] -> [Tìm 3 cơ hội]
                            |
                            v
 [Agent trace] <- [3 thẻ cơ hội + điểm + nguồn + eligibility]
                            |
                            v
                 [Chọn cơ hội + xác nhận]
                            |
                            v
                 [Draft có citation / NEEDS_INPUT]
                            |
                            v
                    [Gửi phòng KHCN]
```

## Vai trò 2 — Quản lý phòng KHCN

```text
[Hàng chờ review] -> [Mở source và draft]
                              |
                  +-----------+-----------+
                  v                       v
             [Phê duyệt]             [Yêu cầu sửa]
```

## Luồng giám sát hiệu lực

```text
[Đồng bộ nguồn] -> [Đọc deadline chính thức]
                           |
        +------------------+------------------+
        v                  v                  v
 [Còn hiệu lực]     [Sắp hết hạn]      [Cần xác minh]
        |                  |                  |
        +------------------+------------------+
                           v
                 [Mở URL nguồn kiểm tra]
```

## Luồng tài khoản

```text
[Đăng nhập] <-> [Đăng ký]
                     |
            [Xác minh email + vai trò]
                     |
               [Vào màn chính]
```

Wireframe hiện mô phỏng hành vi; authentication production cần session bảo mật và role gate server-side.

## Bốn trạng thái trải nghiệm AI

| Trạng thái | Giao diện phải thể hiện |
|---|---|
| Happy path | Top 3, score breakdown, source span, nút chọn |
| Low confidence | `needs_review`, thông tin còn thiếu, không khẳng định đủ điều kiện |
| No grounding | Không sinh draft; yêu cầu sửa hồ sơ/từ khóa |
| Correction | Manager yêu cầu sửa hoặc researcher chọn cơ hội khác |

## Nguyên tắc HAX/PAIR

| Nguyên tắc | Vị trí áp dụng |
|---|---|
| Làm rõ hệ thống có thể làm gì | Mô tả dưới form và trang nguồn dữ liệu |
| Giải thích vì sao có kết quả | Score breakdown, matched terms và citation trên từng thẻ |
| Hỗ trợ sửa và khôi phục | Chọn lại cơ hội, sửa profile, manager yêu cầu sửa |
| Cho người dùng kiểm soát | Hai checkpoint trước draft và trước phê duyệt |
| Thể hiện độ không chắc chắn | Verdict `needs_review`, missing information, source warning |

Ảnh hiện có trong `artifacts/`: home, matches, pgvector result, draft HITL và manager review.
