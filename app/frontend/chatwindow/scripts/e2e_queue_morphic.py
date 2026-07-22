"""Morphic end-to-end test — the way a human actually uses the service.

No direct ``dispatcher.handle`` calls. Every message takes the real path:

    channel adapter  ->  agents:inbound (queue)  ->  DispatcherWorker
        ->  dispatcher reason-act loop  ->  tickets on agents:tasks (one per
            tool-agent task)  ->  agents:replies (queue)  ->  back to the
            originating channel

Two surfaces are exercised — a CLI client and a Frontend (browser-term)
client — and the test asserts they are *morphic*: the same intent produces a
byte-identical reply regardless of which surface sent it, because both publish
to the same queue and are served by the same worker.

Phases:
  COLD  — 3 scrape intents submitted via the CLI surface. The worker drives
          the real LLM, opens tickets for fetch_url/parse_listing/format_listing,
          and after the 3rd, reflection promotes a workflow + generated tool.
  WARM  — unseen URLs submitted via the FRONTEND surface; served from the
          promoted tool (harness hit, no LLM).
  MORPHIC — same URL via CLI and via Frontend; replies must be identical.
  SPECIFICITY — an unrelated intent must NOT trigger the learned scraper.

Exit codes: 0 all pass · 1 a grade failed · 2 environment not ready.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness.bus import (
    STREAM_INBOUND,
    STREAM_REPLIES,
    STREAM_RESULTS,
    STREAM_TASKS,
)
from harness.envelope import TrustLevel
from harness.factory import HarnessConfig, build_harness
from harness.runtime import ChannelClient, DispatcherAgent, TaskAgent


# ---- teacher ground truth (independent of the padawan code path) ----


def _truth_for(url: str) -> dict[str, str]:
    seed = hashlib.md5(url.encode()).hexdigest()[:8]
    return {
        "price": f"${int(seed, 16) % 9000 + 1000}",
        "bedrooms": str(int(seed[0], 16) % 5 + 1),
        "address": f"{seed} Main St",
    }


def _expected(url: str) -> str:
    t = _truth_for(url)
    return f"Price: {t['price']}\nBedrooms: {t['bedrooms']}\nAddress: {t['address']}"


COLD_URLS = [
    "https://example.com/listing/101",
    "https://example.com/listing/202",
    "https://example.com/listing/303",
]
WARM_URLS = ["https://example.com/listing/9999", "https://example.com/listing/77"]
MORPHIC_URL = "https://example.com/listing/555"
UNRELATED = "what is the capital of france"


def banner(s: str) -> None:
    print("\n" + "=" * 78 + f"\n  {s}\n" + "=" * 78)


PASS = "[PASS]"
FAIL = "[FAIL]"


async def _clear_learned_state(bundle) -> None:
    """Clean slate for a genuine cold start: wipe learned state + in-memory
    registry. We do NOT touch the default streams — this run uses its own
    isolated stream namespace, so a gateway/UI worker can keep running."""
    for prefix in ("workflows", "generated", "traces"):
        for key in list(bundle.store.list(prefix)):
            bundle.store.delete(key)
    bundle.registry.reset()


async def _drain_stream(bundle, stream: str, max_idle: float = 0.8) -> list[dict]:
    """Collect every message currently on a stream (observer consumer group)."""
    out: list[dict] = []
    agen = bundle.bus.consume(stream, "observer", "obs-1")
    try:
        while True:
            try:
                msg = await asyncio.wait_for(agen.__anext__(), timeout=max_idle)
            except (asyncio.TimeoutError, StopAsyncIteration):
                break
            out.append(msg.data)
            await bundle.bus.ack(stream, "observer", msg.message_id)
    finally:
        await agen.aclose()
    return out


async def main() -> int:
    os.environ.setdefault("HARNESS_LLM_BASE_URL", "http://localhost:11434/v1")
    os.environ.setdefault("HARNESS_LLM_MODEL", "qwen3.5:latest")
    os.environ.setdefault("HARNESS_LLM_API_KEY", "local")
    # Deterministic synthetic fixtures -> force the stub scraper so the run is
    # identical whether or not crawl4ai is installed (CI == local).
    os.environ["HARNESS_USE_REAL_SCRAPER"] = "0"

    # Preflight: refuse to run mocked.
    from harness import _llm

    if not _llm.REAL_AVAILABLE or not _llm.is_configured():
        print("environment not ready: no real LLM configured")
        return 2
    if not await _llm.is_reachable(timeout_s=3.0):
        print(f"environment not ready: LLM unreachable at {_llm.configured_base_url()}")
        return 2

    bundle = await build_harness(HarnessConfig.from_env())
    banner("MODE REPORT")
    print(bundle.mode_report.pretty())
    if bundle.mode_report.llm_policy == "mock-deterministic":
        print("\nSTRICT VIOLATION: LLM fell back to mock.")
        await bundle.shutdown()
        return 2

    await _clear_learned_state(bundle)

    # Isolated stream namespace so this graded run is hermetic — a running
    # gateway/UI agent on the default streams won't steal our messages.
    suffix = f"e2e-{int(time.time())}"
    s_inbound = f"{STREAM_INBOUND}:{suffix}"
    s_tasks = f"{STREAM_TASKS}:{suffix}"
    s_results = f"{STREAM_RESULTS}:{suffix}"
    s_replies = f"{STREAM_REPLIES}:{suffix}"

    # The full multi-agent runtime: dispatcher (router/finalizer) + scraper
    # (task-specific agent). Same flow the gateway/CLI use.
    dispatcher_agent = DispatcherAgent(
        bundle.bus,
        store=bundle.store,
        registry=bundle.registry,
        tools=bundle.tools,
        reflect_min_hits=3,
        inbound_stream=s_inbound,
        tasks_stream=s_tasks,
        results_stream=s_results,
        replies_stream=s_replies,
    )
    scraper_agent = TaskAgent(
        bundle.bus, bundle.dispatcher, bundle.recorder, capability="scraper",
        tasks_stream=s_tasks, results_stream=s_results,
    )
    dispatcher_agent.start()
    scraper_agent.start()

    # Two human-facing surfaces. Same class, same queue path.
    cli = ChannelClient(
        bundle.bus, name="cli", trust=TrustLevel.ADMIN,
        inbound_stream=s_inbound, replies_stream=s_replies,
    )
    frontend = ChannelClient(
        bundle.bus, name="browser-term", trust=TrustLevel.USER,
        inbound_stream=s_inbound, replies_stream=s_replies,
    )
    cli.start()
    frontend.start()
    await asyncio.sleep(0.3)  # let consumer groups attach

    results: list[tuple[str, bool, str]] = []

    def grade(label: str, url: str | None, reply, want_warm: bool) -> None:
        text = reply.text.strip()
        ok = True
        notes = []
        if url is not None:
            if text != _expected(url).strip():
                ok = False
                notes.append(f"text mismatch (got {text!r})")
            warm = reply.harness_hit is not None
            if warm != want_warm:
                ok = False
                notes.append(
                    f"expected {'warm' if want_warm else 'cold'}, "
                    f"got harness_hit={reply.harness_hit!r}"
                )
        else:  # specificity
            if "Price:" in text or "Bedrooms:" in text:
                ok = False
                notes.append("over-triggered scraper on unrelated intent")
            if reply.harness_hit is not None:
                ok = False
                notes.append(f"unexpected harness_hit={reply.harness_hit!r}")
        results.append((label, ok, "; ".join(notes)))
        hit = reply.harness_hit or "-"
        print(
            f"  {PASS if ok else FAIL} {label:<26} hit={hit:<34} "
            + (f"text={text!r}" if not ok else "")
        )

    try:
        banner("PHASE 1 — COLD via CLI surface (queue -> worker -> real LLM)")
        for url in COLD_URLS:
            r = await cli.request(f"scrape {url}", address="dev-terminal")
            grade(f"cold/cli {url.rsplit('/',1)[-1]}", url, r, want_warm=False)

        # Reflection runs in the worker *after* it publishes each reply, so
        # poll briefly for the promotion to land (it's a background step).
        promoted: list[str] = []
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            promoted = [
                w.id
                for w in bundle.registry.list_workflows()
                if w.status.value in ("active", "compiled")
            ]
            if promoted:
                break
            await asyncio.sleep(0.3)
        print(f"\n  reflection promoted: {promoted or '(none)'}")
        if not promoted:
            print("  STRICT VIOLATION: no workflow promoted after 3 cold runs")
            return 1

        banner("PHASE 2 — WARM via FRONTEND surface (served from learned tool)")
        for url in WARM_URLS:
            r = await frontend.request(f"scrape {url}", address="browser-tab-1")
            grade(f"warm/frontend {url.rsplit('/',1)[-1]}", url, r, want_warm=True)

        banner("PHASE 3 — MORPHIC: same intent, CLI vs Frontend, must match")
        r_cli = await cli.request(f"scrape {MORPHIC_URL}", address="dev-terminal")
        r_fe = await frontend.request(f"scrape {MORPHIC_URL}", address="browser-tab-1")
        identical = r_cli.text == r_fe.text and r_cli.text.strip() == _expected(
            MORPHIC_URL
        ).strip()
        both_warm = (
            r_cli.harness_hit is not None and r_fe.harness_hit is not None
        )
        ok = identical and both_warm
        results.append(("morphic cli==frontend", ok, "" if ok else "replies differ"))
        print(f"  {PASS if ok else FAIL} morphic cli==frontend")
        print(f"        cli      -> {r_cli.text!r}  (hit={r_cli.harness_hit})")
        print(f"        frontend -> {r_fe.text!r}  (hit={r_fe.harness_hit})")

        banner("PHASE 4 — SPECIFICITY via FRONTEND (must not over-trigger)")
        r = await frontend.request(UNRELATED, address="browser-tab-1")
        grade("specificity/frontend", None, r, want_warm=False)

        # ---- show the dispatch flow: dispatcher -> task agent -> results ----
        banner("DISPATCH FLOW (agents:tasks → scraper agent → agents:results)")
        dispatches = await _drain_stream(bundle, s_tasks)
        outcomes = await _drain_stream(bundle, s_results)
        print(f"  dispatcher dispatched {len(dispatches)} task(s) to a task agent")
        for d in dispatches[:3]:
            intent = (d.get("envelope", {}).get("payload", {}) or {}).get("text", "")
            print(f"    task {d.get('task_id','')[:18]:<20} capability={d.get('capability')}"
                  f"  intent={intent[:46]!r}")
        print(f"\n  scraper agent reported {len(outcomes)} result(s); tool chain per task:")
        for o in outcomes[:3]:
            chain = " -> ".join(f"{s['tool']}({s['status']})" for s in o.get("steps", [])) or "(harness replay)"
            print(f"    {o.get('task_id','')[:18]:<20} {chain}")

        banner("VERDICT")
        npass = sum(1 for _, ok, _ in results if ok)
        for label, ok, notes in results:
            print(f"  {PASS if ok else FAIL} {label}" + (f"  — {notes}" if notes else ""))
        all_ok = npass == len(results)
        print(f"\n  {npass}/{len(results)} checks passed")
        print(f"  dispatcher: dispatched {dispatcher_agent.dispatched}, "
              f"replied {dispatcher_agent.replied}  |  "
              f"scraper agent handled {scraper_agent.handled} tasks")
        print("\n  [E2E] morphic queue-driven flow: "
              + ("PASS" if all_ok else "FAIL"))
        return 0 if all_ok else 1
    finally:
        await cli.stop()
        await frontend.stop()
        await scraper_agent.stop()
        await dispatcher_agent.stop()
        await bundle.shutdown()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
