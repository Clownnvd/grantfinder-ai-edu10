from __future__ import annotations
import os
from grantfinder.catalog import check_eligibility,get_catalog
from grantfinder.models import DraftRequest,MatchRequest,ResearcherProfile,ReviewDecision
from grantfinder.workflow import GrantWorkflow

profile=ResearcherProfile(research_interests='artificial intelligence machine learning',keywords=['education'],institution='VinUniversity',institution_type='private_university',country='Vietnam',requested_budget=200000)
workflow=GrantWorkflow();catalog=get_catalog()
assert len(catalog.items)==968
assert sum(x.source=='NAFOSTED' for x in catalog.items)==3
result=workflow.match(MatchRequest(profile=profile,top_k=3))
assert len(result.top_matches)==3
assert [e.tool for e in result.tool_trace]==['search_opportunities','check_eligibility','rerank_candidates','request_human_review']
assert result.tool_trace[-1].status=='waiting_for_human'
assert all(x.citations for x in result.top_matches)
try:
 workflow.draft(DraftRequest(opportunity_id=result.top_matches[0].opportunity.id,profile=profile,research_question='AI hỗ trợ học tập cá nhân hóa',human_confirmed=False))
 raise AssertionError('draft should require confirmation')
except PermissionError:pass
draft=workflow.draft(DraftRequest(opportunity_id=result.top_matches[0].opportunity.id,profile=profile,research_question='AI hỗ trợ học tập cá nhân hóa',human_confirmed=True))
assert draft.banner.startswith('DRAFT_ONLY') and draft.state=='awaiting_research_office_review'
review=workflow.request_review(__import__('grantfinder.models',fromlist=['ReviewRequest']).ReviewRequest(draft_id=draft.draft_id,opportunity_id=draft.opportunity.id))
try:
 workflow.decide(review['review_id'],ReviewDecision(role='researcher',approved=True))
 raise AssertionError('researcher must not approve')
except PermissionError:pass
approved=workflow.decide(review['review_id'],ReviewDecision(role='research_manager',approved=True,note='source checked'))
assert approved['status']=='approved'
print('GRANTFINDER CORE TESTS PASS')
