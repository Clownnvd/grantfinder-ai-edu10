# PRD — GrantFinder AI

## Problem

Nhà nghiên cứu phải theo dõi nhiều website, đọc từng call-for-proposal và tự so điều kiện trước khi viết. Tìm bằng từ khóa tạo nhiều kết quả lệch trọng tâm; deadline, eligibility và biểu mẫu nằm rải trong HTML/PDF. Phòng KHCN khó theo dõi cơ hội, lý do matching và trạng thái duyệt trong một luồng thống nhất.

## Users

1. **Researcher:** nhập hướng nghiên cứu, nhận shortlist, chọn cơ hội, hoàn thiện draft.
2. **Research manager:** xác minh eligibility/deadline, review draft, approve hoặc yêu cầu sửa.

## User stories và DoD

| Story | DoD |
|---|---|
| Tìm cơ hội theo hướng nghiên cứu | Trả đúng 3 kết quả có score breakdown, URL và source span |
| Biết vì sao phù hợp | Hiện matched terms, eligibility verdict và thông tin còn thiếu |
| Không bỏ lỡ deadline | Dashboard chỉ đếm open call; sắp xếp deadline gần nhất |
| Dựng proposal | Chỉ chạy sau confirmation; mọi trường thiếu gắn `[NEEDS_INPUT]` |
| Phòng KHCN kiểm soát | Role manager mới ghi được approve/request changes |
| Audit agent | Mỗi run hiện tool, input summary, output summary, trạng thái và latency |
| Xử lý lỗi | pgvector/Gemini lỗi có fallback được ghi trong trace; app không crash |

## Non-goals MVP

- Không tự nộp hồ sơ cho funder.
- Không khẳng định eligibility cuối cùng.
- Không lưu CV hoặc dữ liệu nghiên cứu chưa công bố thật.
- Không crawl Pivot-RP hay dữ liệu có license hạn chế.

## Success metrics

- Recall@3 ≥80% trên gold set.
- Citation coverage của hard facts =100%.
- Provider error =0 trong demo chính.
- Accuracy trích deadline/eligibility ≥80% khi có gold labels.
- Giảm thời gian shortlist/draft ≥50% chỉ được công bố sau user study thật.
