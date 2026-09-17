import type { MonitoringResponse, MonitoringStatus } from "@/lib/grant-types";

const labels: Record<MonitoringStatus, string> = {
  active: "Còn hiệu lực",
  closing_soon: "Sắp hết hạn",
  expired: "Hết hiệu lực",
  needs_review: "Cần xác minh",
};

const tones: Record<MonitoringStatus, string> = {
  active: "border border-eligible-300 bg-eligible-50 text-eligible-700",
  closing_soon: "border border-caution-300 bg-caution-50 text-caution-700",
  expired: "border border-blocked-300 bg-blocked-50 text-blocked-700",
  needs_review: "border border-border-strong bg-surface-2 text-text-muted",
};

export function MonitoringView({ data }: { data: MonitoringResponse | null }) {
  const counts = data?.counts ?? {
    active: 0,
    closing_soon: 0,
    expired: 0,
    needs_review: 0,
  };

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-border-subtle bg-surface p-5 shadow-sm">
        <span className="rounded-md bg-brand-50 px-2 py-1 text-[10px] font-bold uppercase tracking-[.16em] text-brand-700">
          Deadline monitor
        </span>
        <h2 className="mt-4 text-[17px] font-semibold text-text">Giám sát hiệu lực cơ hội tài trợ</h2>
        <p className="mt-2 max-w-3xl text-[13px] leading-6 text-text-muted">
          Mỗi lần đồng bộ, hệ thống đối chiếu ngày đóng từ nguồn chính thức. Call hết
          hạn không được đưa vào matching; call thiếu deadline được giữ ở trạng thái
          cần xác minh.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {(Object.keys(labels) as MonitoringStatus[]).map((status) => (
          <div key={status} className="rounded-xl border border-border-subtle bg-surface p-4 shadow-sm">
            <span className={`inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold ${tones[status]}`}>
              {labels[status]}
            </span>
            <div className="mt-4 text-3xl font-black">{counts[status].toLocaleString("vi-VN")}</div>
            <p className="mt-1 text-xs text-text-muted">call trong snapshot hiện tại</p>
          </div>
        ))}
      </section>

      <section className="overflow-hidden rounded-xl border border-border-subtle bg-surface shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle px-5 py-4">
          <div>
            <h3 className="font-bold">Danh sách cần theo dõi trước</h3>
            <p className="mt-1 text-xs text-text-muted">
              Kiểm tra ngày {data?.checked_at ?? "—"} · snapshot {data?.snapshot_date ?? "—"}
            </p>
          </div>
          <span className="rounded-full bg-brand-50 px-3 py-1.5 text-xs font-semibold text-brand-700">
            Nguồn chính thức
          </span>
        </div>
        <div className="divide-y divide-border-subtle">
          {(data?.items ?? []).slice(0, 12).map((item) => (
            <article key={item.id} className="grid gap-3 px-5 py-4 md:grid-cols-[150px_minmax(0,1fr)_130px_110px] md:items-center">
              <span className={`w-fit rounded-full px-2.5 py-1 text-[10px] font-bold ${tones[item.status]}`}>
                {labels[item.status]}
              </span>
              <div className="min-w-0">
                <h4 className="truncate font-semibold">{item.title}</h4>
                <p className="mt-1 text-xs text-text-muted">{item.source} · {item.id}</p>
              </div>
              <div className="text-sm font-semibold">{item.close_date ?? "Chưa công bố"}</div>
              <a
                href={item.canonical_url}
                target="_blank"
                rel="noreferrer"
                className="text-sm font-semibold text-brand-700"
              >
                Kiểm tra ↗
              </a>
            </article>
          ))}
          {!data && <p className="p-8 text-center text-sm text-text-muted">Đang tải trạng thái nguồn…</p>}
        </div>
      </section>

      {data?.limitations && (
        <p className="rounded-lg border border-caution-300 bg-caution-50 p-4 text-xs leading-5 text-caution-700">
          {data.limitations}
        </p>
      )}
    </div>
  );
}
