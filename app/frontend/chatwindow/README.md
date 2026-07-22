# GirlfriendGPT frontend (`app/frontend`) — **Vite + React**

Vite is the frontend toolchain (`npm run dev` / `vite build` / `vite preview`).

Stack: **this Vite app** → **[`app/backend`](../backend)** `/api/token` → **LiveKit**; voice = **[`app/agent`](../agent)**.

## Traffic

```text
Vite (:5173)
  --POST /api/token-->  app/backend (:8080)  → { token, url }
  --Room.connect----->  LiveKit (:7880)      → WebRTC
```

Vite proxies `/api/*` to the backend (`VITE_BACKEND_PROXY`).

## Run (Vite)

```bash
cd app/frontend
npm install
npm run dev          # http://127.0.0.1:5173
```

Full stack (Vite preview in Docker):

```bash
cd app && docker compose up -d
```

Also start the agent: `cd app/agent && uv run python voice_agent.py dev` (plus Ollama/Speaches).

| Script | What |
|--------|------|
| `npm run dev` | Vite HMR |
| `npm run build` | `vite build` → `dist/` |
| `npm run preview` | `vite preview` (same /api proxy) |

| Var | Meaning |
|-----|---------|
| `VITE_API_BASE` | Absolute backend URL if not using the proxy |
| `VITE_BACKEND_PROXY` | Proxy target for `/api` (default `http://127.0.0.1:8080`) |

Harness UI: `http://127.0.0.1:5173/?page=harness`

## Layout

```text
vite.config.ts        Vite + /api → backend proxy
index.html            Vite entry
src/main.tsx          React mount
src/TalkPage.tsx      voice talk (default)
src/HarnessPage.tsx   scraper harness
```
