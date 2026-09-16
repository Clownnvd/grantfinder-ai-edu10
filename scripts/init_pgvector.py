from __future__ import annotations
import argparse
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from grantfinder.pgvector_store import DEFAULT_DATABASE_URL,connect
def main():
    p=argparse.ArgumentParser();p.add_argument('--database-url',default=DEFAULT_DATABASE_URL);args=p.parse_args()
    sql=(ROOT/'db'/'init.sql').read_text(encoding='utf-8-sig')
    with connect(args.database_url) as conn:
        with conn.cursor() as cur:cur.execute(sql)
        conn.commit()
    print('pgvector schema initialized')
if __name__=='__main__':main()
