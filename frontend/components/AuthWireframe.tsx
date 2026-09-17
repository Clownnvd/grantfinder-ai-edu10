"use client";

import { FormEvent, useState } from "react";

export function AuthWireframe() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [message, setMessage] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(
      mode === "login"
        ? "Wireframe: thông tin hợp lệ sẽ chuyển về màn Khám phá cơ hội."
        : "Wireframe: tài khoản mới sẽ chờ xác minh email trước khi sử dụng.",
    );
  }

  return (
    <div className="grid overflow-hidden rounded-xl border border-border-subtle bg-surface shadow-sm lg:grid-cols-[1.05fr_.95fr]">
      <section className="bg-brand-800 p-8 text-white md:p-12">
        <span className="inline-flex rounded-md bg-brand-100 px-3 py-1 text-[10px] font-black uppercase tracking-[.16em] text-brand-800">
          Secure workspace
        </span>
        <h2 className="mt-6 max-w-xl text-4xl font-black leading-tight">
          Cơ hội tài trợ, căn cứ và quyết định duyệt trong một nơi.
        </h2>
        <p className="mt-4 max-w-lg text-sm leading-7 text-white/65">
          Tài khoản xác định đúng vai trò nhà nghiên cứu hoặc quản lý phòng KHCN.
          Quyền phê duyệt được kiểm tra ở backend, không dựa vào giao diện.
        </p>
        <div className="mt-10 grid gap-3 text-sm text-white/75">
          <p>✓ Không lưu CV thật trong bản demo</p>
          <p>✓ Hai cổng Human-in-the-loop</p>
          <p>✓ Mọi hard fact có nguồn kiểm chứng</p>
        </div>
      </section>

      <section className="bg-surface p-7 md:p-12">
        <div className="grid grid-cols-2 rounded-lg bg-surface-2 p-1">
          <button
            onClick={() => { setMode("login"); setMessage(""); }}
            className={`rounded-lg px-4 py-2.5 text-sm font-bold ${mode === "login" ? "bg-surface text-text shadow-sm" : "text-text-muted"}`}
          >
            Đăng nhập
          </button>
          <button
            onClick={() => { setMode("register"); setMessage(""); }}
            className={`rounded-lg px-4 py-2.5 text-sm font-bold ${mode === "register" ? "bg-surface text-text shadow-sm" : "text-text-muted"}`}
          >
            Đăng ký
          </button>
        </div>

        <div className="mt-7">
          <p className="text-xs font-bold uppercase tracking-[.16em] text-text-muted">GrantFinder AI</p>
          <h3 className="mt-2 text-2xl font-black">
            {mode === "login" ? "Chào mừng anh quay lại" : "Tạo tài khoản nhóm nghiên cứu"}
          </h3>
        </div>

        <form className="mt-6 space-y-4" onSubmit={submit}>
          {mode === "register" && (
            <label className="block text-xs font-semibold text-text-muted">
              Họ và tên
              <input required className="mt-1 w-full rounded-lg border border-border-strong bg-surface-2 px-3 py-3 text-text" placeholder="Nguyễn Văn A" />
            </label>
          )}
          <label className="block text-xs font-semibold text-text-muted">
            Email tổ chức
            <input required type="email" className="mt-1 w-full rounded-lg border border-border-strong bg-surface-2 px-3 py-3 text-text" placeholder="researcher@university.edu.vn" />
          </label>
          <label className="block text-xs font-semibold text-text-muted">
            Mật khẩu
            <input required minLength={8} type="password" className="mt-1 w-full rounded-lg border border-border-strong bg-surface-2 px-3 py-3 text-text" placeholder="Tối thiểu 8 ký tự" />
          </label>
          {mode === "register" && (
            <label className="block text-xs font-semibold text-text-muted">
              Vai trò
              <select className="mt-1 w-full rounded-lg border border-border-strong bg-surface-2 px-3 py-3 text-text">
                <option>Nhà nghiên cứu</option>
                <option>Quản lý phòng KHCN</option>
              </select>
            </label>
          )}
          <button type="submit" className="w-full rounded-lg bg-brand-600 px-4 py-3.5 font-bold text-white hover:bg-brand-700">
            {mode === "login" ? "Đăng nhập an toàn" : "Tạo tài khoản"}
          </button>
        </form>

        {message && <p className="mt-4 rounded-lg border border-eligible-300 bg-eligible-50 p-3 text-xs leading-5 text-eligible-700">{message}</p>}
        <p className="mt-5 text-center text-[11px] leading-5 text-text-muted">
          Đây là working wireframe. Authentication production sẽ dùng session bảo mật,
          email verification và role gate phía server.
        </p>
      </section>
    </div>
  );
}
