import type { ToolEvent } from "@/lib/grant-types";

export function AgentTrace({ trace, compact = false }: { trace: ToolEvent[]; compact?: boolean }) {
  return (
    <details className="mt-3 overflow-hidden rounded-lg border border-border-subtle bg-surface-2" open={!compact}>
      <summary className="flex cursor-pointer items-center gap-2 px-3 py-2 text-[11.5px] font-medium text-text"><span className="size-1.5 rounded-full bg-brand-500" />LangGraph trace<span className="ml-auto text-text-muted">{trace.length} bước</span></summary>
      <div className="border-t border-border-subtle px-3 py-2">
        {trace.map((event) => <div key={`${event.step}-${event.tool}`} className="flex items-center gap-2 py-1.5 text-[11px]"><span className={`size-1.5 rounded-full ${event.status === "waiting_for_human" ? "bg-caution-500" : event.status === "failed" ? "bg-blocked-500" : "bg-eligible-500"}`} /><code className="min-w-0 flex-1 truncate text-text">{event.tool}</code><span className="text-text-muted">{event.duration_ms}ms</span></div>)}
      </div>
    </details>
  );
}
