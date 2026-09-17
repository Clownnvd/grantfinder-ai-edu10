import type { SourceStats } from "@/lib/grant-types";

export function SourcesWorkspace({ stats }: { stats: SourceStats | null }) {
  return (
    <div className="flex-1 overflow-y-auto"><div className="mx-auto max-w-5xl px-5 py-5">
      <div><h2 className="text-[16px] font-semibold text-text">Nguồn dữ liệu và độ tin cậy</h2><p className="mt-1 text-[13px] leading-relaxed text-text-muted">Hard fact giữ source ID, URL và đoạn trích. Embedding chỉ hỗ trợ retrieval, không quyết định eligibility.</p></div>
      <div className="mt-5 grid gap-3 md:grid-cols-2">{(stats?.sources ?? []).map((source) => <article key={source.name} className="rounded-xl border border-border-subtle bg-surface p-4 shadow-sm"><div className="flex items-center justify-between"><h3 className="text-[13px] font-semibold text-text">{source.name}</h3><span className="font-mono text-[12px] text-brand-700">{source.count?.toLocaleString("vi-VN") ?? "On demand"}</span></div><p className="mt-2 text-[12px] text-text-muted">{source.role}</p><p className="mt-3 text-[10.5px] text-text-muted">{source.mode} · provenance: {source.provenance}</p></article>)}</div>
      <section className="mt-5 rounded-xl border border-border-subtle bg-surface p-5"><h3 className="text-[13px] font-semibold text-text">Chỉ số hiện tại</h3><div className="mt-3 grid gap-3 sm:grid-cols-3"><Metric label="Cơ hội mở" value={stats?.open_opportunities.toLocaleString("vi-VN") ?? "—"} /><Metric label="Snapshot" value={stats?.snapshot_date ?? "—"} /><Metric label="Retrieval" value={stats?.retrieval_mode ?? "—"} /></div><div className="mt-4 rounded-lg border border-caution-300 bg-caution-50 p-3 text-[11.5px] leading-relaxed text-caution-700">Recall@3 và time-saving chỉ được công bố từ artifact/user study có thể chạy lại. Không biến mục tiêu thành kết quả.</div></section>
    </div></div>
  );
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-lg bg-surface-2 p-3"><div className="text-[10px] uppercase tracking-wide text-text-muted">{label}</div><div className="mt-1 truncate text-[13px] font-semibold text-text" title={value}>{value}</div></div>; }
