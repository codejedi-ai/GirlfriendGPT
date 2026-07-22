# GirlfriendGPT voice agent (`app/agent`)

LiveKit **voice worker** — joins rooms as `AI-LiveKit-Agent`, loads personas from
`personas/`, talks via host Ollama + Speaches.

Stack layout (locked):

| Package | Path |
|---------|------|
| Frontend | [`../frontend`](../frontend) |
| Backend (tokens) | [`../backend`](../backend) |
| **Agent (this)** | `app/agent` |

```text
frontend → backend /api/token → frontend → LiveKit
                                    ↑
                         voice_agent.py (here)
```

## Run the worker

```bash
# Infra (from app/): LiveKit + backend + frontend
cd .. && docker compose up -d

cd agent
uv sync
LIVEKIT_URL=ws://127.0.0.1:7880 \
LIVEKIT_API_KEY=devkey \
LIVEKIT_API_SECRET=secret \
uv run python voice_agent.py dev
```

Open **http://127.0.0.1:5173** (frontend). See [`../README.md`](../README.md).

## Package contents

| Path | Role |
|------|------|
| `voice_agent.py` | LiveKit Agents worker entry |
| `personas/*.json` | Ella, Nia |
| `tools/*.json` | Tool defs by id |
| `livekit.yaml` | Local SFU config (used by app compose) |
| `talk/` | Shim → `app/backend` (prefer backend directly) |

## Tests

```bash
uv sync --extra dev
uv run pytest -q
```
