from __future__ import annotations
import json,os,time
from datetime import datetime
from pathlib import Path
from grantfinder.catalog import get_catalog
from grantfinder.models import MatchRequest,ResearcherProfile
from grantfinder.workflow import GrantWorkflow

ROOT=Path(__file__).resolve().parents[1]
CASES=[
 ('mathematical foundations artificial intelligence','grants-353936'),
 ('experiential technologies individual learning AI hubs','grants-359949'),
 ('bioinformatics computational biology research','grants-359003'),
 ('chemical process systems','grants-362061'),
 ('electrical communications computing systems','grants-363613'),
 ('energy power control networks','grants-348258'),
 ('secure open source ecosystems','grants-361333'),
 ('hợp tác khoa học Việt Nam Belarus','nafosted-17668'),
 ('hợp tác nghiên cứu Việt Nam Nga RSF','nafosted-17672'),
 ('nhiệm vụ Liên hiệp Hội khoa học kỹ thuật Việt Nam','nafosted-17693'),
]
def main():
 workflow=GrantWorkflow(); details=[]; hits=0;latencies=[];citation_total=0;citation_grounded=0
 for query,target in CASES:
  profile=ResearcherProfile(research_interests=query,institution_type='private_university',country='Vietnam')
  t=time.perf_counter();result=workflow.match(MatchRequest(profile=profile,top_k=3));latencies.append((time.perf_counter()-t)*1000)
  ids=[x.opportunity.id for x in result.top_matches];hit=target in ids;hits+=int(hit)
  for item in result.top_matches:
   citation_total+=1;citation_grounded+=int(bool(item.citations and all(c.source_url and c.source_id and c.quote for c in item.citations)))
  details.append({'query':query,'target':target,'top3':ids,'hit':hit})
 retrieval=hits/len(CASES);coverage=citation_grounded/max(1,citation_total)
 report={'generated_at':datetime.now().isoformat(timespec='seconds'),'dataset':'grantfinder_retrieval_v1','retrieval_mode':'postgresql_fts+pgvector' if os.getenv('USE_PGVECTOR','0')=='1' else 'in_memory_bm25+local_vector','cases':len(CASES),'metrics':{'recall_at_3':round(retrieval,4),'citation_coverage':round(coverage,4),'median_latency_ms':round(sorted(latencies)[len(latencies)//2],2),'provider_error_cases':0},'thresholds':{'recall_at_3':.8,'citation_coverage':1.0},'passed':retrieval>=.8 and coverage==1.0,'time_saving':{'status':'pending_real_user_measurement','reason':'Không dùng thời gian giả định làm kết quả.'},'details':details}
 out=ROOT/'artifacts'/'eval';out.mkdir(parents=True,exist_ok=True);path=out/'grantfinder_eval.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report['metrics'],ensure_ascii=False,indent=2));print(path)
if __name__=='__main__':main()
