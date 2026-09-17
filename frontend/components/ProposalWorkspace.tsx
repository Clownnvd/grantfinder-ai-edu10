"use client";

import { useMemo, useState } from "react";
import { api, ApiError } from "@/lib/grant-api";
import type { DraftResponse, MatchItem, ResearcherProfile } from "@/lib/grant-types";
import { AgentTrace } from "./AgentTrace";

export function ProposalWorkspace({ selected, profile, onBack, onReviewCreated }: { selected: MatchItem | null; profile: ResearcherProfile; onBack: () => void; onReviewCreated: () => void }) {
  const [question, setQuestion] = useState("Xây dựng trợ lý AI hỗ trợ học tập cá nhân hóa và cảnh báo sớm rủi ro bỏ học");
  const [confirmed, setConfirmed] = useState(false);
  const [draft, setDraft] = useState<DraftResponse | null>(null);
  const [sections, setSections] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reviewSent, setReviewSent] = useState(false);

  const missingCount = useMemo(() => Object.values(sections).filter((value) => value.includes("[NEEDS_INPUT]") || !value.trim()).length, [sections]);
  const rewrite = draft?.tool_trace.find((event) => event.tool === "optional_grounded_llm_rewrite")?.output_summary;

  async function buildDraft() {
    if (!selected || !confirmed || question.trim().length < 5) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await api.draft("researcher", selected.opportunity.id, profile, question, confirmed);
      setDraft(response); setSections(response.sections);
    } catch (caught) {
      setError(caught instanceof ApiError && caught.status === 409 ? "Anh cần xác nhận đã chọn đúng cơ hội trước khi tạo bản nháp." : caught instanceof Error ? caught.message : "Không thể tạo bản nháp.");
    } finally { setBusy(false); }
  }

  function saveLocal() {
    if (!draft) return;
    try { localStorage.setItem(`grantfinder.draft.${draft.draft_id}`, JSON.stringify(sections)); setNotice("Đã lưu bản nháp trên thiết bị này."); }
    catch { setError("Trình duyệt không cho phép lưu bản nháp cục bộ."); }
  }

  async function sendReview() {
    if (!draft || !selected || reviewSent) return;
    setBusy(true); setError("");
    try {
      await api.requestReview(draft.draft_id, selected.opportunity.id, "Nhờ phòng KHCN xác minh eligibility, deadline và khung ngân sách.");
      setReviewSent(true); setNotice("Đã chuyển bản nháp sang hàng chờ của phòng KHCN."); onReviewCreated();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Không thể gửi duyệt."); }
    finally { setBusy(false); }
  }

  if (!selected) return <div className="flex flex-1 items-center justify-center p-6"><div className="max-w-lg rounded-xl border border-dashed border-border-strong bg-surface p-8 text-center"><div className="mx-auto grid size-12 place-items-center rounded-xl bg-brand-50 text-xl text-brand-600">□</div><h2 className="mt-4 text-[16px] font-semibold text-text">Chưa chọn cơ hội</h2><p className="mt-2 text-[13px] leading-relaxed text-text-muted">Quay lại trợ lý, chạy matching và chọn một cơ hội trong top 3 trước khi dựng hồ sơ.</p><button onClick={onBack} className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-[13px] font-medium text-white">Về trợ lý tìm quỹ</button></div></div>;

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-5xl px-5 py-5">
        {error && <div className="mb-4 rounded-lg border border-blocked-300 bg-blocked-50 px-4 py-3 text-[12.5px] text-blocked-700">{error}</div>}
        {notice && <div className="mb-4 rounded-lg border border-eligible-300 bg-eligible-50 px-4 py-3 text-[12.5px] text-eligible-700">{notice}</div>}
        <section className="rounded-xl border border-border-subtle bg-surface p-5 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div><span className="text-[10px] font-semibold uppercase tracking-wider text-brand-600">{selected.opportunity.source}</span><h2 className="mt-1 max-w-3xl text-[17px] font-semibold leading-snug text-text">{selected.opportunity.title}</h2><p className="mt-1 text-[12px] text-text-muted">{selected.opportunity.issuer} · hạn {selected.opportunity.close_date ?? "cần xác minh"}</p></div>
            <a href={selected.opportunity.canonical_url} target="_blank" rel="noreferrer" className="rounded-lg border border-border-strong px-3 py-2 text-[12px] font-medium text-brand-700">Mở nguồn gốc ↗</a>
          </div>
          <label className="mt-4 block text-[12px] font-medium text-text">Câu hỏi nghiên cứu<textarea rows={3} value={question} onChange={(event) => setQuestion(event.target.value)} className="mt-1 w-full resize-none rounded-lg border border-border-strong bg-surface-2 px-3 py-2.5 text-[13px] text-text" /></label>
          <label className="mt-4 flex items-start gap-3 rounded-lg border border-caution-300 bg-caution-50 p-3 text-[12.5px] text-caution-700"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} className="mt-0.5 size-4" /><span><b>Tôi xác nhận đã chọn đúng cơ hội.</b><br />Tôi hiểu eligibility là sơ bộ và sẽ kiểm tra tài liệu gốc.</span></label>
          <button onClick={buildDraft} disabled={!confirmed || question.trim().length < 5 || busy} className="mt-4 rounded-lg bg-brand-600 px-4 py-2.5 text-[13px] font-medium text-white hover:bg-brand-700 disabled:opacity-40">{busy ? "LangGraph đang dựng…" : "Tạo bản nháp có citation"}</button>
        </section>

        {draft && <section className="mt-4 overflow-hidden rounded-xl border border-border-subtle bg-surface shadow-sm">
          <div className="flex flex-wrap items-center gap-2 border-b border-border-subtle bg-surface-2 px-5 py-3"><span className="rounded-md border border-caution-300 bg-caution-50 px-2 py-1 text-[10px] font-semibold text-caution-700">DRAFT ONLY</span><span className="text-[11px] text-text-muted">{missingCount} phần còn cần bổ sung</span>{typeof rewrite?.mode === "string" && <span className="ml-auto text-[10.5px] text-text-muted">Chế độ: {rewrite.mode}</span>}</div>
          <div className="space-y-4 p-5">{Object.entries(sections).map(([name, value]) => <label key={name} className="block"><span className="text-[12px] font-semibold text-text">{name}</span><textarea value={value} onChange={(event) => setSections((current) => ({ ...current, [name]: event.target.value }))} rows={Math.max(3, Math.ceil(value.length / 110))} className={`mt-1 w-full resize-y rounded-lg border px-3 py-2.5 text-[12.5px] leading-relaxed text-text ${value.includes("[NEEDS_INPUT]") ? "border-caution-300 bg-caution-50/40" : "border-border-strong bg-surface"}`} /></label>)}</div>
          <div className="border-t border-border-subtle bg-surface-2/60 px-5 py-3"><AgentTrace trace={draft.tool_trace} compact /><div className="mt-3 flex flex-wrap justify-end gap-2"><button onClick={saveLocal} className="rounded-lg border border-border-strong bg-surface px-3 py-2 text-[12px] font-medium text-text">Lưu nháp</button><button onClick={sendReview} disabled={busy || reviewSent} className="rounded-lg bg-brand-600 px-3 py-2 text-[12px] font-medium text-white disabled:opacity-50">{reviewSent ? "Đã gửi duyệt ✓" : "Gửi phòng KHCN duyệt"}</button></div></div>
        </section>}
      </div>
    </div>
  );
}
