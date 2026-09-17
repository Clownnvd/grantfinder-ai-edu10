import type { MatchItem } from "@/lib/grant-types";

const verdict = { eligible: "Có thể phù hợp", needs_review: "Cần xác minh", ineligible: "Không phù hợp" };
const verdictClass = { eligible: "border-eligible-300 bg-eligible-50 text-eligible-700", needs_review: "border-caution-300 bg-caution-50 text-caution-700", ineligible: "border-blocked-300 bg-blocked-50 text-blocked-700" };

export function GrantOpportunityCard({ item, rank, onSelect }: { item: MatchItem; rank: number; onSelect: () => void }) {
  const opportunity = item.opportunity;
  const citation = item.citations[0];
  return (
    <article className="animate-card-in overflow-hidden rounded-xl border border-border-subtle bg-surface shadow-sm">
      <div className="p-4">
        <div className="flex items-start gap-3">
          <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-brand-600 text-[12px] font-bold text-white">{rank}</span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-1.5"><span className="rounded-md bg-brand-50 px-1.5 py-0.5 text-[10px] font-semibold text-brand-700">{opportunity.source}</span><span className={`rounded-md border px-1.5 py-0.5 text-[10px] font-medium ${verdictClass[item.eligibility.verdict]}`}>{verdict[item.eligibility.verdict]}</span><span className="ml-auto font-mono text-[11px] font-semibold text-text">{Math.round(item.score.total * 100)} điểm</span></div>
            <h3 className="mt-2 text-[14px] font-semibold leading-snug text-text">{opportunity.title}</h3>
            <p className="mt-1 text-[11.5px] text-text-muted">{opportunity.issuer}</p>
          </div>
        </div>
        <div className="mt-3 grid grid-cols-3 gap-1.5">
          <Mini label="Hạn nộp" value={opportunity.close_date ?? "Cần kiểm tra"} />
          <Mini label="Trần tài trợ" value={opportunity.award_ceiling ? `${opportunity.award_ceiling.toLocaleString("vi-VN")} ${opportunity.currency}` : "Chưa công bố"} />
          <Mini label="Quốc gia" value={opportunity.country ?? "Không giới hạn"} />
        </div>
        <div className="mt-3 space-y-1">{item.why_matched.map((reason) => <p key={reason} className="text-[11.5px] leading-relaxed text-text-muted">• {reason}</p>)}</div>
        <div className="mt-2 font-mono text-[10px] text-text-muted">BM25 {Math.round(item.score.lexical * 100)} · vector {Math.round(item.score.semantic * 100)} · eligibility {Math.round(item.score.eligibility * 100)}</div>
        {citation && <details className="mt-3 rounded-lg border border-border-subtle bg-surface-2 px-3 py-2"><summary className="cursor-pointer text-[11px] font-medium text-brand-700">Xem căn cứ được truy xuất</summary><p className="mt-2 line-clamp-4 text-[11px] leading-relaxed text-text-muted">{citation.quote}</p></details>}
      </div>
      <div className="flex flex-wrap gap-2 border-t border-border-subtle bg-surface-2/60 px-4 py-3">
        <a href={opportunity.canonical_url} target="_blank" rel="noreferrer" className="rounded-lg border border-border-strong bg-surface px-3 py-1.5 text-[11.5px] font-medium text-text hover:border-brand-400">Kiểm tra nguồn ↗</a>
        <button onClick={onSelect} className="rounded-lg bg-brand-600 px-3 py-1.5 text-[11.5px] font-medium text-white hover:bg-brand-700">Chọn cơ hội này →</button>
      </div>
    </article>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg bg-surface-2 p-2"><div className="text-[9px] uppercase tracking-wide text-text-muted">{label}</div><div className="mt-0.5 truncate text-[10.5px] font-semibold text-text" title={value}>{value}</div></div>;
}
