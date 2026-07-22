#!/usr/bin/env bash
# Deprecated alias — Streamlit lives in app/streamlit now.
exec "$(cd "$(dirname "$0")" && pwd)/run_streamlit_ui.sh" "$@"
