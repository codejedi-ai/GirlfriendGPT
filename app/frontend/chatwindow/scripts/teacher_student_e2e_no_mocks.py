"""STRICT no-mocks teacher/student e2e test.

Refuses to run unless the real LLM is wired and reachable. There is no
silent fallback. Cannot be cheated by a missing dep or unset env var —
both produce a clear error and an exit code of 2.

Default target is a local OpenAI-compatible endpoint (Ollama at
http://localhost:11434/v1 / llama.cpp / vLLM / LM Studio).

Environment:
    HARNESS_LLM_BASE_URL   default http://localhost:11434/v1
    HARNESS_LLM_MODEL      default llama3.1:8b
    HARNESS_LLM_API_KEY    default "local" (Ollama ignores it)

Or set OPENAI_API_BASE + HF_TOKEN + CONFIGCLAW_AGENT_MODEL for HF.

How the test works:

  PHASE 1 (cold)  — 3 scrape requests. Each step in the dispatcher's
                    reason-and-act loop is a real LLM call. The teacher
                    grades each reply against ground truth derived from
                    the synthesizer's contract — independently of the
                    padawan's code path.
  PHASE 2 (promote)
                  — reflection compiles the YAML workflow and code-gens a
                    Python module from the recorded traces. (The codegen
                    can use the real LLM or the deterministic templater;
                    default is deterministic so the test focuses on
                    proving the *decision* loop is real-LLM. Set
                    HARNESS_USE_REAL_CODEGEN=1 to also exercise the LLM
                    codegen path.)
  PHASE 3 (warm)  — 3 unseen URLs. The warm path skips the LLM and
                    replays the promoted artifact. Teacher grades the
                    output. A non-scrape "specificity" intent confirms
                    the real LLM doesn't over-trigger the learned tool.

Exit codes:
    0 — every grade PASSED and the LLM was real on every cold step.
    1 — at least one grade FAILED.
    2 — environment is not ready (no SDK, endpoint unreachable, etc.)
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness.envelope import InboundEnvelope, TrustLevel
from harness.factory import HarnessConfig, build_harness
from harness.reflection import reflect


# ===== teacher's ground truth (independent of padawan) =====


def _truth_for(url: str) -> dict[str, str]:
    seed = hashlib.md5(url.encode()).hexdigest()[:8]
    return {
        "price": f"${int(seed, 16) % 9000 + 1000}",
        "bedrooms": str(int(seed[0], 16) % 5 + 1),
        "address": f"{seed} Main St",
    }


def _expected_formatted(truth: dict[str, str]) -> str:
    return (
        f"Price: {truth['price']}\n"
        f"Bedrooms: {truth['bedrooms']}\n"
        f"Address: {truth['address']}"
    )


@dataclass
class Scenario:
    name: str
    intent: str
    truth: dict[str, str] | None
    should_be_warm: bool


COLD_URLS = [
    "https://example.com/listing/101",
    "https://example.com/listing/202",
    "https://example.com/listing/303",
]
WARM_URLS = [
    "https://example.com/listing/9999",
    "https://example.com/listing/12345",
    "https://example.com/listing/77",
]
UNRELATED_INTENT = "what is the capital of france"


def make_scenarios() -> list[Scenario]:
    out: list[Scenario] = []
    for u in COLD_URLS:
        out.append(
            Scenario(
                name=f"cold:{u.rsplit('/', 1)[-1]}",
                intent=f"scrape {u}",
                truth=_truth_for(u),
                should_be_warm=False,
            )
        )
    for u in WARM_URLS:
        out.append(
            Scenario(
                name=f"warm:{u.rsplit('/', 1)[-1]}",
                intent=f"scrape {u}",
                truth=_truth_for(u),
                should_be_warm=True,
            )
        )
    out.append(
        Scenario(
            name="specificity:unrelated",
            intent=UNRELATED_INTENT,
            truth=None,
            should_be_warm=False,
        )
    )
    return out


def grade_one(scenario: Scenario, reply_text: str) -> tuple[bool, str, str]:
    if scenario.truth is None:
        if "Price:" in reply_text or "Bedrooms:" in reply_text:
            return (
                False,
                "(no listing fields)",
                "over-triggered on non-scrape intent",
            )
        return (True, "(no listing fields)", "")
    expected = _expected_formatted(scenario.truth)
    if reply_text.strip() == expected.strip():
        return (True, expected, "")

    missing: list[str] = []
    wrong: list[str] = []
    for field, value in scenario.truth.items():
        label = field.title()
        marker = f"{label}: "
        idx = reply_text.find(marker)
        if idx < 0:
            missing.append(label)
            continue
        end = reply_text.find("\n", idx)
        got = reply_text[idx + len(marker) : end if end >= 0 else None]
        if got.strip() != value:
            wrong.append(f"{label}: expected {value!r}, got {got!r}")
    notes_parts: list[str] = []
    if missing:
        notes_parts.append(f"missing fields: {', '.join(missing)}")
    if wrong:
        notes_parts.append("; ".join(wrong))
    return (False, expected, " | ".join(notes_parts) or "shape mismatch")


# ===== strict environment preflight =====


def _hard_fail(msg: str) -> None:
    print()
    print("=" * 78)
    print("  STRICT NO-MOCKS PREFLIGHT FAILED")
    print("=" * 78)
    print(f"  {msg}")
    print()
    print("  Required setup:")
    print("    1. Activate the project venv (has the openai SDK).")
    print("       source .venv/bin/activate")
    print("    2. Ensure Ollama is serving on 127.0.0.1:11434.")
    print("       ollama serve   # if not already running")
    print("    3. Use one of your installed models (from `ollama list`):")
    print("       qwen3.5:latest   — fast, 6.6 GB  (recommended default)")
    print("       gemma4:latest    — 9.6 GB")
    print("       qwen3.6:latest   — 23 GB, best quality, slowest")
    print("    4. Re-run:")
    print("       HARNESS_LLM_MODEL=qwen3.5:latest \\")
    print("       python3 scripts/teacher_student_e2e_no_mocks.py")
    print()
    print("  Override the endpoint if you're using a non-Ollama backend:")
    print("    HARNESS_LLM_BASE_URL=http://localhost:8080/v1   # llama.cpp / vLLM")
    print("    HARNESS_LLM_API_KEY=local                       # ignored locally")
    print()
    sys.exit(2)


async def _preflight() -> None:
    # The factory imports do the SDK availability check; we verify here
    # so the error is loud + actionable.
    try:
        from harness import _llm
    except Exception as exc:
        _hard_fail(f"failed to import harness LLM module: {exc!r}")
    if not _llm.REAL_AVAILABLE:
        _hard_fail(
            "openai SDK not installed (`pip install openai>=1.0`). "
            "Strict mode refuses to fall back to the deterministic policy."
        )
    if not _llm.is_configured():
        _hard_fail("No LLM endpoint configured (set HARNESS_LLM_BASE_URL+_MODEL).")
    ok = await _llm.is_reachable(timeout_s=3.0)
    if not ok:
        _hard_fail(
            f"LLM endpoint unreachable at {_llm.configured_base_url()!r}. "
            "Start Ollama (or your local llama.cpp / vLLM server)."
        )


# ===== padawan driver =====


async def _ask_padawan(bundle, intent: str):
    env = InboundEnvelope(
        source_channel="cli",
        source_address="teacher",
        trust=TrustLevel.ADMIN,
        payload={"text": intent},
    )
    t0 = time.perf_counter()
    result = await bundle.dispatcher.handle(env)
    wall = (time.perf_counter() - t0) * 1000.0
    return result, wall


# ===== main =====


def banner(s: str) -> None:
    print()
    print("=" * 78)
    print(f"  {s}")
    print("=" * 78)


async def main() -> int:
    # ---- 0. Set strict-mode defaults BEFORE the factory reads env ----
    # If the user hasn't set HARNESS_LLM_BASE_URL we default to Ollama so the
    # preflight is meaningful. We never default to a mock.
    os.environ.setdefault("HARNESS_LLM_BASE_URL", "http://localhost:11434/v1")
    os.environ.setdefault("HARNESS_LLM_MODEL", "qwen3.5:latest")
    os.environ.setdefault("HARNESS_LLM_API_KEY", "local")
    # This test grades against deterministic synthetic fixtures, so it must use
    # the stub scraper regardless of whether crawl4ai is installed locally —
    # keeps CI and local identical.
    os.environ["HARNESS_USE_REAL_SCRAPER"] = "0"

    await _preflight()

    run_id = time.strftime("%Y%m%d-%H%M%S")
    fs_root = ROOT / "outputs" / "teacher-student-no-mocks" / run_id
    if fs_root.exists():
        shutil.rmtree(fs_root, ignore_errors=True)
    fs_root.mkdir(parents=True, exist_ok=True)

    cfg = HarnessConfig.from_env()
    cfg.filesystem_store_root = fs_root
    bundle = await build_harness(cfg)

    banner("MODE REPORT")
    print(bundle.mode_report.pretty())

    # ---- STRICT ASSERTION: LLM must be real on this run ----
    if bundle.mode_report.llm_policy in {"mock-deterministic"}:
        print()
        print("STRICT MODE VIOLATION: LLM policy fell back to the mock.")
        print(f"  reason: {bundle.mode_report.llm_reason}")
        await bundle.shutdown()
        return 2

    real_llm_label = bundle.mode_report.llm_policy
    print()
    print(f"  > LLM is real ({real_llm_label}). Every cold-phase step will hit it.")

    scenarios = make_scenarios()
    grades: list[tuple[str, str, str, int, float, str | None, bool]] = []
    cold_tok_sum = 0
    warm_tok_sum = 0
    cold_wall_sum = 0.0
    warm_wall_sum = 0.0
    cold_n = 0
    warm_n = 0

    try:
        # ---- COLD ----
        banner("PHASE 1 — COLD (real LLM drives every step)")
        for sc in scenarios:
            if not sc.name.startswith("cold:"):
                continue
            print(f"  [...] {sc.name}  (calling real LLM, may take seconds)")
            result, wall = await _ask_padawan(bundle, sc.intent)
            reply = result.reply.payload.get("text", "")
            ok, expected, notes = grade_one(sc, reply)
            grades.append(
                (
                    sc.name,
                    "PASS" if ok else "FAIL",
                    notes,
                    result.llm_tokens,
                    wall,
                    result.reply.harness_hit,
                    result.used_harness,
                )
            )
            cold_tok_sum += result.llm_tokens
            cold_wall_sum += wall
            cold_n += 1
            print(
                f"  [{'PASS' if ok else 'FAIL'}] {sc.name:<20}  "
                f"tokens={result.llm_tokens:>6d}  wall={wall:7.1f}ms  "
                f"harness_hit={result.reply.harness_hit}"
            )
            if not ok:
                print(f"        notes:    {notes}")
                print(f"        expected: {expected!r}")
                print(f"        actual:   {reply!r}")

        # Real LLM must have actually consumed tokens on the cold path.
        if cold_tok_sum <= 0:
            print()
            print(
                "STRICT MODE VIOLATION: cold phase recorded 0 LLM tokens; "
                "the real LLM did not appear to be called."
            )
            return 2

        # ---- REFLECTION ----
        banner("PHASE 2 — REFLECTION (deterministic by default; "
               "set HARNESS_USE_REAL_CODEGEN=1 for LLM codegen)")
        reflection = await reflect(
            bundle.store, bundle.registry, bundle.tools,
            min_hits=3, codegen_enabled=True,
        )
        print(f"  promoted: {reflection.workflows_activated or '(none)'}")
        print(f"  code-genned: {reflection.generated_tools_created or '(none)'}")
        if not reflection.workflows_activated:
            print()
            print(
                "STRICT MODE VIOLATION: reflection did not promote a workflow "
                "after 3 cold runs. Check that the real LLM produced a "
                "consistent tool sequence."
            )
            return 1

        # ---- WARM + SPECIFICITY ----
        banner("PHASE 3 — WARM (replay) + specificity (real LLM said no)")
        for sc in scenarios:
            if not (
                sc.name.startswith("warm:") or sc.name.startswith("specificity:")
            ):
                continue
            print(f"  [...] {sc.name}")
            result, wall = await _ask_padawan(bundle, sc.intent)
            reply = result.reply.payload.get("text", "")
            ok, expected, notes = grade_one(sc, reply)
            if sc.name.startswith("warm:") and not result.used_harness:
                ok = False
                notes = (
                    f"{notes} | " if notes else ""
                ) + "warm path expected, harness was NOT hit"
            if sc.name.startswith("specificity:") and result.used_harness:
                ok = False
                notes = (
                    f"{notes} | " if notes else ""
                ) + f"specificity violation: hit {result.reply.harness_hit!r}"
            grades.append(
                (
                    sc.name,
                    "PASS" if ok else "FAIL",
                    notes,
                    result.llm_tokens,
                    wall,
                    result.reply.harness_hit,
                    result.used_harness,
                )
            )
            if sc.name.startswith("warm:"):
                warm_tok_sum += result.llm_tokens
                warm_wall_sum += wall
                warm_n += 1
            print(
                f"  [{'PASS' if ok else 'FAIL'}] {sc.name:<20}  "
                f"tokens={result.llm_tokens:>6d}  wall={wall:7.1f}ms  "
                f"harness_hit={result.reply.harness_hit}"
            )
            if not ok:
                print(f"        notes:    {notes}")

        # ---- VERDICT ----
        banner("TEACHER'S GRADE BOOK")
        n = len(grades)
        passed = sum(1 for g in grades if g[1] == "PASS")
        print(
            f"  scenarios: {n}  pass: {passed}  fail: {n - passed}\n"
        )
        print(
            f"  {'scenario':<22}  {'grade':<6}  {'used_h':<6}  "
            f"{'tokens':>6}  {'harness_hit':<40}"
        )
        for name, grade, _notes, tokens, _wall, hit, used in grades:
            print(
                f"  {name:<22}  {grade:<6}  "
                f"{'yes' if used else 'no':<6}  "
                f"{tokens:>6}  {str(hit or ''):<40}"
            )

        banner("AGGREGATE METRICS")
        cold_avg_tok = cold_tok_sum / max(cold_n, 1)
        warm_avg_tok = warm_tok_sum / max(warm_n, 1)
        cold_avg_wall = cold_wall_sum / max(cold_n, 1)
        warm_avg_wall = warm_wall_sum / max(warm_n, 1)
        print(f"  cold avg:  tokens={cold_avg_tok:7.1f}  wall={cold_avg_wall:7.1f}ms")
        print(f"  warm avg:  tokens={warm_avg_tok:7.1f}  wall={warm_avg_wall:7.1f}ms")

        cold_ok = all(
            g[1] == "PASS" for g in grades if g[0].startswith("cold:")
        )
        warm_ok = all(
            g[1] == "PASS" for g in grades if g[0].startswith("warm:")
        )
        spec_ok = all(
            g[1] == "PASS" for g in grades if g[0].startswith("specificity:")
        )
        token_drop = warm_avg_tok <= max(cold_avg_tok * 0.2, 1.0)
        wall_drop = warm_avg_wall <= cold_avg_wall

        banner("FINAL VERDICT (real LLM, no mocks)")
        print(f"  LLM mode:                       {real_llm_label}")
        print(f"  [G1] cold correctness:          {'PASS' if cold_ok else 'FAIL'}")
        print(f"  [G2] promotion happened:        PASS")
        print(f"  [G3] warm correctness:          {'PASS' if warm_ok else 'FAIL'}")
        print(f"  [G4] specificity:               {'PASS' if spec_ok else 'FAIL'}")
        print(f"  [C1] >=80% LLM-token drop:      {'PASS' if token_drop else 'FAIL'}")
        print(f"  [C1] wall-clock improves:       {'PASS' if wall_drop else 'FAIL'}")
        return 0 if (cold_ok and warm_ok and spec_ok and token_drop and wall_drop) else 1
    finally:
        await bundle.shutdown()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
