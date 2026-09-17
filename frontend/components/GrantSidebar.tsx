"use client";

import { GrantLogo } from "./GrantLogo";
import type { GrantSession, WorkspaceView } from "@/lib/session";

type Props = {
  view: WorkspaceView;
  onView: (view: WorkspaceView) => void;
  sessions: GrantSession[];
  currentId: string;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string) => void;
  open: boolean;
  onOpen: () => void;
  onClose: () => void;
};

const nav: { view: WorkspaceView; label: string; icon: React.ReactNode }[] = [
  { view: "chat", label: "Trợ lý tìm quỹ", icon: <path d="M4 5h12v8H8l-4 3V5Z" /> },
  { view: "proposal", label: "Soạn hồ sơ", icon: <path d="M6 3h5l3 3v11H6zM11 3v3h3M8 11h4M8 14h4" /> },
  { view: "monitoring", label: "Giám sát hiệu lực", icon: <path d="M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14ZM10 6v4l2.5 2" /> },
  { view: "reviews", label: "Hàng chờ phê duyệt", icon: <path d="M5 3h10v14H5zM8 7h4M8 10h4M8 13h3" /> },
  { view: "sources", label: "Nguồn và đánh giá", icon: <path d="M4 5c3-2 9-2 12 0v10c-3-2-9-2-12 0V5Z" /> },
  { view: "account", label: "Tài khoản", icon: <path d="M10 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM4 17c.5-3 2.5-5 6-5s5.5 2 6 5" /> },
];

export function GrantSidebar(props: Props) {
  const usedSessions = props.sessions.filter((item) => item.messages.some((message) => message.role === "user"));

  const rail = (
    <div className="hidden h-full w-14 shrink-0 flex-col items-center border-r border-border-subtle bg-surface-2 py-3 md:flex">
      <GrantLogo size={27} />
      <button className="mb-3 mt-2 grid size-9 place-items-center rounded-lg border border-border-strong text-text-muted hover:border-brand-400 hover:bg-surface hover:text-brand-600" onClick={props.onOpen} aria-label="Mở thanh bên">
        <svg viewBox="0 0 20 20" className="size-[18px]" fill="none"><path d="M8 5l5 5-5 5M16 4v12" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </button>
      {nav.map((item) => <RailButton key={item.view} active={props.view === item.view} label={item.label} onClick={() => props.onView(item.view)}>{item.icon}</RailButton>)}
      <span className="mt-auto grid size-8 place-items-center rounded-full bg-brand-600 text-[11px] font-bold text-white">NC</span>
    </div>
  );

  return (
    <>
      {props.open && <button className="fixed inset-0 z-20 bg-black/40 md:hidden" onClick={props.onClose} aria-label="Đóng thanh bên" />}
      {!props.open && rail}
      <aside className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-border-subtle bg-surface-2 transition-transform md:static ${props.open ? "translate-x-0" : "-translate-x-full md:hidden"}`}>
        <div className="flex items-center gap-2.5 px-4 py-4">
          <GrantLogo size={32} />
          <div className="min-w-0 flex-1"><div className="text-[14px] font-semibold text-text">GrantFinder AI</div><div className="text-[10.5px] text-text-muted">Trợ lý tài trợ nghiên cứu</div></div>
          <button onClick={props.onClose} className="rounded-md p-1 text-text-muted hover:bg-surface" aria-label="Thu gọn thanh bên">
            <svg viewBox="0 0 20 20" className="size-[18px]" fill="none"><path d="M12 5l-5 5 5 5M4 4v12" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </button>
        </div>

        <div className="px-3">
          <button onClick={props.onNewSession} className="flex w-full items-center gap-2 rounded-lg border border-border-strong bg-surface px-3 py-2 text-[13px] font-medium text-text hover:border-brand-400 hover:bg-brand-50 dark:hover:bg-brand-900/30">
            <svg viewBox="0 0 20 20" className="size-4" fill="none"><path d="M10 4v12M4 10h12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg>
            Phiên tìm quỹ mới
          </button>
        </div>

        <nav className="mt-3 px-3">
          {nav.map((item) => (
            <button key={item.view} onClick={() => props.onView(item.view)} className={`mb-0.5 flex w-full items-center rounded-lg px-3 py-2 text-[13px] font-medium transition-colors ${props.view === item.view ? "bg-brand-600 text-white" : "text-text hover:bg-surface"}`}>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="mt-4 flex-1 overflow-y-auto px-2 pb-3">
          <div className="px-2 pb-1 text-[10.5px] font-semibold uppercase tracking-wide text-text-muted">Lịch sử</div>
          {usedSessions.length === 0 && <p className="px-2 py-3 text-[12px] leading-relaxed text-text-muted">Chưa có phiên nào. Hãy mô tả hướng nghiên cứu để bắt đầu.</p>}
          {usedSessions.sort((a, b) => b.updatedAt - a.updatedAt).map((session) => (
            <button key={session.id} onClick={() => props.onSelectSession(session.id)} className={`group mb-1 flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-left text-[12.5px] ${session.id === props.currentId && props.view === "chat" ? "bg-brand-100 text-brand-900 dark:bg-brand-900/50 dark:text-brand-50" : "text-text hover:bg-surface"}`}>
              <span className="min-w-0 flex-1 truncate">{session.title}</span>
              <span role="button" tabIndex={0} onClick={(event) => { event.stopPropagation(); props.onDeleteSession(session.id); }} onKeyDown={(event) => { if (event.key === "Enter") { event.stopPropagation(); props.onDeleteSession(session.id); } }} className="hidden rounded p-0.5 text-text-muted hover:text-blocked-600 group-hover:block" aria-label="Xóa phiên">×</span>
            </button>
          ))}
        </div>

        <div className="border-t border-border-subtle p-2">
          <button onClick={() => props.onView("account")} className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-left hover:bg-surface">
            <span className="grid size-8 place-items-center rounded-full bg-brand-600 text-[11px] font-bold text-white">NC</span>
            <span className="min-w-0"><span className="block truncate text-[12.5px] font-medium text-text">Nhà nghiên cứu</span><span className="block truncate text-[10.5px] text-text-muted">Tài khoản demo</span></span>
          </button>
        </div>
      </aside>
    </>
  );
}

function RailButton({ active, label, onClick, children }: { active: boolean; label: string; onClick: () => void; children: React.ReactNode }) {
  return <button title={label} aria-label={label} onClick={onClick} className={`mb-1 grid size-9 place-items-center rounded-lg ${active ? "bg-brand-600 text-white" : "text-text-muted hover:bg-surface hover:text-text"}`}><svg viewBox="0 0 20 20" className="size-[18px]" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">{children}</svg></button>;
}
