# GirlfriendGPT backend (`app/backend`)

Token API for the Talk frontend. **Does not** join LiveKit rooms as the user.

```text
app/frontend  --POST /api/token-->  this package  → { token, url }
app/frontend  --Room.connect----->  LiveKit
app/agent                         → voice worker joins via dispatch
```

## Run

```bash
# Usually via: cd app && docker compose up -d

cd app/backend
uv sync
uv run python main.py   # :8080
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/token` | Mint JWT + LiveKit URL (RoomAgentDispatch for Ella) |
| `POST` | `/api/connect` | Alias of `/api/token` |
| `GET` | `/api/health` | Liveness |

## Tests

```bash
uv sync --extra dev
uv run pytest tests/test_livekit_token.py -q
```
