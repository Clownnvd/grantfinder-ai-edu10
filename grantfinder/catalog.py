from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
import unicodedata
from collections import Counter
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import numpy as np

from grantfinder.models import EligibilityCheck, MatchItem, Opportunity, ResearcherProfile, ScoreBreakdown, SourceSpan

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'grants'
DIM=256
CATEGORY_LABELS={
    'ST':'Science and technology','HL':'Health','ED':'Education','ENV':'Environment',
    'EN':'Energy','AG':'Agriculture','BC':'Business','HU':'Humanities','IS':'Information',
    'LJL':'Law and justice','NR':'Natural resources','RD':'Regional development',
}

def fold(text:str)->str:
    value=unicodedata.normalize('NFD',(text or '').casefold()).replace('đ','d')
    return ''.join(ch for ch in value if unicodedata.category(ch)!='Mn')

def terms(text:str)->list[str]:
    return [x for x in re.findall(r'[a-z0-9]+',fold(text)) if len(x)>1]

def number(value):
    try: return float(value) if value not in (None,'') else None
    except (TypeError,ValueError): return None

def as_list(value)->list[str]:
    if value is None:return []
    if isinstance(value,list):return [str(x) for x in value]
    return [str(value)]

def hash_embedding(text:str)->np.ndarray:
    vector=np.zeros(DIM,dtype=np.float32)
    tokens=terms(text)
    for token in tokens:
        digest=hashlib.blake2b(token.encode(),digest_size=8).digest()
        idx=int.from_bytes(digest[:4],'big')%DIM
        sign=1.0 if digest[4]&1 else -1.0
        vector[idx]+=sign
    norm=float(np.linalg.norm(vector))
    return vector/norm if norm else vector

def opportunity_text(o:Opportunity)->str:
    return ' '.join([o.title,o.issuer,o.description,o.eligibility_text,' '.join(o.funding_categories)])


def embedding_text(o:Opportunity)->str:
    # Keep the semantic signal focused: title/topic dominate long boilerplate.
    return ' '.join([o.title]*6+[o.issuer]+[' '.join(o.funding_categories)]*3+[o.description[:1200],o.eligibility_text[:600]])


def _load_grants_gov()->list[Opportunity]:
    payload=json.loads((DATA/'grants_gov_open_2026-09-15.json').read_text(encoding='utf-8'))
    out=[]
    for row in payload['items']:
        categories=[CATEGORY_LABELS.get(x,x) for x in as_list(row.get('funding_categories'))]
        spans=[
            SourceSpan(field='title',quote=row.get('title') or '',source_url=row['canonical_url'],source_id=str(row['source_id'])),
            SourceSpan(field='deadline',quote=f"Close date: {row.get('close_date') or row.get('close_date_explanation') or 'not specified'}",source_url=row['canonical_url'],source_id=str(row['source_id'])),
        ]
        if row.get('eligibility_text'):
            spans.append(SourceSpan(field='eligibility',quote=str(row['eligibility_text'])[:600],source_url=row['canonical_url'],source_id=str(row['source_id'])))
        out.append(Opportunity(
            id=f"grants-{row['source_id']}",source='Grants.gov',source_id=str(row['source_id']),
            title=html.unescape(row.get('title') or 'Untitled opportunity'),issuer=html.unescape(row.get('issuer') or 'Unknown agency'),
            status='open',open_date=row.get('post_date'),close_date=row.get('close_date'),country='United States',
            description=html.unescape(row.get('description') or ''),eligibility_text=html.unescape(row.get('eligibility_text') or ''),
            eligible_applicants=as_list(row.get('eligible_applicants')),funding_categories=categories,
            award_ceiling=number(row.get('award_ceiling')),award_floor=number(row.get('award_floor')),
            currency='USD',canonical_url=row['canonical_url'],source_spans=spans,
        ))
    return out


def _load_nafosted()->list[Opportunity]:
    path=DATA/'nafosted_open_curated_2026-09-15.json'
    payload=json.loads(path.read_text(encoding='utf-8'))
    return [Opportunity.model_validate(row) for row in payload['items']]


