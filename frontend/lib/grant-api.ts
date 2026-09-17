import type {
  DraftResponse,
  MatchResponse,
  MonitoringResponse,
  ResearcherProfile,
  ReviewRecord,
  Role,
  SourceStats,
} from "./grant-types";

const BFF = process.env.NEXT_PUBLIC_BFF_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(message: string, public status = 0) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BFF}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError(`Không kết nối được backend ${BFF}.`, 0);
  }
  if (!response.ok) {
    let detail = "";
    try {
      detail = JSON.stringify((await response.json()).detail);
    } catch {
      detail = "";
    }
    throw new ApiError(detail || `Backend trả lỗi ${response.status}`, response.status);
  }
  return response.json() as Promise<T>;
}

export const api = {
  sources: () => request<SourceStats>("/api/v1/sources"),
  monitoring: () => request<MonitoringResponse>("/api/v1/monitoring"),
  match: (role: Role, profile: ResearcherProfile) =>
    request<MatchResponse>("/api/v1/match", {
      method: "POST",
      body: JSON.stringify({ role, profile, top_k: 3 }),
    }),
  draft: (
    role: Role,
    opportunity_id: string,
    profile: ResearcherProfile,
    research_question: string,
    human_confirmed: boolean,
  ) =>
    request<DraftResponse>("/api/v1/proposals/draft", {
      method: "POST",
      body: JSON.stringify({
        role,
        opportunity_id,
        profile,
        research_question,
        human_confirmed,
      }),
    }),
  requestReview: (draft_id: string, opportunity_id: string, note: string) =>
    request<ReviewRecord>("/api/v1/reviews", {
      method: "POST",
      body: JSON.stringify({ role: "researcher", draft_id, opportunity_id, note }),
    }),
  reviews: () => request<{ items: ReviewRecord[] }>("/api/v1/reviews"),
  decide: (review_id: string, approved: boolean, note: string) =>
    request<ReviewRecord>(`/api/v1/reviews/${review_id}/decision`, {
      method: "POST",
      body: JSON.stringify({ role: "research_manager", approved, note }),
    }),
};
