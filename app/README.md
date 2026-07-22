# GirlfriendGPT local stack

Self-contained AI girlfriend (no ALI). Three packages:

| Package | Path | Role |
|---------|------|------|
| **Frontend** | [`app/frontend`](frontend/) | **Vite** Talk UI (`npm run dev`, `:5173`) |
| **Backend** | [`app/backend`](backend/) | Token API only — `POST /api/token` (`:8080`) |
| **Agent** | [`app/agent`](agent/) | LiveKit voice worker + personas (joins rooms) |

## Traffic (locked)

```text
app/frontend
  --POST /api/token-->  app/backend     → { token, url }
  --Room.connect----->  LiveKit :7880   → WebRTC
                              ↑
                    app/agent voice_agent.py
                              ↓
                 Ollama :11434 + Speaches :8000 (host)
```

Backend never joins LiveKit as the user. The agent worker registers as `AI-LiveKit-Agent`.

## Run

```bash
# Infra + backend + frontend
cd app
docker compose up -d

# Voice worker (this is app/agent)
cd agent
uv sync
LIVEKIT_URL=ws://127.0.0.1:7880 \
LIVEKIT_API_KEY=devkey \
LIVEKIT_API_SECRET=secret \
uv run python voice_agent.py dev
```

Open **http://127.0.0.1:5173**

Frontend Vite hot-reload:

```bash
cd app/frontend && npm install && npm run dev
```

## Prerequisites

- Docker
- uv
- Ollama on `:11434` (model from `agent/personas/Ella.json`)
- Speaches on `:8000`
