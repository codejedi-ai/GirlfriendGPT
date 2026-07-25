#!/usr/bin/env bash
# Headless check-up chron (same logic as Streamlit page) — random intervals → backend reach.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/app/streamlit"
uv sync
exec uv run python -c "
from utils.checkup_cron import CronConfig, get_cron_runner, load_cron_config
import logging, time
logging.basicConfig(level=logging.INFO)
cfg = load_cron_config()
cfg.enabled = True
runner = get_cron_runner()
runner.configure(cfg)
runner.start()
print('checkup chron running — Ctrl+C to stop')
print(f'interval {cfg.min_minutes}-{cfg.max_minutes} min ±{cfg.jitter_frac} → {cfg.backend_url}')
try:
    while True:
        time.sleep(30)
except KeyboardInterrupt:
    runner.stop()
"
