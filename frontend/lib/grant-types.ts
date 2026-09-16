export type Role = "researcher" | "research_manager";
export type SourceSpan = { field: string; quote: string; source_url: string; source_id: string };
export type Opportunity = {
  id: string; source: string; source_id: string; title: string; issuer: string; status: string;
  open_date?: string | null; close_date?: string | null; country?: string | null; description: string;
  eligibility_text: string; eligible_applicants: string[]; funding_categories: string[];
  award_ceiling?: number | null; award_floor?: number | null; currency: string; canonical_url: string;
  source_spans: SourceSpan[];
};
export type ResearcherProfile = {
  name: string; research_interests: string; keywords: string[];
  career_stage: "student" | "postdoc" | "faculty" | "research_lead";
  institution: string; institution_type: "private_university" | "public_university" | "research_institute" | "individual";
  country: string; requested_budget?: number | null; project_duration_months?: number | null;
};
export type Eligibility = { verdict: "eligible" | "needs_review" | "ineligible"; reasons: string[]; missing_information: string[] };
export type MatchItem = {
  opportunity: Opportunity; eligibility: Eligibility;
  score: { total: number; lexical: number; semantic: number; eligibility: number; freshness: number };
  why_matched: string[]; citations: SourceSpan[];
};
export type ToolEvent = { step: number; tool: string; status: string; input: Record<string, unknown>; output_summary: Record<string, unknown>; duration_ms: number; error?: string | null };
export type MatchResponse = { run_id: string; state: string; generated_at: string; top_matches: MatchItem[]; tool_trace: ToolEvent[]; limitations: string[] };
export type DraftResponse = { draft_id: string; state: string; banner: string; opportunity: Opportunity; sections: Record<string, string>; missing_information: string[]; citations: SourceSpan[]; tool_trace: ToolEvent[] };
export type SourceStats = { open_opportunities: number; by_source: Record<string, number>; next_deadlines: {id:string;title:string;close_date:string;source:string}[]; snapshot_date:string; retrieval_mode:string; sources?: {name:string;role:string;mode:string;provenance:string;count:number|null}[] };
export type ReviewRecord = { review_id:string;draft_id:string;opportunity_id:string;note:string;status:string;created_at:string;decision?:{approved:boolean;note:string;decided_at:string}|null };
