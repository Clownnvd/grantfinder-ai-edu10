"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/grant-api";
import type { ReviewRecord, Role } from "@/lib/grant-types";

export function ReviewsWorkspace({ role, refreshKey }: { role: Role; refreshKey: number }) {
  const [items, setItems] = useState<ReviewRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rejectId, setRejectId] = useState("");
  const [reason, setReason] = useState("");

  useEffect(() => { api.reviews().then((result) => setItems(result.items)).catch((caught) => setError(caught instanceof Error ? caught.message : "Không tải được hàng chờ.")).finally(() => setLoading(false)); }, [refreshKey]);

  async function decide(id: string, approved: boolean, note: string) {
    setError("");
    try { await api.decide(id, approved, note); const result = await api.reviews(); setItems(result.items); setRejectId(""); setReason(""); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Không thể ghi quyết định."); }
  }

  return (
    <div className="flex-1 overflow-y-auto"><div className="mx-auto max-w-5xl px-5 py-5">
      <div className="mb-4"><h2 className="text-[16px] font-semibold text-text">Hàng chờ phòng KHCN</h2><p className="mt-1 text-[13px] text-text-muted">Kiểm tra eligibility, deadline, citation và nội dung draft trước khi quyết định.</p></div>
      {role !== "research_manager" && <div className="mb-4 rounded-lg border border-caution-300 bg-caution-50 px-4 py-3 text-[12.5px] text-caution-700">Vai trò Nhà nghiên cứu chỉ được xem trạng thái. Chuyển sang Quản lý phòng KHCN để phê duyệt hoặc yêu cầu sửa.</div>}
      {error && <div className="mb-4 rounded-lg border border-blocked-300 bg-blocked-50 px-4 py-3 text-[12.5px] text-blocked-700">{error}</div>}
      {loading ? <p className="text-[13px] text-text-muted">Đang tải hàng chờ…</p> : items.length === 0 ? <div className="rounded-xl border border-dashed border-border-strong bg-surface p-8 text-center"><h3 className="font-semibold text-text">Chưa có yêu cầu duyệt</h3><p className="mt-2 text-[12.5px] text-text-muted">Nhà nghiên cứu cần tạo draft và gửi review trước.</p></div> : <div className="space-y-3">{items.map((item) => <article key={item.review_id} className="rounded-xl border border-border-subtle bg-surface p-4 shadow-sm"><div className="flex flex-wrap items-center gap-2"><Status status={item.status} /><code className="text-[11px] text-text">{item.draft_id}</code><span className="text-[11px] text-text-muted">{item.opportunity_id}</span><span className="ml-auto text-[10.5px] text-text-muted">{item.created_at}</span></div><p className="mt-3 text-[12.5px] leading-relaxed text-text-muted">{item.note || "Không có ghi chú từ nhà nghiên cứu."}</p>{item.decision && <div className="mt-3 rounded-lg bg-surface-2 p-3 text-[11.5px] text-text-muted">Quyết định: {item.decision.note || "Không có ghi chú"} · {item.decision.decided_at}</div>}{item.status === "pending" && role === "research_manager" && <div className="mt-4"><div className="flex gap-2"><button onClick={() => decide(item.review_id, true, "Đã kiểm tra nguồn và cho phép tiếp tục hoàn thiện.")} className="rounded-lg bg-eligible-600 px-3 py-2 text-[12px] font-medium text-white">Phê duyệt</button><button onClick={() => setRejectId(item.review_id)} className="rounded-lg border border-blocked-300 bg-blocked-50 px-3 py-2 text-[12px] font-medium text-blocked-700">Yêu cầu sửa</button></div>{rejectId === item.review_id && <div className="mt-3 rounded-lg border border-blocked-300 bg-blocked-50 p-3"><label className="text-[11.5px] font-medium text-blocked-700">Lý do yêu cầu sửa<textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={3} className="mt-1 w-full resize-none rounded-lg border border-blocked-300 bg-surface px-3 py-2 text-[12px] text-text" /></label><div className="mt-2 flex gap-2"><button onClick={() => decide(item.review_id, false, reason)} disabled={!reason.trim()} className="rounded-lg bg-blocked-600 px-3 py-1.5 text-[11.5px] font-medium text-white disabled:opacity-40">Gửi yêu cầu sửa</button><button onClick={() => { setRejectId(""); setReason(""); }} className="rounded-lg border border-border-strong bg-surface px-3 py-1.5 text-[11.5px] text-text">Hủy</button></div></div>}</div>}</article>)}</div>}
    </div></div>
  );
}

function Status({ status }: { status: string }) {
  const styles = status === "approved" ? "border-eligible-300 bg-eligible-50 text-eligible-700" : status === "changes_requested" ? "border-blocked-300 bg-blocked-50 text-blocked-700" : "border-caution-300 bg-caution-50 text-caution-700";
  const label = status === "approved" ? "Đã phê duyệt" : status === "changes_requested" ? "Cần sửa" : "Đang chờ";
  return <span className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold ${styles}`}>{label}</span>;
}
