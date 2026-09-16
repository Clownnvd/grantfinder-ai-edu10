from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from grantfinder.pgvector_store import DEFAULT_DATABASE_URL,ingest

def main():
    p=argparse.ArgumentParser();p.add_argument('--database-url',default=DEFAULT_DATABASE_URL);args=p.parse_args()
    count=ingest(args.database_url);print(f'Ingested {count} open opportunities into PostgreSQL + pgvector.')
if __name__=='__main__':main()
