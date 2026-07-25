"""Streamlit chron server: randomly wake the companion to check up on the user.

Owns the schedule (backend ``CHECKUP_ENABLED`` should stay off). Each tick
``POST``s ``/api/agent/reach`` with ``purpose=checkup`` so the Vite UI's
WebSocket opens talk and the LiveKit worker greets the user.

Timing is intentionally inexact: each wait is drawn uniformly from
``[min_minutes, max_minutes]`` (optional quiet-hours skip).
"""

from __future__ import annotations

import json
import logging
import random
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import requests

logger = logging.getLogger("checkup-cron")

CONFIG_FILE = Path.home() / ".gfgpt" / "checkup_cron.json"
DEFAULT_BACKEND = "http://127.0.0.1:8080"
DEFAULT_AGENT_ID = "e11a0000-0000-4000-8000-000000000001"
DEFAULT_AGENT_NAME = "Lena Van Der Meer"


@dataclass
class CronConfig:
    enabled: bool = False
    backend_url: str = DEFAULT_BACKEND
    agent_id: str = DEFAULT_AGENT_ID
    agent_name: str = DEFAULT_AGENT_NAME
    # Random wait between check-ups (minutes). Never exact.
    min_minutes: float = 20.0
    max_minutes: float = 50.0
    # Extra ± jitter fraction applied after the uniform draw (0–0.4 typical).
    jitter_frac: float = 0.15
    # Quiet hours (local): skip firing; roll a short wait instead.
    quiet_start_hour: int = 23  # 23:00
    quiet_end_hour: int = 7  # 07:00
    respect_quiet_hours: bool = True
    auto_answer: bool = True
    message: str = "is checking up on you"


@dataclass
class CronStatus:
    running: bool = False
    next_fire_at: float | None = None
    last_fire_at: float | None = None
    last_result: dict[str, Any] | None = None
    last_error: str | None = None
    fires: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)


def load_cron_config() -> CronConfig:
    if not CONFIG_FILE.exists():
        return CronConfig()
    try:
        raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return CronConfig()
    base = CronConfig()
    for key in asdict(base):
        if key in raw:
            setattr(base, key, raw[key])
    # Keep min <= max
    if base.min_minutes > base.max_minutes:
        base.min_minutes, base.max_minutes = base.max_minutes, base.min_minutes
    base.min_minutes = max(1.0, float(base.min_minutes))
    base.max_minutes = max(base.min_minutes, float(base.max_minutes))
    base.jitter_frac = min(0.5, max(0.0, float(base.jitter_frac)))
    return base


def save_cron_config(cfg: CronConfig) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")


def in_quiet_hours(cfg: CronConfig, *, now: datetime | None = None) -> bool:
    if not cfg.respect_quiet_hours:
        return False
    now = now or datetime.now()
    start = int(cfg.quiet_start_hour) % 24
    end = int(cfg.quiet_end_hour) % 24
    hour = now.hour
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    # Wraps midnight (e.g. 23 → 7)
    return hour >= start or hour < end


def next_delay_seconds(
    cfg: CronConfig,
    *,
    rng: random.Random | None = None,
    now: datetime | None = None,
) -> float:
    """Draw a random delay. Longer short-wait while in quiet hours."""
    rng = rng or random.Random()
    lo = float(cfg.min_minutes) * 60.0
    hi = float(cfg.max_minutes) * 60.0
    if hi < lo:
        lo, hi = hi, lo
    delay = rng.uniform(lo, hi)
    # Apply ± jitter so even equal min/max is never exact.
    if cfg.jitter_frac > 0:
        factor = 1.0 + rng.uniform(-cfg.jitter_frac, cfg.jitter_frac)
        delay = max(30.0, delay * factor)
    if in_quiet_hours(cfg, now=now):
        # Sleep until roughly quiet_end, with randomness (15–45 min chunks).
        delay = max(delay, rng.uniform(15 * 60, 45 * 60))
    return delay


