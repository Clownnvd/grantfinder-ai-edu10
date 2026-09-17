import type { MatchResponse, ResearcherProfile } from "./grant-types";

export type WorkspaceView =
  | "chat"
  | "proposal"
  | "monitoring"
  | "reviews"
  | "sources"
  | "account";

export type GrantMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  match?: MatchResponse;
  error?: boolean;
};

export type GrantSession = {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  profile: ResearcherProfile;
  messages: GrantMessage[];
};

const STORAGE_KEY = "grantfinder.sessions.v2";

export const DEFAULT_PROFILE: ResearcherProfile = {
  name: "Nguyễn An",
  research_interests: "",
  keywords: ["artificial intelligence", "education", "machine learning"],
  career_stage: "faculty",
  institution: "VinUniversity",
  institution_type: "private_university",
  country: "Vietnam",
  requested_budget: 200_000,
  project_duration_months: 24,
};

export function newSession(): GrantSession {
  const now = Date.now();
  return {
    id: `session-${now.toString(36)}`,
    title: "Phiên tìm quỹ mới",
    createdAt: now,
    updatedAt: now,
    profile: { ...DEFAULT_PROFILE },
    messages: [
      {
        id: `welcome-${now}`,
        role: "assistant",
        content:
          "Hãy mô tả hướng nghiên cứu của anh. Tôi sẽ truy xuất dữ liệu chính thức, kiểm tra điều kiện sơ bộ và trả ba cơ hội phù hợp kèm căn cứ. Eligibility cuối cùng vẫn cần phòng KHCN xác minh.",
      },
    ],
  };
}

export function loadSessions(): GrantSession[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as GrantSession[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveSessions(sessions: GrantSession[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(0, 20)));
  } catch {
    // The workspace remains usable when storage is blocked.
  }
}

export function sessionTitle(query: string): string {
  const compact = query.trim().replace(/\s+/g, " ");
  return compact.length > 42 ? `${compact.slice(0, 42)}…` : compact || "Phiên tìm quỹ mới";
}
