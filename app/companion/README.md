# CLI companion (`app/companion`)

Text / WebSocket **CLI sub-agent** for GirlfriendGPT (not the LiveKit voice worker).

| Piece | Role |
|-------|------|
| `gateway/` | FastAPI WebSocket gateway (`gfgpt gateway start`) |
| `agent/` | SmolAgent + media tools (legacy path; prefer `core/`) |
| `core/` | Run loop, context, memory |
| `tools/` | Tool registry + shared JSON catalog loader |
| `templates/` | Personality JSON + config template |
| `services/` | Cron / heartbeat helpers |

Entry points:

- Root `cli.py` → `gfgpt` (`from companion…`)
- `PYTHONPATH=app python -m companion` → gateway

Voice stack stays in `app/agent/`. Streamlit chron is `app/streamlit/`.
