from __future__ import annotations

import os
import time
import uuid
from datetime import datetime
from threading import Lock

from grantfinder.catalog import get_catalog, rerank
from grantfinder.llm import improve_draft
from grantfinder.models import DraftRequest, DraftResponse, MatchRequest, MatchResponse, ReviewDecision, ReviewRequest, ToolEvent


def event(step:int,tool:str,status:str,t0:float,input:dict,output:dict|None=None,error:str|None=None)->ToolEvent:
    return ToolEvent(step=step,tool=tool,status=status,input=input,output_summary=output or {},duration_ms=round((time.perf_counter()-t0)*1000),error=error)


class GrantWorkflow:
    """Explicit stateful tool workflow. LLM is optional and never decides hard eligibility."""

    def __init__(self):
        self.catalog=get_catalog()
        self.reviews:dict[str,dict]={}
        self.lock=Lock()

    def match(self,req:MatchRequest)->MatchResponse:
        trace=[]; run_id='run-'+uuid.uuid4().hex[:10]
        t=time.perf_counter(); query={'research_interests':req.profile.research_interests,'keywords':req.profile.keywords,'top_k':req.top_k}
        engine='in_memory_bm25+local_vector'
        retrieval_warning=None
        if os.getenv('USE_PGVECTOR','0')=='1':
            try:
                from grantfinder.pgvector_store import search as pg_search
                candidates=pg_search(req.profile,limit=max(30,req.top_k*10))
                engine='postgresql_fts+pgvector'
            except Exception as exc:
                candidates=self.catalog.search(req.profile,limit=max(30,req.top_k*10))
                retrieval_warning=f'{type(exc).__name__}: pgvector unavailable; deterministic fallback used'
        else:
            candidates=self.catalog.search(req.profile,limit=max(30,req.top_k*10))
        trace.append(event(1,'search_opportunities','succeeded',t,query,{'candidates':len(candidates),'engine':engine,'warning':retrieval_warning}))
        t=time.perf_counter(); matches=rerank(req.profile,candidates,req.top_k)
        trace.append(event(2,'check_eligibility','succeeded',t,{'candidate_count':len(candidates),'profile_type':req.profile.institution_type},{'shortlisted':len(matches),'hard_decision_owner':'deterministic_rules'}))
        t=time.perf_counter(); matches=sorted(matches,key=lambda x:x.score.total,reverse=True)
        trace.append(event(3,'rerank_candidates','succeeded',t,{'weights':{'lexical':.42,'semantic':.28,'eligibility':.22,'freshness':.08}},{'top_ids':[x.opportunity.id for x in matches]}))
        trace.append(ToolEvent(step=4,tool='request_human_review',status='waiting_for_human',input={'role':'researcher'},output_summary={'next':'select one opportunity before drafting'},duration_ms=0))
        return MatchResponse(run_id=run_id,state='awaiting_researcher_review',generated_at=datetime.now(),top_matches=matches,tool_trace=trace,limitations=[
            'Kết quả matching là shortlist; phòng KHCN phải xác minh eligibility trong tài liệu gốc.',
            'Local vector là fallback tất định; khi DATABASE_URL được cấu hình, ingestion và retrieval dùng pgvector.',
            'Không có hành động nộp hồ sơ tự động.',
        ])

    def draft(self,req:DraftRequest)->DraftResponse:
        opportunity=self.catalog.get(req.opportunity_id)
        if not opportunity:raise KeyError('opportunity_not_found')
        if not req.human_confirmed:raise PermissionError('researcher_confirmation_required')
        t=time.perf_counter(); trace=[]
        trace.append(event(1,'load_grounded_opportunity','succeeded',t,{'opportunity_id':req.opportunity_id},{'source':opportunity.source,'citations':len(opportunity.source_spans)}))
        t=time.perf_counter()
        sections={
            'Tóm tắt đề xuất':f"[DRAFT — CẦN DUYỆT] {req.research_question}",
            'Mức độ phù hợp với quỹ':f"Đề xuất liên quan tới {opportunity.title}. Chỉ sử dụng điều kiện và phạm vi đã trích từ nguồn gốc.",
            'Mục tiêu nghiên cứu':'[NEEDS_INPUT] Viết 2–3 mục tiêu đo được và kiểm tra lại với call-for-proposal.',
            'Phương pháp':'[NEEDS_INPUT] Mô tả thiết kế nghiên cứu, dữ liệu, phương pháp phân tích và kế hoạch quản trị rủi ro.',
            'Kế hoạch công việc':'[NEEDS_INPUT] Chia work package, mốc nghiệm thu, người phụ trách và thời gian.',
            'Ngân sách':f"[NEEDS_INPUT] Ngân sách đề nghị: {req.profile.requested_budget or 'chưa cung cấp'} {opportunity.currency}; phải đối chiếu trần và chi phí hợp lệ.",
            'Tác động dự kiến':'[NEEDS_INPUT] Nêu kết quả khoa học, tác động xã hội và kế hoạch phổ biến.',
            'Tuân thủ và đạo đức':'[NEEDS_INPUT] Phòng KHCN xác nhận eligibility, đạo đức nghiên cứu, dữ liệu và xung đột lợi ích.',
        }
        trace.append(event(2,'build_proposal_draft','succeeded',t,{'template':'grounded_generic_v1','research_question':req.research_question},{'sections':len(sections),'banner':'DRAFT_ONLY'}))
        t=time.perf_counter()
        grounded_context={'opportunity':opportunity.model_dump(mode='json'),'profile':req.profile.model_dump(mode='json'),'research_question':req.research_question}
        sections,llm_info=improve_draft(sections,grounded_context)
        trace.append(event(3,'optional_grounded_llm_rewrite','succeeded',t,{'provider':'gemini_or_offline_fallback'},llm_info))
        trace.append(ToolEvent(step=4,tool='request_research_office_review',status='waiting_for_human',input={'required_role':'research_manager'},output_summary={'write_or_submit_performed':False},duration_ms=0))
        return DraftResponse(draft_id='draft-'+uuid.uuid4().hex[:10],state='awaiting_research_office_review',banner='DRAFT_ONLY — Chưa phải hồ sơ nộp; cần phòng KHCN duyệt.',opportunity=opportunity,sections=sections,missing_information=['Mục tiêu định lượng','Phương pháp chi tiết','Work packages','Dự toán chi tiết','Kế hoạch tác động','Xác nhận eligibility'],citations=opportunity.source_spans,tool_trace=trace)

    def request_review(self,req:ReviewRequest)->dict:
        if req.role!='researcher':raise PermissionError('researcher_role_required')
        review_id='review-'+uuid.uuid4().hex[:10]
        record={'review_id':review_id,'draft_id':req.draft_id,'opportunity_id':req.opportunity_id,'note':req.note,'status':'pending','created_at':datetime.now().isoformat(timespec='seconds'),'decision':None}
        with self.lock:self.reviews[review_id]=record
        return record

    def decide(self,review_id:str,decision:ReviewDecision)->dict:
        if decision.role!='research_manager':raise PermissionError('research_manager_role_required')
        with self.lock:
            if review_id not in self.reviews:raise KeyError('review_not_found')
            record=self.reviews[review_id]
            record['status']='approved' if decision.approved else 'changes_requested'
            record['decision']={'approved':decision.approved,'note':decision.note,'decided_at':datetime.now().isoformat(timespec='seconds')}
            return dict(record)

    def list_reviews(self)->list[dict]:
        with self.lock:return list(self.reviews.values())

