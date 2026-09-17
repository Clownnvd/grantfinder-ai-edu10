import type { GrantMessage } from "@/lib/session";
import type { MatchItem } from "@/lib/grant-types";
import { AgentTrace } from "./AgentTrace";
import { GrantOpportunityCard } from "./GrantOpportunityCard";

export function GrantChatMessage({ message, onSelect }: { message: GrantMessage; onSelect: (item: MatchItem) => void }) {
  if (message.role === "user") return <div className="ml-auto max-w-[85%] rounded-xl bg-brand-600 px-3.5 py-2.5 text-[13.5px] leading-relaxed text-white">{message.content}</div>;
  return (
    <div className="max-w-full">
      <div className={`rounded-xl border px-4 py-3 text-[13px] leading-relaxed ${message.error ? "border-blocked-300 bg-blocked-50 text-blocked-700" : "border-border-subtle bg-surface text-text"}`}>
        <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-brand-600">GrantFinder</div>
        <p className="whitespace-pre-wrap">{message.content}</p>
      </div>
      {message.match && <div className="mt-3 space-y-3">{message.match.top_matches.map((item, index) => <GrantOpportunityCard key={item.opportunity.id} item={item} rank={index + 1} onSelect={() => onSelect(item)} />)}<AgentTrace trace={message.match.tool_trace} compact /></div>}
    </div>
  );
}
