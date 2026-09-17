"use client";

import { useEffect, useRef, useState } from "react";

export function GrantChatInput({ onSend, busy, suggestions = [] }: { onSend: (text: string) => void; busy: boolean; suggestions?: string[] }) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = ref.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 220)}px`;
  }, [text]);

  function send(value: string) {
    const clean = value.trim();
    if (!clean || busy) return;
    onSend(clean);
    setText("");
  }

  return (
    <div className="border-t border-border-subtle bg-surface-2/90 backdrop-blur">
      <div className="mx-auto max-w-3xl px-4 py-3">
        {suggestions.length > 0 && <div className="mb-2 flex flex-wrap gap-1.5">{suggestions.map((suggestion) => <button key={suggestion} onClick={() => send(suggestion)} disabled={busy} className="rounded-full border border-border-strong bg-surface px-3 py-1 text-[12px] text-text-muted hover:border-brand-300 hover:text-brand-700 disabled:opacity-50">{suggestion}</button>)}</div>}
        <form onSubmit={(event) => { event.preventDefault(); send(text); }} className="flex items-end gap-2">
          <textarea ref={ref} aria-label="Hướng nghiên cứu hoặc mục tiêu dự án" value={text} onChange={(event) => setText(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(text); } }} rows={1} placeholder="Mô tả hướng nghiên cứu hoặc mục tiêu dự án… (Shift+Enter để xuống dòng)" className="min-h-[44px] flex-1 resize-none overflow-y-auto rounded-lg border border-border-strong bg-surface px-3 py-2.5 text-[14px] leading-relaxed text-text placeholder:text-text-muted focus:border-brand-400" />
          <button type="submit" disabled={busy || !text.trim()} className="h-[44px] shrink-0 rounded-lg bg-brand-600 px-4 text-[14px] font-medium text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-40">{busy ? "Đang tìm…" : "Gửi"}</button>
        </form>
        <p className="mt-1.5 text-[11px] text-text-muted">GrantFinder chỉ khẳng định hard fact có trong nguồn. Eligibility cuối cùng luôn cần người có trách nhiệm xác minh.</p>
      </div>
    </div>
  );
}
