from fastapi.testclient import TestClient
from bff.grant_main import app
client=TestClient(app)
profile={'name':'Test','research_interests':'artificial intelligence education','keywords':['machine learning'],'career_stage':'faculty','institution':'VinUniversity','institution_type':'private_university','country':'Vietnam','requested_budget':200000,'project_duration_months':24}
health=client.get('/health');assert health.status_code==200 and health.json()['open_opportunities']==968 and health.json()['orchestration']=='langgraph'
monitoring=client.get('/api/v1/monitoring');assert monitoring.status_code==200 and sum(monitoring.json()['counts'].values())==968
matched=client.post('/api/v1/match',json={'role':'researcher','profile':profile,'top_k':3});assert matched.status_code==200
body=matched.json();assert len(body['top_matches'])==3 and body['tool_trace'][-1]['status']=='waiting_for_human' and body['orchestration']=='langgraph'
graph_run=client.get(f"/api/v1/graph/runs/{body['run_id']}");assert graph_run.status_code==200 and graph_run.json()['checkpoint_id']
missing_graph=client.get('/api/v1/graph/runs/match-does-not-exist');assert missing_graph.status_code==404
opp=body['top_matches'][0]['opportunity']['id']
blocked=client.post('/api/v1/proposals/draft',json={'role':'researcher','opportunity_id':opp,'profile':profile,'research_question':'AI hỗ trợ cá nhân hóa học tập','human_confirmed':False});assert blocked.status_code==409
draft=client.post('/api/v1/proposals/draft',json={'role':'researcher','opportunity_id':opp,'profile':profile,'research_question':'AI hỗ trợ cá nhân hóa học tập','human_confirmed':True});assert draft.status_code==200 and draft.json()['banner'].startswith('DRAFT_ONLY')
review=client.post('/api/v1/reviews',json={'role':'researcher','draft_id':draft.json()['draft_id'],'opportunity_id':opp,'note':'review'});assert review.status_code==200
rid=review.json()['review_id']
forbidden=client.post(f'/api/v1/reviews/{rid}/decision',json={'role':'researcher','approved':True});assert forbidden.status_code==403
approved=client.post(f'/api/v1/reviews/{rid}/decision',json={'role':'research_manager','approved':True,'note':'checked'});assert approved.status_code==200 and approved.json()['status']=='approved'
print('GRANTFINDER API TESTS PASS')
