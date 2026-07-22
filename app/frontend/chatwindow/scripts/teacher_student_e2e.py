"""Teacher/padawan end-to-end test.

The Teacher is Claude: it derives the ground truth for every scenario
INDEPENDENTLY of the padawan's code path — by re-implementing what the
synthesizer (``_FakeWeb.html_for`` in ``tools.py``) is contractually
supposed to produce. The padawan is the ConfigClaw harness running
``Dispatcher`` through ``factory.build_harness``.

We test four things, in order:

  (G1) COLD CORRECTNESS — first-time scrapes produce outputs that match
       the teacher's ground truth, field-by-field.
  (G2) PROMOTION — after 3 successful cold scrapes, the reflection
       worker compiles and code-gens a workflow.
  (G3) WARM CORRECTNESS — replays on UNSEEN URLs hit the learned path
       AND still match the teacher's ground truth.
  (G4) SPECIFICITY — an unrelated intent (not a scrape) does NOT hit the
       promoted workflow. The harness must not over-generalize.

Exit code 0 iff every grade passes AND the harness's own VERIFY criteria
hold (cold-vs-warm tokens, wall-clock, harness_hit signal).
"""

from __future__ import annotations

import asyncio
import hashlib
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness.envelope import InboundEnvelope, TrustLevel
from harness.factory import HarnessConfig, build_harness
from harness.reflection import reflect


# ===== Teacher: independent ground truth =====
#
# The padawan calls ``_FakeWeb.html_for(url)`` then parses it. The teacher
# reproduces the same algorithm here so we can predict — without touching
# the padawan — exactly what ``parse_listing`` should yield and what
# ``format_listing`` should render. If the padawan's output diverges
# (compiler bug, codegen bug, replay bug), the teacher catches it.


def _truth_for(url: str) -> dict[str, str]:
    """Re-implement _FakeWeb.html_for's contract, without importing it.

    Synthesizer contract (from tools.py): seed = md5(url)[:8],
    price = ${(int(seed,16) % 9000) + 1000}, bedrooms = (int(seed[0],16) % 5) + 1,
    address = "{seed} Main St".
    """
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
    truth: dict[str, str] | None  # None means: there should be no extraction
    should_be_warm: bool          # Was the harness expected to know this by now?
    should_promote: bool          # Should this intent count toward promotion?


@dataclass
class GradeRow:
    scenario: str
    intent: str
    grade: str          # PASS / FAIL
    expected: str
    actual: str
    notes: str
    used_harness: bool
    harness_hit: str | None
    llm_tokens: int


# ===== build the test plan =====


COLD_URLS = [
    "https://example.com/listing/101",
    "https://example.com/listing/202",
    "https://example.com/listing/303",
]
WARM_URLS = [
    # Unseen during training — tests generalization.
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
                should_promote=True,
            )
        )
    for u in WARM_URLS:
        out.append(
            Scenario(
                name=f"warm:{u.rsplit('/', 1)[-1]}",
                intent=f"scrape {u}",
                truth=_truth_for(u),
                should_be_warm=True,
                should_promote=False,
            )
        )
    out.append(
        Scenario(
            name="specificity:unrelated",
            intent=UNRELATED_INTENT,
            truth=None,
            should_be_warm=False,
            should_promote=False,
        )
    )
    return out


# ===== grading =====


def grade_one(scenario: Scenario, reply_text: str) -> tuple[bool, str, str]:
    """Returns (passed, expected_str, notes)."""
    if scenario.truth is None:
        # Specificity scenario: padawan should NOT produce a scraped listing.
        if "Price:" in reply_text or "Bedrooms:" in reply_text:
            return (
                False,
                "(no listing fields)",
                "over-triggered: produced listing fields for non-scrape intent",
            )
        return (True, "(no listing fields)", "")

    expected = _expected_formatted(scenario.truth)
    if reply_text.strip() == expected.strip():
        return (True, expected, "")

    # Field-by-field analysis for a useful failure message.
    missing: list[str] = []
    wrong: list[str] = []
    for field, value in scenario.truth.items():
        label = field.title()  # "Price"
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


