from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


Role = Literal["researcher", "research_manager"]
Verdict = Literal["eligible", "needs_review", "ineligible"]


class SourceSpan(BaseModel):
    field: str
    quote: str
    source_url: str
    source_id: str


class Opportunity(BaseModel):
    id: str
    source: str
    source_id: str
    title: str
    issuer: str
    status: str
    open_date: date | None = None
    close_date: date | None = None
    country: str | None = None
    description: str = ""
    eligibility_text: str = ""
    eligible_applicants: list[str] = []
    funding_categories: list[str] = []
    award_ceiling: float | None = None
    award_floor: float | None = None
    currency: str = "USD"
    canonical_url: str
    document_hash: str | None = None
    source_spans: list[SourceSpan] = []


class ResearcherProfile(BaseModel):
    name: str = "Nhà nghiên cứu demo"
    research_interests: str = Field(min_length=3)
    keywords: list[str] = []
    career_stage: Literal["student", "postdoc", "faculty", "research_lead"] = "faculty"
    institution: str = "VinUniversity"
    institution_type: Literal["private_university", "public_university", "research_institute", "individual"] = "private_university"
    country: str = "Vietnam"
    requested_budget: float | None = Field(default=None, ge=0)
    project_duration_months: int | None = Field(default=None, ge=1, le=120)


class EligibilityCheck(BaseModel):
    verdict: Verdict
    reasons: list[str]
    missing_information: list[str] = []


class ScoreBreakdown(BaseModel):
    total: float
    lexical: float
    semantic: float
    eligibility: float
    freshness: float


class MatchItem(BaseModel):
    opportunity: Opportunity
    eligibility: EligibilityCheck
    score: ScoreBreakdown
    why_matched: list[str]
    citations: list[SourceSpan]


class ToolEvent(BaseModel):
    step: int
    tool: str
    status: Literal["started", "succeeded", "failed", "waiting_for_human"]
    input: dict[str, Any] = {}
    output_summary: dict[str, Any] = {}
    duration_ms: int = 0
    error: str | None = None


class MatchRequest(BaseModel):
    role: Role = "researcher"
    profile: ResearcherProfile
    top_k: int = Field(default=3, ge=1, le=10)


class MatchResponse(BaseModel):
    run_id: str
    state: Literal["awaiting_researcher_review"]
    generated_at: datetime
    top_matches: list[MatchItem]
    tool_trace: list[ToolEvent]
    limitations: list[str]


class DraftRequest(BaseModel):
    role: Role = "researcher"
    opportunity_id: str
    profile: ResearcherProfile
    research_question: str = Field(min_length=5)
    human_confirmed: bool = False


class DraftResponse(BaseModel):
    draft_id: str
    state: Literal["awaiting_research_office_review"]
    banner: str
    opportunity: Opportunity
    sections: dict[str, str]
    missing_information: list[str]
    citations: list[SourceSpan]
    tool_trace: list[ToolEvent]


class ReviewRequest(BaseModel):
    role: Role = "researcher"
    draft_id: str
    opportunity_id: str
    note: str = ""


class ReviewDecision(BaseModel):
    role: Role
    approved: bool
    note: str = ""
