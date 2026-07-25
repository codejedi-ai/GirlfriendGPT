"""CLI sub-agent gateway process control (app/companion WebSocket server).

Streamlit at :8501 starts/stops this — it is not the Vite Talk UI.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger("subagent-server")

CONFIG_FILE = Path.home() / ".gfgpt" / "subagent_server.json"
STATE_FILE = Path.home() / ".gfgpt" / "subagent_server_state.json"
_REPO_ROOT = Path(__file__).resolve().parents[3]  # utils → streamlit → app → GirlfriendGPT
_APP_DIR = _REPO_ROOT / "app"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18789


@dataclass
class SubagentConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    backend_url: str = "http://127.0.0.1:8080"


@dataclass
class SubagentStatus:
    running: bool = False
    pid: int | None = None
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    last_error: str | None = None
    health: dict[str, Any] | None = None


def load_subagent_config() -> SubagentConfig:
    if not CONFIG_FILE.exists():
        return SubagentConfig()
    try:
        raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return SubagentConfig()
    base = SubagentConfig()
    for key in asdict(base):
        if key in raw:
            setattr(base, key, raw[key])
    base.port = int(base.port)
    return base


def save_subagent_config(cfg: SubagentConfig) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")


def _load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


class SubagentServerRunner:
    """Background subprocess for ``companion.gateway.gateway``."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._proc: subprocess.Popen[Any] | None = None
        self._cfg = load_subagent_config()
        self.status = SubagentStatus()
        self._restore()

    def _restore(self) -> None:
        state = _load_state()
        pid = state.get("pid")
        if isinstance(pid, int) and _pid_alive(pid):
            self.status.running = True
            self.status.pid = pid
            self.status.host = str(state.get("host") or self._cfg.host)
            self.status.port = int(state.get("port") or self._cfg.port)

    def configure(self, cfg: SubagentConfig) -> None:
        with self._lock:
            self._cfg = cfg
            save_subagent_config(cfg)

    def get_config(self) -> SubagentConfig:
        with self._lock:
            return SubagentConfig(**asdict(self._cfg))

    def is_running(self) -> bool:
        with self._lock:
            if self._proc is not None:
                if self._proc.poll() is None:
                    return True
                self._proc = None
            if self.status.pid and _pid_alive(self.status.pid):
                return True
            self.status.running = False
            self.status.pid = None
            return False

    def start(self) -> SubagentStatus:
        with self._lock:
            if self.is_running():
                return self.status
            cfg = self.get_config()
            log_file = Path.home() / ".gfgpt" / "logs" / "subagent_gateway.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            env = {
                **os.environ,
                "PYTHONPATH": str(_APP_DIR) + os.pathsep + os.environ.get("PYTHONPATH", ""),
            }
            cmd = [
                sys.executable,
                "-m",
                "companion.gateway.gateway",
                "--host",
                cfg.host,
                "--port",
                str(cfg.port),
            ]
            try:
                with open(log_file, "a", encoding="utf-8") as log:
                    self._proc = subprocess.Popen(
                        cmd,
                        stdout=log,
                        stderr=log,
                        start_new_session=True,
                        env=env,
                        cwd=str(_REPO_ROOT),
                    )
                time.sleep(0.8)
                if self._proc.poll() is not None:
                    self.status.running = False
                    self.status.pid = None
                    self.status.last_error = f"exited immediately — see {log_file}"
                    return self.status
                self.status.running = True
                self.status.pid = self._proc.pid
                self.status.host = cfg.host
                self.status.port = cfg.port
                self.status.last_error = None
                _save_state(
                    {"pid": self._proc.pid, "host": cfg.host, "port": cfg.port}
                )
                logger.info("subagent gateway started pid=%s", self._proc.pid)
            except Exception as exc:  # noqa: BLE001
                self.status.last_error = str(exc)
                self.status.running = False
                logger.warning("subagent start failed: %s", exc)
            return self.status

    def stop(self) -> SubagentStatus:
        with self._lock:
            pid = self.status.pid or (self._proc.pid if self._proc else None)
            if pid and _pid_alive(pid):
                try:
                    os.killpg(pid, signal.SIGTERM)
                except (ProcessLookupError, PermissionError, OSError):
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except (ProcessLookupError, PermissionError, OSError):
                        pass
            if self._proc is not None:
                try:
                    self._proc.terminate()
                    self._proc.wait(timeout=3)
                except Exception:  # noqa: BLE001
                    pass
                self._proc = None
            self.status.running = False
            self.status.pid = None
            self.status.health = None
            _save_state({})
            return self.status

    def probe_health(self) -> dict[str, Any]:
        cfg = self.get_config()
        url = f"http://{cfg.host}:{cfg.port}/health"
        try:
            res = requests.get(url, timeout=2.0)
            body: dict[str, Any]
            try:
                parsed = res.json()
                body = parsed if isinstance(parsed, dict) else {"raw": parsed}
            except Exception:  # noqa: BLE001
                body = {"text": res.text[:200]}
            body["http_status"] = res.status_code
            self.status.health = body
            return body
        except Exception as exc:  # noqa: BLE001
            err = {"ok": False, "error": str(exc)}
            self.status.health = err
            return err


_RUNNER: SubagentServerRunner | None = None
_LOCK = threading.Lock()


def get_subagent_runner() -> SubagentServerRunner:
    global _RUNNER
    with _LOCK:
        if _RUNNER is None:
            _RUNNER = SubagentServerRunner()
        return _RUNNER
