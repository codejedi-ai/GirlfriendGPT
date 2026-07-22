"""Factory — picks real or in-memory backings based on env + availability.

The demo, the FastAPI app, and the CLI all call ``build_harness(config)``
and get back a fully wired bundle. Each component is real when its dep
is importable AND its env is set; otherwise it gracefully falls back.

The bundle's ``mode_report`` enumerates what went real vs fell back, so
the demo prints it at the top and the user knows exactly what's exercising
the real stack on any given run.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bus import InMemoryQueueBus, QueueBus
from .codegen import codegen_source as _deterministic_codegen
from .dispatcher import Dispatcher, _LLMPolicy
from .registry import HarnessRegistry
from .runner import WorkflowRunner
from .store import FilesystemStore, Store
from .tools import build_default_tool_registry
from .trace import TraceRecorder


@dataclass
class HarnessConfig:
    """Where each component connects. Each field is optional — when None,
    we attempt the real impl using env, and fall back to in-memory if that
    fails."""

    redis_url: str | None = None
    minio_endpoint: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_bucket: str = "configclaw-harness"
    postgres_dsn: str | None = None
    use_real_llm: bool = True
    use_real_scraper: bool = True
    filesystem_store_root: Path = Path("app/outputs/harness-demo")

    @classmethod
    def from_env(cls) -> "HarnessConfig":
        return cls(
            redis_url=os.environ.get("HARNESS_REDIS_URL", "redis://localhost:6379"),
            minio_endpoint=os.environ.get("HARNESS_MINIO_ENDPOINT", "localhost:9000"),
            minio_access_key=os.environ.get("HARNESS_MINIO_ACCESS_KEY", "configclaw"),
            minio_secret_key=os.environ.get("HARNESS_MINIO_SECRET_KEY", "configclaw123"),
            minio_bucket=os.environ.get("HARNESS_MINIO_BUCKET", "configclaw-harness"),
            postgres_dsn=os.environ.get(
                "HARNESS_POSTGRES_DSN",
                "postgresql://configclaw:configclaw@localhost:5432/configclaw",
            ),
            use_real_llm=os.environ.get("HARNESS_USE_REAL_LLM", "1") != "0",
            use_real_scraper=os.environ.get("HARNESS_USE_REAL_SCRAPER", "1") != "0",
        )


@dataclass
class ModeReport:
    """Which component is running real vs in-memory for this bundle."""

    bus: str = "in-memory"
    store: str = "filesystem"
    registry_index: str = "in-memory"
    llm_policy: str = "mock-deterministic"
    llm_codegen: str = "deterministic-templater"
    scraper: str = "stub"
    bus_reason: str = ""
    store_reason: str = ""
    registry_reason: str = ""
    llm_reason: str = ""
    scraper_reason: str = ""

    def pretty(self) -> str:
        lines = [
            f"  bus:             {self.bus:<14} {self.bus_reason}",
            f"  store:           {self.store:<14} {self.store_reason}",
            f"  registry index:  {self.registry_index:<14} {self.registry_reason}",
            f"  llm policy:      {self.llm_policy:<14} {self.llm_reason}",
            f"  llm codegen:     {self.llm_codegen:<14}",
            f"  scraper tools:   {self.scraper:<14} {self.scraper_reason}",
        ]
        return "\n".join(lines)


@dataclass
class HarnessBundle:
    """Everything the dispatcher needs, plus the mode_report for telemetry."""

    bus: QueueBus
    store: Store
    registry: HarnessRegistry
    recorder: TraceRecorder
    runner: WorkflowRunner
    dispatcher: Dispatcher
    tools: Any
    mode_report: ModeReport
    pg_index: Any = None  # PostgresHarnessIndex when available

    async def shutdown(self) -> None:
        # Close real backings gracefully.
        for component in (self.bus, self.pg_index):
            if component is None:
                continue
            close = getattr(component, "close", None) or getattr(component, "stop", None)
            if close is None:
                continue
            try:
                res = close()
                if hasattr(res, "__await__"):
                    await res
            except Exception:
                pass


async def build_harness(config: HarnessConfig | None = None) -> HarnessBundle:
    config = config or HarnessConfig.from_env()
    report = ModeReport()

    # ---- bus ----
    bus: QueueBus = InMemoryQueueBus()
    if config.redis_url:
        try:
            from ._redis_bus import REAL_AVAILABLE, RedisStreamBus

            if not REAL_AVAILABLE:
                report.bus_reason = "(redis SDK not installed)"
            else:
                rb = RedisStreamBus(config.redis_url)
                # Verify connectivity before committing — fall back if Redis is down.
                try:
                    await rb.length("agents:inbound")
                    bus = rb
                    report.bus = "redis"
                    report.bus_reason = f"({config.redis_url})"
                except Exception as exc:
                    await rb.close()
                    report.bus_reason = f"(redis unreachable: {type(exc).__name__})"
        except Exception as exc:  # noqa: BLE001
            report.bus_reason = f"(redis init failed: {type(exc).__name__})"

    # ---- store ----
    store: Store = FilesystemStore(config.filesystem_store_root)
    if config.minio_endpoint and config.minio_access_key and config.minio_secret_key:
        try:
            from ._minio_store import MinIOStore, REAL_AVAILABLE

            if not REAL_AVAILABLE:
                report.store_reason = "(minio SDK not installed)"
            else:
                try:
                    ms = MinIOStore(
                        endpoint=config.minio_endpoint,
                        access_key=config.minio_access_key,
                        secret_key=config.minio_secret_key,
                        bucket=config.minio_bucket,
                    )
                    # Smoke test the bucket.
                    list(ms.list("workflows"))
                    store = ms
                    report.store = "minio"
                    report.store_reason = f"({config.minio_endpoint}/{config.minio_bucket})"
                except Exception as exc:  # noqa: BLE001
                    report.store_reason = f"(minio unreachable: {type(exc).__name__})"
        except Exception as exc:  # noqa: BLE001
            report.store_reason = f"(minio init failed: {type(exc).__name__})"

    # ---- registry + pg index ----
    registry = HarnessRegistry(store)
    registry.load()
    pg_index = None
    if config.postgres_dsn:
        try:
            from ._postgres_index import PostgresHarnessIndex, REAL_AVAILABLE

            if not REAL_AVAILABLE:
                report.registry_reason = "(asyncpg not installed)"
            else:
                try:
                    pg = PostgresHarnessIndex(config.postgres_dsn)
                    await pg.start()
                    pg_index = pg
                    report.registry_index = "postgres"
                    report.registry_reason = f"({_short_dsn(config.postgres_dsn)})"
                except Exception as exc:  # noqa: BLE001
                    report.registry_reason = f"(postgres unreachable: {type(exc).__name__})"
        except Exception as exc:  # noqa: BLE001
            report.registry_reason = f"(postgres init failed: {type(exc).__name__})"

    # ---- tools (stub by default, real scraper if available) ----
    tools, _ = build_default_tool_registry()
    if config.use_real_scraper:
        try:
            from . import _real_scraper

            if _real_scraper.install_real_scraper_tools(tools):
                report.scraper = "http+bs4+llm"
                report.scraper_reason = "(real HTTP fetch + LLM extraction)"
            else:
                report.scraper_reason = "(crawl4ai or bs4 not installed)"
        except Exception as exc:  # noqa: BLE001
            report.scraper_reason = f"(real scraper failed: {type(exc).__name__})"

    # ---- LLM policy + codegen ----
    policy: Any = _LLMPolicy()
    if config.use_real_llm:
        try:
            from . import _llm

            if not _llm.is_configured():
                report.llm_reason = "(openai SDK not installed or no env set)"
            else:
                reachable = await _llm.is_reachable()
                if not reachable:
                    report.llm_reason = (
                        f"(endpoint not reachable: {_llm.configured_base_url()})"
                    )
                else:
                    policy = _llm.OpenAILLMPolicy()
                    base = _llm.configured_base_url() or ""
                    if "localhost" in base or "127.0.0.1" in base:
                        report.llm_policy = "local-openai-compat"
                        report.llm_codegen = "local-openai-compat"
                        report.llm_reason = (
                            f"({base} model={_llm.configured_model()})"
                        )
                    else:
                        report.llm_policy = "openai-compat"
                        report.llm_codegen = "openai-compat"
                        report.llm_reason = (
                            f"({base} model={_llm.configured_model()})"
                        )
        except Exception as exc:  # noqa: BLE001
            report.llm_reason = f"(llm init failed: {type(exc).__name__})"

    # ---- recorder, runner, dispatcher ----
    recorder = TraceRecorder(store=store)
    runner = WorkflowRunner(tools)
    dispatcher = Dispatcher(tools, registry, recorder, runner=runner, policy=policy)

    return HarnessBundle(
        bus=bus,
        store=store,
        registry=registry,
        recorder=recorder,
        runner=runner,
        dispatcher=dispatcher,
        tools=tools,
        mode_report=report,
        pg_index=pg_index,
    )


def _short_dsn(dsn: str) -> str:
    # Hide credentials in the mode report.
    if "@" in dsn:
        return "postgresql://***@" + dsn.split("@", 1)[1]
    return dsn
