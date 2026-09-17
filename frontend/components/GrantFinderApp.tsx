"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError } from "@/lib/grant-api";
import type { MatchItem, MonitoringResponse, Role, SourceStats } from "@/lib/grant-types";
import { loadSessions, newSession, saveSessions, sessionTitle, type GrantMessage, type GrantSession, type WorkspaceView } from "@/lib/session";
import { AuthWireframe } from "./AuthWireframe";
import { GrantChatInput } from "./GrantChatInput";
import { GrantChatMessage } from "./GrantChatMessage";
import { GrantSidebar } from "./GrantSidebar";
import { MonitoringView } from "./MonitoringView";
import { ProposalWorkspace } from "./ProposalWorkspace";
import { ResearchProfilePanel } from "./ResearchProfilePanel";
import { ReviewsWorkspace } from "./ReviewsWorkspace";
import { SourcesWorkspace } from "./SourcesWorkspace";

const suggestions = [
  "Trí tuệ nhân tạo ứng dụng trong giáo dục và phân tích dữ liệu học tập",
  "Hợp tác nghiên cứu Việt Nam về khoa học dữ liệu và y tế số",
  "Năng lượng sạch, lưới điện thông minh và điều khiển tối ưu",
];

const viewCopy: Record<WorkspaceView, { title: string; subtitle: string }> = {
  chat: { title: "Trợ lý tìm quỹ", subtitle: "Tìm cơ hội phù hợp, giải thích điểm và dẫn nguồn" },
  proposal: { title: "Soạn hồ sơ xin tài trợ", subtitle: "Dựng bản nháp có căn cứ và hai cổng duyệt" },
  monitoring: { title: "Giám sát hiệu lực", subtitle: "Theo dõi call còn hạn, sắp đóng hoặc cần xác minh" },
  reviews: { title: "Hàng chờ phê duyệt", subtitle: "Quản lý phòng KHCN kiểm tra và ghi quyết định" },
  sources: { title: "Nguồn và đánh giá", subtitle: "Provenance, retrieval mode và bằng chứng chất lượng" },
  account: { title: "Đăng nhập và phân quyền", subtitle: "Working wireframe cho tài khoản và vai trò" },
};

