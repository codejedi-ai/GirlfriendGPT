# GirlfriendGPT frontend (default UI)

Vite + React shell. Voice talk opens from Discover / profile **TALK** (full main pane).

## Routes

| Path | UI |
|------|-----|
| `/` | Landing |
| `/discover` | Profile grid + sidebar |
| `/profile/:id` | Profile detail → TALK |
| `/talk` | Optional full-page talk (embeds) |

Backend for talk tokens: **`app/backend`** (`POST /api/token`). Discover profiles fall back to `GET /api/companions` when Django is absent.

## Run

```bash
cd app/frontend && npm run dev
```

Open **http://127.0.0.1:5173/**.
