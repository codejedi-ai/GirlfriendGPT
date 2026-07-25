"""GirlfriendGPT Streamlit — companion server UI (chron + CLI gateway).

One page at :8501. Product Talk/Discover stays on Vite :5173.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.checkup_cron import (
    CronConfig,
    format_eta,
    get_cron_runner,
    load_cron_config,
    next_delay_seconds,
)
from utils.data import list_companions
from utils.subagent_server import (
    SubagentConfig,
    get_subagent_runner,
    load_subagent_config,
)

st.set_page_config(
    page_title="Companion server",
    page_icon="🤗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("Companion server")
st.caption("Chron check-ups + CLI sub-agent gateway · Talk UI → http://127.0.0.1:5173")

# ── CLI sub-agent gateway ─────────────────────────────────────────────
st.header("CLI sub-agent")
sub = get_subagent_runner()
scfg = sub.get_config() if sub.is_running() else load_subagent_config()

sub_host = st.text_input("Gateway host", value=scfg.host, key="sub_host")
sub_port = st.number_input(
    "Gateway port",
    min_value=1,
    max_value=65535,
    value=int(scfg.port),
    key="sub_port",
)
new_sub = SubagentConfig(
    host=sub_host.strip() or "127.0.0.1",
    port=int(sub_port),
    backend_url=scfg.backend_url,
)

b1, b2, b3 = st.columns(3)
with b1:
    if st.button("Save", use_container_width=True, key="sub_save"):
        sub.configure(new_sub)
        st.success("Saved")
with b2:
    if st.button("Start gateway", type="primary", use_container_width=True):
        sub.configure(new_sub)
        st_status = sub.start()
        if st_status.running:
            st.success(f"PID {st_status.pid}")
        else:
            st.error(st_status.last_error or "Failed")
with b3:
    if st.button("Stop gateway", use_container_width=True):
        sub.stop()
        st.info("Stopped")

st.write(
    f"**Gateway:** {'running' if sub.is_running() else 'stopped'}"
    + (f" · PID {sub.status.pid} · {sub.status.host}:{sub.status.port}" if sub.status.pid else "")
)
if st.button("Probe /health"):
    st.json(sub.probe_health())
if sub.status.last_error:
    st.warning(sub.status.last_error)

st.divider()

# ── Check-up chron ────────────────────────────────────────────────────
st.header("Check-up chron")
runner = get_cron_runner()
cfg = runner.get_config() if runner.is_running() else load_cron_config()
voice_companions = [c for c in list_companions() if c.voice and c.agent_id]
name_to_card = {c.name: c for c in voice_companions}
if cfg.agent_name in name_to_card:
    default_name = cfg.agent_name
elif voice_companions:
    default_name = voice_companions[0].name
else:
    default_name = cfg.agent_name

backend_url = st.text_input("Backend URL", value=cfg.backend_url, key="chron_backend")
companion_label = st.selectbox(
    "Companion",
    options=list(name_to_card.keys()) or [cfg.agent_name],
    index=(
        list(name_to_card.keys()).index(default_name) if default_name in name_to_card else 0
    ),
)
card = name_to_card.get(companion_label)
agent_id = (card.agent_id if card else cfg.agent_id) or cfg.agent_id
message = st.text_input("Reach message", value=cfg.message, key="chron_msg")
auto_answer = st.checkbox("Auto-answer (Vite talk + mic)", value=cfg.auto_answer)

min_m = st.number_input(
    "Min minutes",
    min_value=1.0,
    max_value=24 * 60.0,
    value=float(cfg.min_minutes),
    step=1.0,
)
max_m = st.number_input(
    "Max minutes",
    min_value=1.0,
    max_value=24 * 60.0,
    value=float(cfg.max_minutes),
    step=1.0,
)
jitter = st.slider(
    "Jitter (±)",
    min_value=0.0,
    max_value=0.5,
    value=float(cfg.jitter_frac),
    step=0.05,
)
respect_quiet = st.checkbox("Quiet hours", value=cfg.respect_quiet_hours)
q_start = st.number_input("Quiet start (hour)", 0, 23, int(cfg.quiet_start_hour))
q_end = st.number_input("Quiet end (hour)", 0, 23, int(cfg.quiet_end_hour))

sample = [
    next_delay_seconds(
        CronConfig(min_minutes=min_m, max_minutes=max_m, jitter_frac=jitter)
    )
    / 60
    for _ in range(5)
]
st.caption("Sample waits (min): " + ", ".join(f"{x:.1f}" for x in sample))

new_cfg = CronConfig(
    enabled=cfg.enabled,
    backend_url=backend_url.rstrip("/"),
    agent_id=str(agent_id),
    agent_name=companion_label,
    min_minutes=float(min_m),
    max_minutes=float(max_m),
    jitter_frac=float(jitter),
    quiet_start_hour=int(q_start),
    quiet_end_hour=int(q_end),
    respect_quiet_hours=bool(respect_quiet),
    auto_answer=bool(auto_answer),
    message=message.strip() or "is checking up on you",
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("Save chron", use_container_width=True, key="chron_save"):
        new_cfg.enabled = runner.get_config().enabled
        runner.configure(new_cfg)
        st.success("Saved")
with c2:
    if st.button("Start chron", type="primary", use_container_width=True):
        new_cfg.enabled = True
        runner.configure(new_cfg)
        runner.start()
        st.success("Running")
with c3:
    if st.button("Stop chron", use_container_width=True):
        stop_cfg = runner.get_config()
        stop_cfg.enabled = False
        runner.configure(stop_cfg)
        runner.stop()
        st.info("Stopped")
with c4:
    if st.button("Check up now", use_container_width=True):
        runner.configure(new_cfg)
        try:
            result = runner.fire_now()
            st.success(f"delivered={result.get('delivered')}")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

status = runner.status
st.write(
    f"**Chron:** {'running' if runner.is_running() and status.running else 'stopped'}"
    f" · fires {status.fires} · next {format_eta(status.next_fire_at)}"
)
if status.last_error:
    st.warning(status.last_error)
if status.history:
    st.dataframe(
        [
            {
                "when": datetime.fromtimestamp(h["ts"]).strftime("%H:%M:%S"),
                "ok": h.get("ok"),
                "delivered": h.get("delivered"),
            }
            for h in reversed(status.history[-12:])
        ],
        use_container_width=True,
        hide_index=True,
    )


@st.fragment(run_every=timedelta(seconds=5))
def _chron_tick() -> None:
    if runner.is_running() and runner.status.next_fire_at:
        st.caption(f"Next check-up {format_eta(runner.status.next_fire_at)}")


_chron_tick()