export function GrantFinderApp() {
  const [sessions, setSessions] = useState<GrantSession[]>([]);
  const [currentId, setCurrentId] = useState("");
  const [view, setViewRaw] = useState<WorkspaceView>("chat");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [role, setRole] = useState<Role>("researcher");
  const [selected, setSelected] = useState<MatchItem | null>(null);
  const [stats, setStats] = useState<SourceStats | null>(null);
  const [monitoring, setMonitoring] = useState<MonitoringResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [latency, setLatency] = useState<number | null>(null);
  const [reviewRefresh, setReviewRefresh] = useState(0);
  const [dark, setDark] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const sessionsRef = useRef<GrantSession[]>([]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const loaded = loadSessions();
      const initial = loaded.length ? loaded : [newSession()];
      sessionsRef.current = initial;
      setSessions(initial);
      setCurrentId(initial[0].id);
      const savedView = localStorage.getItem("grantfinder.view") as WorkspaceView | null;
      if (savedView && savedView in viewCopy) setViewRaw(savedView);
      const savedTheme = localStorage.getItem("grantfinder.theme");
      const shouldDark = savedTheme === "dark";
      setDark(shouldDark);
      document.documentElement.dataset.theme = shouldDark ? "dark" : "light";
      setHydrated(true);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    api.sources().then(setStats).catch(() => setStats(null));
    api.monitoring().then(setMonitoring).catch(() => setMonitoring(null));
  }, []);

  const current = sessions.find((session) => session.id === currentId) ?? sessions[0] ?? null;
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [current?.messages.length, busy]);

  function setView(next: WorkspaceView) {
    setViewRaw(next);
    localStorage.setItem("grantfinder.view", next);
    if (next !== "chat") setSidebarOpen(false);
  }

  function commitSessions(next: GrantSession[]) {
    sessionsRef.current = next;
    setSessions(next);
    saveSessions(next);
  }

  function updateSession(id: string, update: (session: GrantSession) => GrantSession) {
    const next = sessionsRef.current.map((session) => session.id === id ? { ...update(session), updatedAt: Date.now() } : session);
    commitSessions(next);
  }

  function createSession() {
    const unused = sessionsRef.current.find((session) => !session.messages.some((message) => message.role === "user"));
    if (unused) { setCurrentId(unused.id); setView("chat"); return; }
    const session = newSession();
    commitSessions([session, ...sessionsRef.current]);
    setCurrentId(session.id);
    setSelected(null);
    setView("chat");
  }

  function deleteSession(id: string) {
    const remaining = sessionsRef.current.filter((session) => session.id !== id);
    if (remaining.length) {
      if (id === currentId) setCurrentId(remaining[0].id);
      commitSessions(remaining);
      return;
    }
    const replacement = newSession();
    setCurrentId(replacement.id);
    commitSessions([replacement]);
  }

  function selectSession(id: string) {
    setCurrentId(id);
    setSelected(null);
    setView("chat");
    setSidebarOpen(false);
  }

  async function runQuery(text: string) {
    if (!current || busy) return;
    const sessionId = current.id;
    const started = performance.now();
    const profile = { ...current.profile, research_interests: text };
    const userMessage: GrantMessage = { id: `user-${Date.now()}`, role: "user", content: text };
    updateSession(sessionId, (session) => ({ ...session, title: sessionTitle(text), profile, messages: [...session.messages, userMessage] }));
    setBusy(true);
    try {
      const match = await api.match(role, profile);
      const content = match.top_matches.length
        ? `Tôi đã quét ${stats?.open_opportunities?.toLocaleString("vi-VN") ?? "kho"} cơ hội và chọn ${match.top_matches.length} kết quả tốt nhất. Retrieval chỉ tạo shortlist; anh hãy mở nguồn và chọn một cơ hội trước khi soạn.`
        : "Chưa tìm thấy cơ hội có đủ căn cứ. Anh hãy bổ sung lĩnh vực, từ khóa hoặc phạm vi hợp tác rồi thử lại.";
      const assistant: GrantMessage = { id: `assistant-${Date.now()}`, role: "assistant", content, match };
      updateSession(sessionId, (session) => ({ ...session, messages: [...session.messages, assistant] }));
    } catch (caught) {
      const content = caught instanceof ApiError && caught.status === 0 ? "Không kết nối được backend. Dữ liệu trong phiên vẫn được giữ; hãy kiểm tra dịch vụ rồi thử lại." : caught instanceof Error ? caught.message : "Không thể chạy matching.";
      updateSession(sessionId, (session) => ({ ...session, messages: [...session.messages, { id: `error-${Date.now()}`, role: "assistant", content, error: true }] }));
    } finally {
      setLatency(Math.round(performance.now() - started));
      setBusy(false);
    }
  }

  function selectOpportunity(item: MatchItem) { setSelected(item); setView("proposal"); }
  function toggleTheme() { const next = !dark; setDark(next); document.documentElement.dataset.theme = next ? "dark" : "light"; localStorage.setItem("grantfinder.theme", next ? "dark" : "light"); }

  const copy = viewCopy[view];
  const showChat = view === "chat" && current;
  const messages = useMemo(() => current?.messages ?? [], [current]);

  if (!hydrated || !current) {
    return <div className="grid h-dvh place-items-center bg-bg text-[13px] text-text-muted">Đang tải GrantFinder workspace…</div>;
  }

  return (
    <div className="flex h-dvh overflow-hidden bg-bg text-text">
      <GrantSidebar view={view} onView={setView} sessions={sessions} currentId={currentId} onSelectSession={selectSession} onNewSession={createSession} onDeleteSession={deleteSession} open={sidebarOpen} onOpen={() => setSidebarOpen(true)} onClose={() => setSidebarOpen(false)} />
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-2 border-b border-border-subtle bg-surface px-4 py-2.5">
          {!sidebarOpen && <button onClick={() => setSidebarOpen(true)} className="-ml-1 rounded-md p-1.5 text-text-muted hover:bg-surface-2 md:hidden" aria-label="Mở thanh bên"><svg viewBox="0 0 20 20" className="size-5" fill="none"><path d="M3 6h14M3 10h14M3 14h14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg></button>}
          <div className="min-w-0 flex-1"><h1 className="truncate text-[15px] font-semibold leading-none text-text">{copy.title}</h1><p className="mt-1 truncate text-[11px] leading-none text-text-muted">{copy.subtitle}</p></div>
          {view === "chat" && latency !== null && <span className="rounded border border-border-subtle px-1.5 py-0.5 font-mono text-[10px] text-text-muted">{latency}ms</span>}
          <label className="hidden items-center gap-1.5 rounded-lg border border-border-subtle bg-surface-2 px-2 py-1.5 text-[11px] text-text-muted sm:flex">Vai trò<select value={role} onChange={(event) => { const next = event.target.value as Role; setRole(next); if (next === "research_manager") setView("reviews"); }} className="bg-transparent font-medium text-text outline-none"><option value="researcher">Nhà nghiên cứu</option><option value="research_manager">Quản lý KHCN</option></select></label>
          <button onClick={toggleTheme} className="grid size-8 place-items-center rounded-lg border border-border-subtle text-text-muted hover:bg-surface-2" aria-label="Đổi giao diện sáng tối">{dark ? "☀" : "◐"}</button>
        </header>

        {showChat ? <div className="flex min-h-0 flex-1">
          <div className="flex min-w-0 flex-1 flex-col">
            <div className="flex-1 overflow-y-auto"><div className="mx-auto flex max-w-3xl flex-col gap-3 px-4 py-4">{messages.map((message) => <GrantChatMessage key={message.id} message={message} onSelect={selectOpportunity} />)}{busy && <p className="text-[12px] text-text-muted">LangGraph đang truy xuất pgvector, kiểm tra điều kiện và rerank…</p>}<div ref={endRef} /></div></div>
            <GrantChatInput onSend={runQuery} busy={busy} suggestions={messages.every((message) => message.role !== "user") ? suggestions : []} />
          </div>
          <ResearchProfilePanel profile={current.profile} onChange={(profile) => updateSession(current.id, (session) => ({ ...session, profile }))} />
        </div> : view === "proposal" ? <ProposalWorkspace key={selected?.opportunity.id ?? "no-selection"} selected={selected} profile={current?.profile ?? newSession().profile} onBack={() => setView("chat")} onReviewCreated={() => setReviewRefresh((value) => value + 1)} /> : view === "monitoring" ? <div className="flex-1 overflow-y-auto"><div className="mx-auto max-w-6xl px-5 py-5"><MonitoringView data={monitoring} /></div></div> : view === "reviews" ? <ReviewsWorkspace role={role} refreshKey={reviewRefresh} /> : view === "sources" ? <SourcesWorkspace stats={stats} /> : <div className="flex-1 overflow-y-auto p-5"><div className="mx-auto max-w-5xl"><AuthWireframe /></div></div>}
      </main>
    </div>
  );
}
