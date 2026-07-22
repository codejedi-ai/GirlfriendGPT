"""Postgres index for the harness registry.

Truth lives in the ``Store`` (MinIO / filesystem). The index is a
queryable, restart-safe view: which workflows exist, what's their status,
their hit counts, and how to look them up by intent hash.

If the registry's index is wiped, ``backfill_from_store`` rebuilds it
by reading every workflow YAML from the store.

DDL lives in ``migrations/004_harness_tables.sql`` (alembic-compatible
plain SQL — your project uses alembic.ini).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


try:  # pragma: no cover
    import asyncpg  # type: ignore

    REAL_AVAILABLE = True
except Exception:  # noqa: BLE001
    asyncpg = None  # type: ignore[assignment]
    REAL_AVAILABLE = False


_DDL = """
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
"""


@dataclass
class WorkflowRow:
    workflow_id: str
    version: int
    status: str
    intent_hash: str
    hits: int
    minio_path: str


class PostgresHarnessIndex:
    """Async Postgres index. Pool lifecycle is the caller's responsibility."""

    def __init__(self, dsn: str) -> None:
        if not REAL_AVAILABLE:
            raise RuntimeError(
                "asyncpg not installed; install 'asyncpg>=0.29' or use "
                "the in-memory HarnessRegistry index"
            )
        self._dsn = dsn
        self._pool: Optional["asyncpg.Pool"] = None  # type: ignore[name-defined]

    async def start(self) -> None:
        self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=4)
        async with self._pool.acquire() as conn:
            await conn.execute(_DDL)

    async def stop(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def upsert_workflow(
        self,
        workflow_id: str,
        version: int,
        status: str,
        intent_hash: str,
        hits: int,
        minio_path: str,
    ) -> None:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO harness_workflows
                  (workflow_id, version, status, intent_hash, hits, minio_path)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (workflow_id) DO UPDATE SET
                  version = EXCLUDED.version,
                  status = EXCLUDED.status,
                  intent_hash = EXCLUDED.intent_hash,
                  hits = EXCLUDED.hits,
                  minio_path = EXCLUDED.minio_path
                """,
                workflow_id, version, status, intent_hash, hits, minio_path,
            )

    async def find_workflow_by_intent(self, intent_hash: str) -> Optional[WorkflowRow]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT workflow_id, version, status, intent_hash, hits, minio_path
                FROM harness_workflows
                WHERE intent_hash = $1
                  AND status IN ('active', 'compiled')
                LIMIT 1
                """,
                intent_hash,
            )
            if row is None:
                return None
            return WorkflowRow(**dict(row))

    async def bump_workflow_hits(self, workflow_id: str) -> int:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            r = await conn.fetchval(
                """
                UPDATE harness_workflows
                SET hits = hits + 1, last_used_at = now()
                WHERE workflow_id = $1
                RETURNING hits
                """,
                workflow_id,
            )
            return int(r or 0)

    async def index_trace(
        self,
        session_id: str,
        intent_hash: str,
        tool_seq_hash: str,
        succeeded: bool,
        minio_path: str,
    ) -> None:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO harness_trace_index
                  (session_id, intent_hash, tool_seq_hash, succeeded, minio_path)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (session_id) DO NOTHING
                """,
                session_id, intent_hash, tool_seq_hash, succeeded, minio_path,
            )

    async def register_generated_tool(
        self,
        tool_id: str,
        workflow_id: str,
        version: int,
        status: str,
        tests_passed: bool,
        disk_path: str,
        minio_path: str,
    ) -> None:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO harness_generated_tools
                  (tool_id, workflow_id, version, status, tests_passed_at,
                   disk_path, minio_path)
                VALUES ($1, $2, $3, $4,
                        CASE WHEN $5 THEN now() ELSE NULL END,
                        $6, $7)
                ON CONFLICT (tool_id) DO UPDATE SET
                  status = EXCLUDED.status,
                  tests_passed_at = EXCLUDED.tests_passed_at
                """,
                tool_id, workflow_id, version, status, tests_passed,
                disk_path, minio_path,
            )
