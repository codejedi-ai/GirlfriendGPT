"""Self-improving agent harness.

Multi-channel agent platform on a shared message queue. Records every tool
call as a trace, then on a reflection pass promotes repeated trace patterns
into reusable workflows (YAML) and, for hot workflows, code-genned Python tools.

See ``docs/plans/self-improving-harness-design.md`` for the design.

v0.1 scope: in-memory queue, filesystem store, deterministic codegen
templater. Interfaces shaped so Redis Streams / MinIO / Postgres / LLM
codegen swap in without changing call sites.
"""

from __future__ import annotations

__version__ = "0.1.0"
