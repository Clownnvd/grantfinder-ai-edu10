"use client";

import type { ResearcherProfile } from "@/lib/grant-types";

export function ResearchProfilePanel({ profile, onChange }: { profile: ResearcherProfile; onChange: (profile: ResearcherProfile) => void }) {
  const fields = [
    ["Tổ chức", profile.institution],
    ["Quốc gia", profile.country],
    ["Giai đoạn", profile.career_stage],
    ["Thời lượng", profile.project_duration_months ? `${profile.project_duration_months} tháng` : ""],
    ["Ngân sách", profile.requested_budget ? `${profile.requested_budget.toLocaleString("vi-VN")} USD` : ""],
    ["Từ khóa", profile.keywords.join(", ")],
  ];
  const completed = fields.filter(([, value]) => Boolean(value)).length + (profile.research_interests ? 1 : 0);
  const total = fields.length + 1;

  return (
    <aside className="hidden w-72 shrink-0 flex-col border-l border-border-subtle bg-surface-2 lg:flex">
      <div className="border-b border-border-subtle px-4 py-3.5">
        <div className="flex items-center justify-between"><h2 className="text-[13px] font-semibold text-text">Hồ sơ nghiên cứu</h2><span className="text-[12px] font-medium text-text-muted">{completed}/{total}</span></div>
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-border-subtle"><span className="block h-full rounded-full bg-brand-500 transition-[width]" style={{ width: `${Math.round((completed / total) * 100)}%` }} /></div>
        <p className="mt-1.5 text-[10.5px] leading-snug text-text-muted">Ngữ cảnh được giữ trong phiên. Anh có thể sửa các trường trước khi chạy lại.</p>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <label className="block text-[11px] font-medium text-text-muted">Hướng nghiên cứu<textarea value={profile.research_interests} onChange={(event) => onChange({ ...profile, research_interests: event.target.value })} rows={4} placeholder="— chưa có" className="mt-1 w-full resize-none rounded-lg border border-border-strong bg-surface px-2.5 py-2 text-[12px] leading-relaxed text-text" /></label>
        <label className="mt-3 block text-[11px] font-medium text-text-muted">Từ khóa<input value={profile.keywords.join(", ")} onChange={(event) => onChange({ ...profile, keywords: event.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} className="mt-1 w-full rounded-lg border border-border-strong bg-surface px-2.5 py-2 text-[12px] text-text" /></label>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <label className="text-[11px] font-medium text-text-muted">Tháng<input type="number" min={1} max={120} value={profile.project_duration_months ?? ""} onChange={(event) => onChange({ ...profile, project_duration_months: Number(event.target.value) || null })} className="mt-1 w-full rounded-lg border border-border-strong bg-surface px-2 py-2 text-[12px] text-text" /></label>
          <label className="text-[11px] font-medium text-text-muted">Ngân sách<input type="number" min={0} value={profile.requested_budget ?? ""} onChange={(event) => onChange({ ...profile, requested_budget: Number(event.target.value) || null })} className="mt-1 w-full rounded-lg border border-border-strong bg-surface px-2 py-2 text-[12px] text-text" /></label>
        </div>
        <div className="mt-4 border-t border-border-subtle pt-2">
          {fields.slice(0, 3).map(([label, value]) => <div key={label} className="flex items-start gap-2 rounded-lg px-1 py-2"><span className={`mt-1.5 size-1.5 shrink-0 rounded-full ${value ? "bg-eligible-500" : "bg-border-strong"}`} /><div><div className="text-[10.5px] text-text-muted">{label}</div><div className={`mt-0.5 text-[12px] ${value ? "font-medium text-text" : "text-text-muted"}`}>{value || "— chưa có"}</div></div></div>)}
        </div>
      </div>
    </aside>
  );
}
