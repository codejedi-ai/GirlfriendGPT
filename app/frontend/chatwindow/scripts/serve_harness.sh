#!/usr/bin/env bash
# Host the self-improving harness AI on localhost, durably.
#
#   scripts/serve_harness.sh start    # start (detached; survives terminal close)
#   scripts/serve_harness.sh stop     # stop
#   scripts/serve_harness.sh restart
#   scripts/serve_harness.sh status
#
# Serves the chat UI + API on http://127.0.0.1:8099 (localhost only).
# Backing services (Redis/MinIO/Postgres) come from docker-compose.harness.yml;
# the local Ollama LLM must be running (ollama serve).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

PORT="${HARNESS_UI_PORT:-8099}"
HOST="127.0.0.1"
LOG="/tmp/harness_ui.log"
PIDFILE="/tmp/harness_ui.pid"
URL="http://${HOST}:${PORT}/api/v1/harness/ui"

is_running() {
  [[ -f "${PIDFILE}" ]] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null
}

start() {
  if is_running; then
    echo "already running (pid $(cat "${PIDFILE}"))  ->  ${URL}"
    return 0
  fi
  # Prefer the project venv's python.
  local PY="${ROOT}/.venv/bin/python3"
  [[ -x "${PY}" ]] || PY="python3"
  # nohup + detached stdio so it survives this shell closing (macOS has no setsid).
  HARNESS_UI_PORT="${PORT}" nohup "${PY}" scripts/harness_ui.py \
    > "${LOG}" 2>&1 < /dev/null &
  echo $! > "${PIDFILE}"
  disown 2>/dev/null || true
  sleep 4
  if is_running && curl -fsS -o /dev/null "http://${HOST}:${PORT}/api/v1/harness/state"; then
    echo "started (pid $(cat "${PIDFILE}"))  ->  ${URL}"
  else
    echo "failed to start; see ${LOG}"; tail -n 20 "${LOG}" || true; exit 1
  fi
}

stop() {
  if is_running; then
    kill "$(cat "${PIDFILE}")" 2>/dev/null || true
    sleep 1
    pkill -f "scripts/harness_ui.py" 2>/dev/null || true
    rm -f "${PIDFILE}"
    echo "stopped"
  else
    pkill -f "scripts/harness_ui.py" 2>/dev/null || true
    echo "not running"
  fi
}

status() {
  if is_running; then
    echo "running (pid $(cat "${PIDFILE}"))  ->  ${URL}"
    curl -fsS "http://${HOST}:${PORT}/api/v1/harness/state" || true
    echo
  else
    echo "not running"
  fi
}

case "${1:-start}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status) status ;;
  *) echo "usage: $0 {start|stop|restart|status}"; exit 1 ;;
esac
