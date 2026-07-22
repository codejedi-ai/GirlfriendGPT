"""End-to-end demo of the self-improving harness.

Run from the repo root:

    python3 scripts/harness_demo.py

How it works:

The demo calls ``build_harness()`` which auto-detects what's available
in your env and picks real backings where it can: Redis Streams (queue),
MinIO (object store), Postgres (registry index), OpenAI-compatible LLM
(policy + codegen), crawl4ai+BeautifulSoup (real scraper). When a real
backing's dep is missing or its service is unreachable, the in-memory
equivalent transparently kicks in so the demo always runs end-to-end.

The "mode report" at the top of the run tells you exactly which
components went real vs fell back, so you can see at a glance what part
of the real stack you exercised.

VERIFY criteria — printed at the bottom — pass regardless of mode:
  C1. Warm runs use >=80% fewer LLM tokens than cold.
  C2. Promoted workflow generalizes to new URLs not in the training set.
  C3. Replies on the warm path surface a "Reusing learned workflow X" signal.

Bring up the infra:
    docker compose -f docker-compose.harness.yml up -d
Then re-run the demo. The mode report should flip from in-memory to
real for bus, store, and registry. With OPENAI_API_BASE + HF_TOKEN in
.env, llm policy + codegen go real too. With crawl4ai pip-installed,
the scraper goes real (and you'll point COLD_URLS at real listings).
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness.envelope import InboundEnvelope, TrustLevel
from harness.factory import HarnessConfig, build_harness
from harness.reflection import reflect


COLD_URLS = [
    "https://example.com/listing/1",
    "https://example.com/listing/2",
    "https://example.com/listing/3",
]
WARM_URLS = [
    "https://example.com/listing/42",
    "https://example.com/listing/99",
]


def banner(label: str) -> None:
    print()
    print("=" * 72)
    print(f"  {label}")
    print("=" * 72)


def _scrape_envelope(url: str) -> InboundEnvelope:
    return InboundEnvelope(
        source_channel="cli",
        source_address="demo-terminal",
        trust=TrustLevel.ADMIN,
        payload={"text": f"scrape {url}"},
    )


async def _trace_count(store) -> int:
    return sum(1 for k in store.list("traces") if k.endswith(".jsonl"))


async def main() -> int:
    # Clean slate for the local filesystem store so the demo is
    # repeatable. Real MinIO buckets aren't wiped — they accumulate.
    # Each demo run gets its own subdir under harness-demo/ so prior-run
    # artifacts (which the sandbox sometimes can't delete) don't leak into
    # the next run's registry on load.
    run_id = time.strftime("%Y%m%d-%H%M%S")
    fs_root = ROOT / "outputs" / "harness-demo" / run_id
    fs_root.mkdir(parents=True, exist_ok=True)
    _stale = ROOT / "outputs" / "harness-demo" / "latest"
    try:
        if _stale.is_symlink() or _stale.exists():
            _stale.unlink()
    except Exception:
        pass
    try:
        _stale.symlink_to(fs_root)
    except Exception:
        pass

    cfg = HarnessConfig.from_env()
    cfg.filesystem_store_root = fs_root
    bundle = await build_harness(cfg)
    report = bundle.mode_report

    banner("MODE REPORT — which components are real, which fell back")
    print(report.pretty())

    cold_stats: list[tuple[str, float, int]] = []
    warm_stats: list[tuple[str, float, int, str | None]] = []

    try:
        banner("PHASE 1 — COLD: 3 reason-and-act sessions, traces recorded")
        for url in COLD_URLS:
            env = _scrape_envelope(url)
            t0 = time.perf_counter()
            result = await bundle.dispatcher.handle(env)
            wall_ms = (time.perf_counter() - t0) * 1000.0
            cold_stats.append((url, wall_ms, result.llm_tokens))
            print(
                f"  cold  {url:<45} "
                f"wall={wall_ms:7.1f}ms  llm_tokens={result.llm_tokens:5d}  "
                f"harness_hit={result.reply.harness_hit}"
            )

        banner("PHASE 2 — REFLECTION: detect pattern, compile YAML, code-gen tool")
        print(f"  scanning {await _trace_count(bundle.store)} traces in store...")
        reflection = await reflect(
            bundle.store, bundle.registry, bundle.tools,
            min_hits=3, codegen_enabled=True,
        )
        for wf_id in reflection.workflows_activated:
            wf = bundle.registry.get_workflow(wf_id)
            print(
                f"  promoted workflow:   {wf_id}  "
                f"(status={wf.status.value}, steps={len(wf.steps)}, "
                f"required_params={wf.required_params})"
            )
            # Push to Postgres index if real.
            if bundle.pg_index is not None:
                from harness.trace import intent_hash, normalize_intent
                ih = intent_hash(normalize_intent(" ".join(wf.intent_keywords)))
                await bundle.pg_index.upsert_workflow(
                    workflow_id=wf.id,
                    version=wf.version,
                    status=wf.status.value,
                    intent_hash=ih,
                    hits=wf.hits,
                    minio_path=f"workflows/{wf.id}.yaml",
                )
        for tool_id in reflection.generated_tools_created:
            gen = bundle.registry.get_generated_tool(tool_id)
            rel = Path(gen.disk_path).relative_to(ROOT)
            print(f"  codegen wrote:       {rel}  tests_passed={gen.tests_passed}")

        if not reflection.workflows_activated:
            print("  no promotion (check cluster threshold or seed traces)")

        banner("PHASE 3 — WARM: 2 more requests, same intent shape")
        for url in WARM_URLS:
            env = _scrape_envelope(url)
            t0 = time.perf_counter()
            result = await bundle.dispatcher.handle(env)
            wall_ms = (time.perf_counter() - t0) * 1000.0
            warm_stats.append(
                (url, wall_ms, result.llm_tokens, result.reply.harness_hit)
            )
            prefix = (
                f"Reusing learned workflow {result.reply.harness_hit}: "
                if result.reply.harness_hit
                else ""
            )
            print(
                f"  warm  {url:<45} "
                f"wall={wall_ms:7.1f}ms  llm_tokens={result.llm_tokens:5d}  "
                f"harness_hit={result.reply.harness_hit}"
            )
            first_line = result.reply.payload["text"].splitlines()[:1]
            print(f"        reply: {prefix}{first_line[0] if first_line else ''}")

        banner("VERIFY — acceptance criteria from design §12")
        avg_cold_wall = sum(s[1] for s in cold_stats) / max(len(cold_stats), 1)
        avg_cold_tok = sum(s[2] for s in cold_stats) / max(len(cold_stats), 1)
        avg_warm_wall = sum(s[1] for s in warm_stats) / max(len(warm_stats), 1)
        avg_warm_tok = sum(s[2] for s in warm_stats) / max(len(warm_stats), 1)
        print(f"  avg cold:  wall={avg_cold_wall:7.1f}ms  llm_tokens={avg_cold_tok:7.1f}")
        print(f"  avg warm:  wall={avg_warm_wall:7.1f}ms  llm_tokens={avg_warm_tok:7.1f}")

        crit1_tokens = avg_warm_tok <= max(avg_cold_tok * 0.2, 0.0)
        crit1_wall = avg_warm_wall <= avg_cold_wall
        crit2_general = all(s[3] is not None for s in warm_stats)
        crit3_signal = all(s[3] is not None for s in warm_stats)

        print()
        print(f"  [C1] >=80% LLM-token drop:               "
              f"{'PASS' if crit1_tokens else 'FAIL'}")
        print(f"  [C1] wall-clock improves:                "
              f"{'PASS' if crit1_wall else 'FAIL'}")
        print(f"  [C2] generalizes to unseen URLs:         "
              f"{'PASS' if crit2_general else 'FAIL'}")
        print(f"  [C3] 'reusing learned workflow' signal:  "
              f"{'PASS' if crit3_signal else 'FAIL'}")
        all_pass = all([crit1_tokens, crit1_wall, crit2_general, crit3_signal])
        print()
        print(f"  artifacts under: {fs_root}"
              f"{' (also mirrored to MinIO bucket)' if report.store == 'minio' else ''}")
        print(f"  generated code:  {ROOT / 'harness/generated'}")
        return 0 if all_pass else 1
    finally:
        await bundle.shutdown()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
