from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0,'.')
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from grantfinder.catalog import fold, get_catalog
from grantfinder.models import DraftRequest, DraftResponse, MatchRequest, MatchResponse, ReviewDecision, ReviewRequest
from grantfinder.workflow import GrantWorkflow

ROOT=Path(__file__).resolve().parents[1]
app=FastAPI(title='GrantFinder AI API',version='0.1.0',description='Grounded grant discovery, eligibility triage and proposal drafting with HITL.')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:3000','http://localhost:3002','http://127.0.0.1:3000','http://127.0.0.1:3002'],allow_origin_regex=r'https://.*\.(up\.railway\.app|vercel\.app|pages\.dev)',allow_methods=['*'],allow_headers=['*'])
workflow=GrantWorkflow(); catalog=get_catalog()

@app.get('/health')
def health()->dict:
    stats=catalog.stats()
    return {'ok':True,'service':'grantfinder-bff','open_opportunities':stats['open_opportunities'],'snapshot_date':stats['snapshot_date'],'retrieval_mode':stats['retrieval_mode'],'human_review_required':True}

@app.get('/api/v1/sources')
def sources()->dict:
    stats=catalog.stats()
    return {**stats,'sources':[
        {'name':'Grants.gov','role':'Cơ hội quốc tế','mode':'Daily XML + public API','provenance':'official','count':stats['by_source'].get('Grants.gov',0)},
        {'name':'NAFOSTED','role':'Cơ hội Việt Nam','mode':'Public WordPress REST + manual source audit','provenance':'official','count':stats['by_source'].get('NAFOSTED',0)},
        {'name':'OpenAlex','role':'Hồ sơ công bố nhà nghiên cứu','mode':'REST on demand','provenance':'official','count':None},
        {'name':'CORDIS','role':'Dự án EU đã được tài trợ','mode':'Bulk CSV/JSON','provenance':'official','count':None},
    ]}

@app.get('/api/v1/opportunities')
def opportunities(q:str='',source:str='',limit:int=Query(default=20,ge=1,le=100))->dict:
    query=fold(q); selected=[]
    for item in catalog.items:
        if source and fold(item.source)!=fold(source):continue
        hay=fold(' '.join([item.title,item.issuer,item.description,' '.join(item.funding_categories)]))
        if query and not all(term in hay for term in query.split()):continue
        selected.append(item)
        if len(selected)>=limit:break
    return {'count':len(selected),'items':selected}

@app.get('/api/v1/opportunities/{opportunity_id}')
def opportunity(opportunity_id:str):
    item=catalog.get(opportunity_id)
    if not item:raise HTTPException(404,'Opportunity not found')
    return item

@app.post('/api/v1/match',response_model=MatchResponse)
def match(req:MatchRequest):
    return workflow.match(req)

@app.post('/api/v1/proposals/draft',response_model=DraftResponse)
def draft(req:DraftRequest):
    try:return workflow.draft(req)
    except KeyError as exc:raise HTTPException(404,str(exc)) from exc
    except PermissionError as exc:raise HTTPException(409,{'code':str(exc),'message':'Nhà nghiên cứu phải chọn và xác nhận cơ hội trước khi tạo bản nháp.'}) from exc

@app.post('/api/v1/reviews')
def request_review(req:ReviewRequest):
    try:return workflow.request_review(req)
    except PermissionError as exc:raise HTTPException(403,str(exc)) from exc

@app.get('/api/v1/reviews')
def reviews():
    return {'items':workflow.list_reviews()}

@app.post('/api/v1/reviews/{review_id}/decision')
def decide(review_id:str,decision:ReviewDecision):
    try:return workflow.decide(review_id,decision)
    except PermissionError as exc:raise HTTPException(403,str(exc)) from exc
    except KeyError as exc:raise HTTPException(404,str(exc)) from exc

@app.get('/api/v1/evaluation')
def evaluation():
    path=ROOT/'artifacts'/'eval'/'grantfinder_eval.json'
    if path.exists():return json.loads(path.read_text(encoding='utf-8'))
    return {'status':'not_run','message':'Chạy python -m grantfinder.eval để tạo benchmark; không hiển thị số liệu giả.'}