class GrantCatalog:
    def __init__(self,opportunities:list[Opportunity]):
        self.items=opportunities
        self.by_id={x.id:x for x in opportunities}
        self.docs=[terms(opportunity_text(x)) for x in opportunities]
        self.tf=[Counter(x) for x in self.docs]
        self.avgdl=sum(map(len,self.docs))/max(1,len(self.docs))
        self.df=Counter()
        for doc in self.docs:self.df.update(set(doc))
        self.embeddings=np.stack([hash_embedding(embedding_text(x)) for x in opportunities])

    def stats(self)->dict:
        source=Counter(x.source for x in self.items)
        today=date.today()
        upcoming=sorted([x for x in self.items if x.close_date and x.close_date>=today],key=lambda x:x.close_date)[:8]
        return {
            'open_opportunities':len(self.items),'by_source':dict(source),
            'next_deadlines':[{'id':x.id,'title':x.title,'close_date':x.close_date.isoformat(),'source':x.source} for x in upcoming],
            'snapshot_date':'2026-09-15','retrieval_mode':'postgresql_fts+pgvector' if os.getenv('USE_PGVECTOR','0')=='1' else 'in_memory_bm25+local_vector',
        }

    def get(self,opportunity_id:str)->Opportunity|None:
        return self.by_id.get(opportunity_id)

    def _bm25(self,query_terms:list[str],index:int,k1:float=1.2,b:float=.75)->float:
        score=0.0; tf=self.tf[index]; dl=len(self.docs[index]); n=len(self.items)
        for term in query_terms:
            f=tf.get(term,0)
            if not f:continue
            idf=math.log(1+(n-self.df[term]+.5)/(self.df[term]+.5))
            score += idf*(f*(k1+1))/(f+k1*(1-b+b*dl/max(self.avgdl,1)))
        return score

    def search(self,profile:ResearcherProfile,limit:int=30)->list[tuple[Opportunity,float,float]]:
        query=' '.join([profile.research_interests,*profile.keywords]); qterms=terms(query); qvec=hash_embedding(query)
        lexical=np.array([self._bm25(qterms,i) for i in range(len(self.items))],dtype=np.float32)
        if lexical.max()>0:lexical=lexical/lexical.max()
        query_set=set(qterms)
        title_overlap=np.array([len(query_set & set(terms(item.title)))/max(1,len(query_set)) for item in self.items],dtype=np.float32)
        phrase_bonus=np.array([max([1.0 if fold(keyword) in fold(item.title) else 0.0 for keyword in profile.keywords] or [0.0]) for item in self.items],dtype=np.float32)
        lexical=np.minimum(1.0,0.62*lexical+0.28*title_overlap+0.10*phrase_bonus)
        semantic=self.embeddings@qvec
        ranked=np.argsort(-(0.72*lexical+0.28*np.maximum(semantic,0)))[:limit]
        return [(self.items[int(i)],float(lexical[int(i)]),float(max(semantic[int(i)],0))) for i in ranked]


def check_eligibility(profile:ResearcherProfile,o:Opportunity)->EligibilityCheck:
    reasons=[]; missing=[]
    if o.close_date and o.close_date<date.today():
        return EligibilityCheck(verdict='ineligible',reasons=['Cơ hội đã quá hạn theo ngày đóng trong nguồn.'])
    if profile.requested_budget and o.award_ceiling and profile.requested_budget>o.award_ceiling:
        return EligibilityCheck(verdict='ineligible',reasons=['Ngân sách yêu cầu vượt mức trần công bố.'])
    if o.source=='NAFOSTED':
        if fold(profile.country)!='vietnam':
            return EligibilityCheck(verdict='ineligible',reasons=['Nguồn NAFOSTED yêu cầu đầu mối hoặc tổ chức phù hợp tại Việt Nam.'])
        reasons.append('Hồ sơ thuộc tổ chức nghiên cứu/đại học tại Việt Nam.')
        missing.append('Phòng KHCN xác minh điều kiện chủ trì và năng lực theo tài liệu gốc.')
        return EligibilityCheck(verdict='needs_review',reasons=reasons,missing_information=missing)
    codes=set(o.eligible_applicants)
    allowed={'private_university':{'20','21','99'},'public_university':{'06','21','99'},'research_institute':{'12','13','21','25','99'},'individual':{'21','99'}}[profile.institution_type]
    if codes and not (codes&allowed):
        return EligibilityCheck(verdict='ineligible',reasons=[f"Loại ứng viên {profile.institution_type} không khớp mã eligibility công bố: {', '.join(sorted(codes))}."])
    if codes&allowed:reasons.append('Loại ứng viên có mã tương thích trong metadata của funder.')
    else:missing.append('Nguồn chưa cung cấp mã loại ứng viên rõ ràng.')
    if o.eligibility_text:missing.append('Cần người phụ trách đọc điều kiện bổ sung trong thông báo gốc.')
    if fold(profile.country)!='united states':missing.append('Xác minh khả năng nộp từ Việt Nam hoặc yêu cầu đối tác Hoa Kỳ.')
    return EligibilityCheck(verdict='needs_review',reasons=reasons or ['Có độ phù hợp chủ đề nhưng chưa đủ căn cứ kết luận eligibility.'],missing_information=missing)


def rerank(profile:ResearcherProfile,candidates:Iterable[tuple[Opportunity,float,float]],top_k:int)->list[MatchItem]:
    query=set(terms(' '.join([profile.research_interests,*profile.keywords])))
    out=[]; today=date.today()
    for o,lexical,semantic in candidates:
        eligibility=check_eligibility(profile,o)
        if eligibility.verdict=='ineligible': eligibility_score=0.0
        elif eligibility.verdict=='eligible': eligibility_score=1.0
        else: eligibility_score=.62
        freshness=.5
        if o.close_date:
            days=max(0,(o.close_date-today).days); freshness=min(1.0,.35+days/180)
        total=.42*lexical+.28*semantic+.22*eligibility_score+.08*freshness
        overlap=sorted(query&set(terms(opportunity_text(o))))[:6]
        why=[]
        if overlap:why.append('Khớp chủ đề: '+', '.join(overlap))
        why.append('Nguồn chính thức: '+o.source)
        if o.close_date:why.append('Hạn nộp: '+o.close_date.isoformat())
        out.append(MatchItem(opportunity=o,eligibility=eligibility,score=ScoreBreakdown(total=round(total,4),lexical=round(lexical,4),semantic=round(semantic,4),eligibility=eligibility_score,freshness=round(freshness,4)),why_matched=why,citations=o.source_spans[:3]))
    out.sort(key=lambda x:x.score.total,reverse=True)
    viable=[item for item in out if item.eligibility.verdict!='ineligible']
    return (viable if len(viable)>=top_k else out)[:top_k]


@lru_cache(maxsize=1)
def get_catalog()->GrantCatalog:
    return GrantCatalog([*_load_nafosted(),*_load_grants_gov()])

