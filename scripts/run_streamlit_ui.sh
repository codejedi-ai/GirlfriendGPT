#!/usr/bin/env bash
# Chron + CLI sub-agent server only (app/streamlit). Product UI is Vite :5173.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STREAMLIT_DIR="${ROOT}/app/streamlit"
cd "$STREAMLIT_DIR"
echo "Chron + sub-agent server → http://127.0.0.1:8501" >&2
echo "Talk / Discover → http://127.0.0.1:5173" >&2
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
uv sync
exec uv run streamlit run Companion.py \
  --server.port 8501 \
  --server.address 127.0.0.1 \
  --server.headless true \
  --browser.gatherUsageStats false