# ===== padawan driver =====


async def _ask_padawan(bundle, intent: str) -> tuple[Any, float]:
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
    run_id = time.strftime("%Y%m%d-%H%M%S")
    fs_root = ROOT / "outputs" / "teacher-student-e2e" / run_id
    if fs_root.exists():
        shutil.rmtree(fs_root, ignore_errors=True)
    fs_root.mkdir(parents=True, exist_ok=True)

    cfg = HarnessConfig.from_env()
    cfg.filesystem_store_root = fs_root
    bundle = await build_harness(cfg)

    banner("MODE REPORT")
    print(bundle.mode_report.pretty())

    scenarios = make_scenarios()
    grades: list[GradeRow] = []
    cold_tokens_total = 0
    warm_tokens_total = 0
    cold_wall_total = 0.0
    warm_wall_total = 0.0
    cold_count = 0
    warm_count = 0

    try:
        # ---- COLD PHASE ----
        banner("PHASE 1 — COLD: 3 first-time scrapes, teacher grades each")
        for sc in scenarios:
            if sc.name.startswith("cold:"):
                result, wall = await _ask_padawan(bundle, sc.intent)
                reply_text = result.reply.payload.get("text", "")
                ok, expected, notes = grade_one(sc, reply_text)
                grades.append(
                    GradeRow(
                        scenario=sc.name,
                        intent=sc.intent,
                        grade="PASS" if ok else "FAIL",
                        expected=expected,
                        actual=reply_text,
                        notes=notes,
                        used_harness=result.used_harness,
                        harness_hit=result.reply.harness_hit,
                        llm_tokens=result.llm_tokens,
                    )
                )
                cold_tokens_total += result.llm_tokens
                cold_wall_total += wall
                cold_count += 1
                print(
                    f"  [{('PASS' if ok else 'FAIL'):4}] {sc.name:<22}  "
                    f"used_harness={result.used_harness}  "
                    f"tokens={result.llm_tokens:5d}  "
                    f"wall={wall:6.1f}ms"
                )
                if not ok:
                    print(f"         {notes}")

        # ---- REFLECTION ----
        banner("PHASE 2 — REFLECTION: pattern detect → workflow YAML → code-gen")
        before_workflows = len(bundle.registry.list_workflows())
        reflection = await reflect(
            bundle.store,
            bundle.registry,
            bundle.tools,
            min_hits=3,
            codegen_enabled=True,
        )
        promoted_workflows = reflection.workflows_activated
        promoted_tools = reflection.generated_tools_created
        after_workflows = len(bundle.registry.list_workflows())
        print(f"  workflows before:  {before_workflows}")
        print(f"  workflows after:   {after_workflows}")
        print(f"  promoted:          {promoted_workflows or '(none)'}")
        print(f"  code-genned:       {promoted_tools or '(none)'}")
        promotion_happened = bool(promoted_workflows or promoted_tools)

        # ---- WARM PHASE ----
        banner("PHASE 3 — WARM: unseen URLs + an unrelated intent (specificity)")
        for sc in scenarios:
            if sc.name.startswith("warm:") or sc.name.startswith("specificity:"):
                result, wall = await _ask_padawan(bundle, sc.intent)
                reply_text = result.reply.payload.get("text", "")
                ok, expected, notes = grade_one(sc, reply_text)
                # For scrape warm scenarios, also enforce: must hit harness.
                if sc.name.startswith("warm:"):
                    if not result.used_harness:
                        ok = False
                        notes = (
                            (notes + " | " if notes else "")
                            + "warm path expected, but harness was NOT hit"
                        )
                # For specificity scenario, also enforce: must NOT hit harness.
                if sc.name.startswith("specificity:"):
                    if result.used_harness:
                        ok = False
                        notes = (
                            (notes + " | " if notes else "")
                            + f"specificity violation: harness hit {result.reply.harness_hit!r}"
                        )
                grades.append(
                    GradeRow(
                        scenario=sc.name,
                        intent=sc.intent,
                        grade="PASS" if ok else "FAIL",
                        expected=expected,
                        actual=reply_text,
                        notes=notes,
                        used_harness=result.used_harness,
                        harness_hit=result.reply.harness_hit,
                        llm_tokens=result.llm_tokens,
                    )
                )
                if sc.name.startswith("warm:"):
                    warm_tokens_total += result.llm_tokens
                    warm_wall_total += wall
                    warm_count += 1
                print(
                    f"  [{('PASS' if ok else 'FAIL'):4}] {sc.name:<22}  "
                    f"used_harness={result.used_harness}  "
                    f"hit={str(result.harness_hit) if hasattr(result, 'harness_hit') else result.reply.harness_hit}  "
                    f"tokens={result.llm_tokens:5d}  wall={wall:6.1f}ms"
                )
                if not ok:
                    print(f"         {notes}")

        # ---- GRADING TABLE ----
        banner("TEACHER'S GRADE BOOK")
        passed = sum(1 for g in grades if g.grade == "PASS")
        failed = sum(1 for g in grades if g.grade == "FAIL")
        print(f"  scenarios: {len(grades)}  pass: {passed}  fail: {failed}")
        print()
        print(
            f"  {'scenario':<22}  {'grade':<6}  {'used_h':<6}  "
            f"{'tokens':>6}  {'harness_hit':<40}"
        )
        for g in grades:
            print(
                f"  {g.scenario:<22}  {g.grade:<6}  "
                f"{'yes' if g.used_harness else 'no':<6}  "
                f"{g.llm_tokens:>6}  {str(g.harness_hit or ''):<40}"
            )

        banner("AGGREGATE METRICS")
        cold_avg_tok = cold_tokens_total / max(cold_count, 1)
        warm_avg_tok = warm_tokens_total / max(warm_count, 1)
        cold_avg_wall = cold_wall_total / max(cold_count, 1)
        warm_avg_wall = warm_wall_total / max(warm_count, 1)
        print(
            f"  cold avg:  llm_tokens={cold_avg_tok:7.1f}  wall={cold_avg_wall:7.1f}ms"
        )
        print(
            f"  warm avg:  llm_tokens={warm_avg_tok:7.1f}  wall={warm_avg_wall:7.1f}ms"
        )
        token_drop_ok = warm_avg_tok <= cold_avg_tok * 0.2 + 1e-9
        wall_drop_ok = warm_avg_wall <= cold_avg_wall

        banner("FINAL VERDICT")
        print(f"  [G1] cold correctness:        "
              f"{'PASS' if all(g.grade == 'PASS' for g in grades if g.scenario.startswith('cold:')) else 'FAIL'}")
        print(f"  [G2] promotion happened:      "
              f"{'PASS' if promotion_happened else 'FAIL'}")
        print(f"  [G3] warm correctness:        "
              f"{'PASS' if all(g.grade == 'PASS' for g in grades if g.scenario.startswith('warm:')) else 'FAIL'}")
        print(f"  [G4] specificity (no over-trigger):  "
              f"{'PASS' if all(g.grade == 'PASS' for g in grades if g.scenario.startswith('specificity:')) else 'FAIL'}")
        print(f"  [C1] >=80% LLM-token drop:    {'PASS' if token_drop_ok else 'FAIL'}")
        print(f"  [C1] wall-clock improves:     {'PASS' if wall_drop_ok else 'FAIL'}")

        all_ok = (
            all(g.grade == "PASS" for g in grades)
            and promotion_happened
            and token_drop_ok
            and wall_drop_ok
        )
        return 0 if all_ok else 1
    finally:
        await bundle.shutdown()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
