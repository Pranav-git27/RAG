-- secOwasp — one-time schema initialisation (Supabase / Postgres + pgvector)
--
-- HOW TO RUN:
--   1. Open your Supabase project → SQL Editor → New query.
--   2. Paste this entire file → Run.
--
-- Idempotent: every statement uses IF NOT EXISTS, so re-running is safe.
-- Tables created: documents, conversations, messages, audit_logs.


-- ── Required extensions ───────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;     -- pgvector: vector similarity search
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()


-- ── documents: the vector store (replaces Chroma) ─────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content         TEXT        NOT NULL,
    embedding       VECTOR(768),                          -- MRL-truncated gemini-embedding-2
    owasp_category  TEXT,
    chunk_type      TEXT,
    target_language TEXT,
    cwe_id          TEXT,
    severity        TEXT,
    source          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- HNSW index for fast approximate-nearest-neighbour cosine search.
CREATE INDEX IF NOT EXISTS documents_embedding_idx
    ON documents USING hnsw (embedding vector_cosine_ops);


-- ── conversations ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS conversations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS conversations_created_at_idx
    ON conversations (created_at DESC);


-- ── messages ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    sources         JSONB,                                -- retrieved doc refs used for the answer
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS messages_conversation_idx
    ON messages (conversation_id);


-- ── audit_logs ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id          BIGSERIAL PRIMARY KEY,
    event_type  TEXT,                                    -- e.g. 'search', 'ingest'
    query       TEXT,
    n_results   INTEGER,
    latency_ms  INTEGER,
    status      TEXT,                                    -- 'ok' | 'error'
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS audit_logs_created_at_idx
    ON audit_logs (created_at DESC);


-- ── updated_at trigger for conversations ─────────────────────────────────
CREATE OR REPLACE FUNCTION touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS conversations_touch_updated_at ON conversations;
CREATE TRIGGER conversations_touch_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
