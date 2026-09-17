from __future__ import annotations

from grantfinder.models import DraftRequest, MatchRequest, ResearcherProfile
from grantfinder.workflow import GrantWorkflow

profile = ResearcherProfile(
    research_interests="artificial intelligence education",
    keywords=["machine learning"],
    institution="VinUniversity",
    institution_type="private_university",
    country="Vietnam",
    requested_budget=200_000,
)
workflow = GrantWorkflow()

matched = workflow.match(MatchRequest(profile=profile, top_k=3))
assert matched.orchestration == "langgraph"
assert matched.graph_nodes == [
    "search_opportunities",
    "check_eligibility",
    "rerank_candidates",
    "request_researcher_review",
]

checkpoint = workflow.inspect_run(matched.run_id)
assert checkpoint["checkpoint_id"]
assert checkpoint["status"] == "awaiting_researcher_review"
assert checkpoint["next_nodes"] == []
assert checkpoint["top_ids"] == [
    item.opportunity.id for item in matched.top_matches
]

draft = workflow.draft(
    DraftRequest(
        opportunity_id=matched.top_matches[0].opportunity.id,
        profile=profile,
        research_question="AI hỗ trợ cá nhân hóa học tập như thế nào?",
        human_confirmed=True,
    )
)
assert draft.orchestration == "langgraph"
assert "validate_draft_output" in draft.graph_nodes
assert draft.tool_trace[-1].tool == "request_research_office_review"
assert draft.tool_trace[-1].status == "waiting_for_human"

draft_checkpoint = workflow.inspect_run(draft.run_id)
assert draft_checkpoint["checkpoint_id"]
assert draft_checkpoint["status"] == "awaiting_research_office_review"

print("LANGGRAPH WORKFLOW TESTS PASS")
