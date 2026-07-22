#!/usr/bin/env bash
# Optional Streamlit companion UI (isolated under app/streamlit).
# Default product UI is Vite GirlfriendGPT: app/frontend (:5173).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STREAMLIT_DIR="${ROOT}/app/streamlit"
cd "$STREAMLIT_DIR"
echo "Streamlit UI → http://127.0.0.1:8501 (optional; default UI is app/frontend :5173)" >&2
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
uv sync
exec uv run streamlit run Companion.py \
  --server.port 8501 \
  --server.address 127.0.0.1 \
  --server.headless true \
  --browser.gatherUsageStats false
