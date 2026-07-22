"""CLI surface for the harness — the same queue path the browser frontend uses.

This puts each line you type onto ``agents:inbound`` (via a ChannelClient),
where the DispatcherWorker (the dispatcher agent) picks it up, opens tickets
for the tool-agents, and replies on ``agents:replies``. It is byte-for-byte
the same path as the frontend WebSocket — that is the point.

Usage:
    source .venv/bin/activate
    python3 scripts/harness_cli.py "scrape https://example.com/listing/101"
    python3 scripts/harness_cli.py            # interactive REPL
    python3 scripts/harness_cli.py --reset    # wipe learned state, then exit

It runs its own worker so it works standalone. When the gateway is also up,
both workers share the Redis consumer group and the persistent store, so
learning done here shows up there and vice versa.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import os

os.environ.setdefault("HARNESS_LLM_BASE_URL", "http://localhost:11434/v1")
os.environ.setdefault("HARNESS_LLM_MODEL", "qwen3.5:latest")
os.environ.setdefault("HARNESS_LLM_API_KEY", "local")

from harness.envelope import TrustLevel
from harness.factory import HarnessConfig, build_harness
from harness.runtime import ChannelClient, DispatcherWorker


def _kind(text: str, hit) -> str:
    if hit:
        return "WARM"
    if text.strip().startswith("Price:"):
        return "COLD"
    return "----"


async def main(argv: list[str]) -> int:
    reset = "--reset" in argv
    one_shot = [a for a in argv if not a.startswith("--")]

    bundle = await build_harness(HarnessConfig.from_env())
    print("mode:", bundle.mode_report.bus, "|", bundle.mode_report.store, "|",
          bundle.mode_report.registry_index, "|", bundle.mode_report.llm_policy)

    if reset:
        n = 0
        for prefix in ("workflows", "generated", "traces"):
            for key in list(bundle.store.list(prefix)):
                bundle.store.delete(key)
                n += 1
        bundle.registry.reset()
        print(f"reset: cleared {n} objects. next intent is a cold start.")
        await bundle.shutdown()
        return 0

    worker = DispatcherWorker(
        bundle.bus, bundle.dispatcher, bundle.recorder,
        store=bundle.store, registry=bundle.registry, tools=bundle.tools,
        reflect_min_hits=3,
    )
    worker.start()
    cli = ChannelClient(bundle.bus, name="cli", trust=TrustLevel.ADMIN)
    cli.start()
    await asyncio.sleep(0.2)

    async def ask(text: str) -> None:
        reply = await cli.request(text, address="terminal")
        tag = _kind(reply.text, reply.harness_hit)
        hit = f"  [{reply.harness_hit}]" if reply.harness_hit else ""
        print(f"\n[{tag}]{hit}\n{reply.text}\n")

    try:
        if one_shot:
            await ask(" ".join(one_shot))
        else:
            print("harness CLI — type an intent, or 'quit'. "
                  "e.g. scrape https://example.com/listing/101")
            loop = asyncio.get_running_loop()
            while True:
                line = await loop.run_in_executor(None, lambda: input("you> "))
                if line.strip().lower() in {"quit", "exit"}:
                    break
                if line.strip():
                    await ask(line.strip())
    finally:
        await cli.stop()
        await worker.stop()
        await bundle.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
