from grantfinder.models import ResearcherProfile
from grantfinder.pgvector_store import healthy,search
assert healthy(), 'PostgreSQL/pgvector is unavailable'
rows=search(ResearcherProfile(research_interests='artificial intelligence education',keywords=['machine learning']),limit=5)
assert len(rows)==5
assert all(item.status=='open' for item,_,_ in rows)
assert all(0<=semantic<=1 for _,_,semantic in rows)
print('PGVECTOR INTEGRATION TEST PASS')
