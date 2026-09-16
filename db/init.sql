CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS opportunities (
  id text PRIMARY KEY,
  source text NOT NULL,
  source_id text NOT NULL,
  title text NOT NULL,
  issuer text NOT NULL,
  status text NOT NULL,
  close_date date,
  description text NOT NULL DEFAULT '',
  eligibility_text text NOT NULL DEFAULT '',
  raw_json jsonb NOT NULL,
  embedding vector(256) NOT NULL,
  search_tsv tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', coalesce(title,'')), 'A') ||
    setweight(to_tsvector('simple', coalesce(issuer,'')), 'B') ||
    setweight(to_tsvector('simple', coalesce(eligibility_text,'')), 'B') ||
    setweight(to_tsvector('simple', coalesce(description,'')), 'C')
  ) STORED,
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(source, source_id)
);
CREATE INDEX IF NOT EXISTS opportunities_embedding_hnsw ON opportunities USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS opportunities_search_gin ON opportunities USING gin (search_tsv);
CREATE INDEX IF NOT EXISTS opportunities_status_deadline ON opportunities(status, close_date);

CREATE TABLE IF NOT EXISTS review_requests (
  id text PRIMARY KEY,
  draft_id text NOT NULL,
  opportunity_id text NOT NULL REFERENCES opportunities(id),
  status text NOT NULL CHECK (status IN ('pending','approved','changes_requested')),
  researcher_note text NOT NULL DEFAULT '',
  manager_note text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now(),
  decided_at timestamptz
);
