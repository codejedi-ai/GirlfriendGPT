-- 004_harness_tables.sql
-- Self-improving harness: trace index, workflow registry, generated-tool registry.
-- Truth lives in MinIO; these tables are the queryable index.
--
-- See docs/plans/self-improving-harness-design.md §9 and
-- app/agents/harness/_postgres_index.py for the runtime that owns these tables.

CREATE TABLE IF NOT EXISTS harness_trace_index (
    session_id        TEXT PRIMARY KEY,
    intent_hash       TEXT NOT NULL,
    tool_seq_hash     TEXT NOT NULL,
    succeeded         BOOLEAN NOT NULL,
    minio_path        TEXT NOT NULL,
    recorded_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS harness_trace_index_intent_seq
    ON harness_trace_index(intent_hash, tool_seq_hash) WHERE succeeded;

CREATE TABLE IF NOT EXISTS harness_workflows (
    workflow_id       TEXT PRIMARY KEY,
    version           INT NOT NULL,
    status            TEXT NOT NULL,
    intent_hash       TEXT NOT NULL,
    hits              INT NOT NULL DEFAULT 0,
    last_used_at      TIMESTAMPTZ,
    minio_path        TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS harness_workflows_intent
    ON harness_workflows(intent_hash) WHERE status IN ('active', 'compiled');

CREATE TABLE IF NOT EXISTS harness_generated_tools (
    tool_id           TEXT PRIMARY KEY,
    workflow_id       TEXT NOT NULL REFERENCES harness_workflows(workflow_id)
                                    ON DELETE CASCADE,
    version           INT NOT NULL,
    status            TEXT NOT NULL,
    tests_passed_at   TIMESTAMPTZ,
    disk_path         TEXT NOT NULL,
    minio_path        TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
