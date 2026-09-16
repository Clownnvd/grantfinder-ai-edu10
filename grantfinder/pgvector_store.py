from __future__ import annotations

import json
import os
from contextlib import contextmanager
from typing import Iterator

from grantfinder.catalog import embedding_text, get_catalog, hash_embedding, terms
from grantfinder.models import Opportunity, ResearcherProfile

DEFAULT_DATABASE_URL='postgresql://grantfinder:grantfinder_local@127.0.0.1:54329/grantfinder'

def database_url()->str|None:
    return os.getenv('DATABASE_URL')

@contextmanager
def connect(url:str|None=None)->Iterator:
    import psycopg
    with psycopg.connect(url or database_url() or DEFAULT_DATABASE_URL) as conn:
        yield conn

def vector_literal(values)->str:
    return '['+','.join(f'{float(x):.8f}' for x in values)+']'

def ingest(url:str|None=None)->int:
    catalog=get_catalog()
    with connect(url) as conn:
        with conn.cursor() as cur:
            for o in catalog.items:
                emb=vector_literal(hash_embedding(embedding_text(o)))
                cur.execute('''
                    INSERT INTO opportunities(id,source,source_id,title,issuer,status,close_date,description,eligibility_text,raw_json,embedding)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::vector)
                    ON CONFLICT (id) DO UPDATE SET title=excluded.title,issuer=excluded.issuer,status=excluded.status,
                      close_date=excluded.close_date,description=excluded.description,eligibility_text=excluded.eligibility_text,
                      raw_json=excluded.raw_json,embedding=excluded.embedding,updated_at=now()
                ''',(o.id,o.source,o.source_id,o.title,o.issuer,o.status,o.close_date,o.description,o.eligibility_text,o.model_dump_json(),emb))
        conn.commit()
    return len(catalog.items)

def search(profile:ResearcherProfile,limit:int=30,url:str|None=None)->list[tuple[Opportunity,float,float]]:
    query=' '.join([profile.research_interests,*profile.keywords]); query_or=' OR '.join(dict.fromkeys(terms(query))) or query; emb=vector_literal(hash_embedding(query))
    with connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT raw_json,
                       ts_rank_cd(search_tsv, websearch_to_tsquery('simple', %s)) AS lexical,
                       greatest(0, 1 - (embedding <=> %s::vector)) AS semantic
                FROM opportunities
                WHERE status='open' AND (close_date IS NULL OR close_date >= CURRENT_DATE)
                ORDER BY (0.65 * ts_rank_cd(search_tsv, websearch_to_tsquery('simple', %s)))
                       + (0.35 * greatest(0, 1 - (embedding <=> %s::vector))) DESC
                LIMIT %s
            ''',(query_or,emb,query_or,emb,limit))
            rows=cur.fetchall()
    max_lex=max([float(row[1] or 0) for row in rows] or [1.0]) or 1.0
    return [(Opportunity.model_validate(row[0]),min(1.0,float(row[1] or 0)/max_lex),min(1.0,max(0.0,float(row[2] or 0)))) for row in rows]

def healthy(url:str|None=None)->bool:
    try:
        with connect(url) as conn:
            with conn.cursor() as cur:cur.execute('SELECT 1');return cur.fetchone()==(1,)
    except Exception:return False
