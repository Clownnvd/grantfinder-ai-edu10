from __future__ import annotations
import json,os,re,time
from pathlib import Path
from typing import Any
AUDIT=Path(__file__).resolve().parents[1]/'artifacts'/'audit'/'llm_calls.jsonl'
NUM=re.compile(r'\b\d+(?:[.,]\d+)?\b')
def _audit(row:dict[str,Any])->None:
    AUDIT.parent.mkdir(parents=True,exist_ok=True)
    with AUDIT.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
def _new_numbers(output:str,context:str)->list[str]:
    allowed={x.replace(',','.') for x in NUM.findall(context)}|{'1','2','3'}
    return sorted({x for x in NUM.findall(output) if x.replace(',','.') not in allowed})
def improve_draft(base:dict[str,str],context:dict[str,Any])->tuple[dict[str,str],dict[str,Any]]:
    if os.getenv('USE_LLM','0')!='1' or not os.getenv('GEMINI_API_KEY'):
        return base,{'mode':'deterministic_template','model':None,'guard':'not_needed'}
    started=time.perf_counter();model=os.getenv('GEMINI_MODEL','gemini-3.7-flash');ok=False;error=None
    try:
        from google import genai
        from google.genai import types
        system='Bạn là trợ lý soạn đề xuất nghiên cứu. Chỉ dùng GROUNDED_CONTEXT. Không tạo deadline, ngân sách, eligibility, số liệu hoặc kết quả. Giữ [DRAFT_ONLY] và [NEEDS_INPUT]. Trả JSON có đúng các khóa của BASE_SECTIONS.'
        prompt='GROUNDED_CONTEXT:\n'+json.dumps(context,ensure_ascii=False)+'\nBASE_SECTIONS:\n'+json.dumps(base,ensure_ascii=False)
        response=genai.Client(api_key=os.environ['GEMINI_API_KEY']).models.generate_content(model=model,contents=prompt,config=types.GenerateContentConfig(system_instruction=system,temperature=.2,response_mime_type='application/json'))
        parsed=json.loads(response.text or '{}')
        if set(parsed)!=set(base) or not all(isinstance(v,str) for v in parsed.values()):raise ValueError('invalid_output_contract')
        invented=_new_numbers(json.dumps(parsed,ensure_ascii=False),json.dumps(context,ensure_ascii=False)+json.dumps(base,ensure_ascii=False))
        if invented:raise ValueError('number_guard_blocked:'+','.join(invented))
        ok=True;return parsed,{'mode':'gemini_grounded_rewrite','model':model,'guard':'passed'}
    except Exception as exc:
        error=f'{type(exc).__name__}: {exc}'[:240]
        return base,{'mode':'deterministic_fallback','model':model,'guard':'blocked_or_error','error':error}
    finally:_audit({'at':time.strftime('%Y-%m-%dT%H:%M:%S'),'purpose':'proposal_draft_rewrite','model':model,'ok':ok,'latency_ms':round((time.perf_counter()-started)*1000),'error':error})