def invoke_checkup(
    cfg: CronConfig,
    *,
    session: requests.Session | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """POST /api/agent/reach — wakes browser WS → agent voice check-up."""
    base = (cfg.backend_url or DEFAULT_BACKEND).rstrip("/")
    url = f"{base}/api/agent/reach"
    payload = {
        "agent_id": cfg.agent_id or DEFAULT_AGENT_ID,
        "agent_name": cfg.agent_name or DEFAULT_AGENT_NAME,
        "message": cfg.message or "is checking up on you",
        "mode": "voice_call",
        "auto_answer": bool(cfg.auto_answer),
        "greeting_context": "reminder_call",
        "purpose": "checkup",
    }
    http = session or requests
    res = http.post(url, json=payload, timeout=timeout)
    res.raise_for_status()
    body = res.json()
    if not isinstance(body, dict):
        return {"ok": True, "raw": body}
    return body


class CheckupCronRunner:
    """Background thread: sleep random delay → invoke backend reach."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._cfg = load_cron_config()
        self.status = CronStatus()
        self._on_tick: Callable[[CronStatus], None] | None = None

    def configure(self, cfg: CronConfig) -> None:
        with self._lock:
            self._cfg = cfg
            save_cron_config(cfg)

    def get_config(self) -> CronConfig:
        with self._lock:
            return CronConfig(**asdict(self._cfg))

    def is_running(self) -> bool:
        with self._lock:
            return bool(self._thread and self._thread.is_alive())

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self.status.running = True
            self._thread = threading.Thread(
                target=self._loop,
                name="gfgpt-checkup-cron",
                daemon=True,
            )
            self._thread.start()
            logger.info("checkup cron started")

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            self.status.running = False
            self.status.next_fire_at = None
        t = self._thread
        if t and t.is_alive() and t is not threading.current_thread():
            t.join(timeout=2.0)
        logger.info("checkup cron stopped")

    def fire_now(self) -> dict[str, Any]:
        """Immediate check-up (also used by the UI button)."""
        cfg = self.get_config()
        if in_quiet_hours(cfg) and cfg.respect_quiet_hours:
            # Still allow manual fire — only auto loop skips.
            pass
        try:
            result = invoke_checkup(cfg)
            with self._lock:
                self.status.last_fire_at = time.time()
                self.status.last_result = result
                self.status.last_error = None
                self.status.fires += 1
                self._push_history(result, error=None)
            return result
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self.status.last_error = str(exc)
                self._push_history(None, error=str(exc))
            raise

    def _push_history(self, result: dict[str, Any] | None, error: str | None) -> None:
        entry = {
            "ts": time.time(),
            "ok": error is None,
            "delivered": (result or {}).get("delivered"),
            "error": error,
        }
        self.status.history = (self.status.history + [entry])[-40:]

    def _loop(self) -> None:
        while not self._stop.is_set():
            cfg = self.get_config()
            if not cfg.enabled:
                self._stop.wait(5.0)
                continue
            if in_quiet_hours(cfg):
                delay = next_delay_seconds(cfg)
            else:
                delay = next_delay_seconds(cfg)
            next_at = time.time() + delay
            with self._lock:
                self.status.next_fire_at = next_at
                self.status.running = True
            logger.info("checkup cron sleeping %.0fs (until %s)", delay, datetime.fromtimestamp(next_at))
            if self._stop.wait(delay):
                break
            cfg = self.get_config()
            if not cfg.enabled:
                continue
            if in_quiet_hours(cfg):
                logger.info("checkup cron quiet hours — skip fire")
                continue
            try:
                result = invoke_checkup(cfg)
                with self._lock:
                    self.status.last_fire_at = time.time()
                    self.status.last_result = result
                    self.status.last_error = None
                    self.status.fires += 1
                    self._push_history(result, error=None)
                logger.info("checkup cron fired delivered=%s", result.get("delivered"))
            except Exception as exc:  # noqa: BLE001
                with self._lock:
                    self.status.last_error = str(exc)
                    self._push_history(None, error=str(exc))
                logger.warning("checkup cron fire failed: %s", exc)
        with self._lock:
            self.status.running = False
            self.status.next_fire_at = None


# Process-wide singleton so Streamlit reruns keep the same thread.
_RUNNER: CheckupCronRunner | None = None
_RUNNER_LOCK = threading.Lock()


def get_cron_runner() -> CheckupCronRunner:
    global _RUNNER
    with _RUNNER_LOCK:
        if _RUNNER is None:
            _RUNNER = CheckupCronRunner()
        return _RUNNER


def format_eta(ts: float | None) -> str:
    if not ts:
        return "—"
    delta = max(0, int(ts - time.time()))
    mins, secs = divmod(delta, 60)
    hours, mins = divmod(mins, 60)
    when = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
    if hours:
        return f"in {hours}h {mins}m ({when})"
    if mins:
        return f"in {mins}m {secs}s ({when})"
    return f"in {secs}s ({when})"
