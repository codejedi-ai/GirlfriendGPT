# Cursor Engineering Log — 2026-07-21

## Session: 19:15 - Local AI Girlfriend Talk Stack (standalone)

### Thought Process & Regression Analysis

- **Problem:** GirlfriendGPT needed a self-contained local path to talk to the AI girlfriend in a browser. ALI orchestration is gone; persona catalog symlinks to `ali-agents/GirlfriendGPT-agents` were broken; there was no Docker LiveKit or browser Talk UI in-package.
- **Regression Opportunities:** `agent_paths` / `load_persona` / worker name → Ella fallback; talk `/api/connect` JWT + RoomAgentDispatch metadata (`agent_id`, `greeting_context`).
- **Execution Strategy:** Tests executed via dedicated CI/CD Workflow `GirlfriendGPT Voice Agent Tests` (`.github/workflows/girlfriendgpt-voice-agent.yml`).

### UML Diagram

```mermaid
sequenceDiagram
  participant Browser
  participant TalkGateway
  participant LiveKit
  participant VoiceWorker
  participant Ollama
  participant Speaches

  Browser->>TalkGateway: POST /api/connect
  TalkGateway-->>Browser: JWT + ws URL (RoomAgentDispatch)
  Browser->>LiveKit: Room.connect(token)
  LiveKit->>VoiceWorker: dispatch AI-LiveKit-Agent
  VoiceWorker->>VoiceWorker: load_persona(Ella)
  Browser->>LiveKit: mic audio
  LiveKit->>VoiceWorker: audio
  VoiceWorker->>Speaches: STT
  VoiceWorker->>Ollama: LLM
  VoiceWorker->>Speaches: TTS
  VoiceWorker->>LiveKit: agent audio
  LiveKit->>Browser: hear Ella
```

### Changes

- In-package `app/agent/personas/` (Ella, Nia) + `app/agent/tools/`
- `agent_paths.py` prefers package root; no ALI required
- `docker-compose.yml` + `livekit.yaml` (LiveKit + Redis + talk-gateway)
- `talk/` FastAPI gateway + browser Talk page
- Pytest + workflow for automated regression on the local branch / remote pipeline

Tests and workflow configured for automated execution on the local branch/remote pipeline.
**Workflow Name:** `GirlfriendGPT Voice Agent Tests` / job `pytest`

## Session: 19:20 - Frontend→Backend token, Frontend→LiveKit

### Thought Process & Regression Analysis

- **Problem:** Clarify traffic: backend must only mint tokens; the frontend is the LiveKit client.
- **Regression Opportunities:** `/api/token` response shape `{token, url}`; `/api/connect` alias; TalkPage + static UI follow two-step connect.
- **Execution Strategy:** Tests executed via dedicated CI/CD Workflow.

### UML Diagram

```mermaid
sequenceDiagram
  participant FE as Frontend
  participant BE as AppBackend
  participant LK as LiveKit
  participant Worker as VoiceWorker

  FE->>BE: POST /api/token
  BE-->>FE: token + url
  FE->>LK: Room.connect(url, token)
  LK->>Worker: agent dispatch
  Note over FE,LK: Backend never joins as user
```

## Session: 19:25 - Token API owned by app/backend

### Thought Process & Regression Analysis

- **Problem:** User specified backend location is `app/backend`, not `app/agent/talk`.
- **Regression Opportunities:** `app/backend/tests/test_livekit_token.py`; compose `backend` service builds from `../backend`.
- **Execution Strategy:** Tests via workflow jobs `backend-token` + `agent`.

Canonical: Frontend → `app/backend` `/api/token` → Frontend → LiveKit.

## Session: 19:30 - Frontend owned by app/frontend

### Thought Process & Regression Analysis

- **Problem:** User specified frontend path is `app/frontend`.
- **Regression Opportunities:** Vite app default route = TalkPage; `/api` proxy to backend; compose `frontend` service (nginx → backend).
- **Execution Strategy:** `npm run build` in app/frontend; stack via agent docker compose.

```mermaid
flowchart LR
  FE["app/frontend :5173"] -->|"POST /api/token"| BE["app/backend :8080"]
  FE -->|"Room.connect"| LK["LiveKit :7880"]
  Worker["app/agent voice"] --> LK
```

## Session: 19:35 - Agent owned by app/agent

### Thought Process & Regression Analysis

- **Problem:** Lock the third package path: voice worker = `app/agent`.
- **Regression Opportunities:** `app/README.md` three-package table; `app/docker-compose.yml` is canonical stack; agent compose includes it.
- **Execution Strategy:** Document + compose include; worker still `uv run python voice_agent.py dev` from `app/agent`.

## Session: 20:00 - Live left/right transcripts

### Thought Process & Regression Analysis

- **Problem:** User wants realtime STT for both speakers — Ella left, user right.
- **Regression Opportunities:** `upsertTranscriptLine` / `resolveWhoFromMeta` in `app/frontend/src/transcript.ts`; agent `RoomOutputOptions(transcription_enabled=True)`.
- **Execution Strategy:** `npm test` in app/frontend; agent republishes `lk.transcription` streams.

## Session: 20:10 - Fix deaf agent (no hearing)

### Thought Process & Regression Analysis

- **Problem:** Lena greets (TTS works) but does not hear the user — no STT metrics. LiveKit showed user ICE reconnect loops (~15s) and sessions where the user mic never published; agent used `close_on_disconnect=True` and linked audio after `session.start`.
- **Regression Opportunities:** `voice_agent._first_human_participant` / wait-before-start; `RoomInputOptions(close_on_disconnect=False, participant_identity=…)`; frontend waits for agent join; backend explicit `CreateAgentDispatch`.
- **Execution Strategy:** Tests via `uv run pytest tests/test_patient_link.py` in `app/agent`.

```mermaid
sequenceDiagram
  participant FE as Frontend
  participant BE as Backend
  participant LK as LiveKit
  participant AG as Voice worker
  FE->>BE: POST /api/token
  FE->>LK: connect + publish mic
  LK->>AG: job
  AG->>AG: wait human then session.start(bound)
  Note over AG: close_on_disconnect=False
```

## Session: 20:15 - Lena English + single greeting

### Thought Process & Regression Analysis

- **Problem:** Transcript showed Dutch-planned CoT (`# Response Selection`) twice instead of one English spoken greeting — Qwythos `generate_reply` leaked planning text; persona defaulted to Dutch.
- **Regression Opportunities:** `personas/Lena Van Der Meer.json` English TTS/greetings; `voice_agent` greets via `session.say(template)`; `tests/test_worker_name_persona.py`.
- **Execution Strategy:** `uv run pytest tests/test_worker_name_persona.py tests/test_patient_link.py` in `app/agent`.

## Session: 20:17 - Dedupe transcript bubbles

### Thought Process & Regression Analysis

- **Problem:** Identical YOU bubbles — TalkPage listened to both `lk.transcription` and `TranscriptionReceived`.
- **Regression Opportunities:** `upsertTranscriptLine` content dedupe; single text-stream listener in `TalkPage.tsx`; `transcript.test.ts`.
- **Execution Strategy:** `npm test` in `app/frontend`.

## Session: 20:40 - Fix intermittent silent agent audio

### Thought Process & Regression Analysis

- **Problem:** Agent TTS runs (metrics show audio) but browser sometimes plays no sound — autoplay gesture expires before remote track arrives.
- **Regression Opportunities:** `room.startAudio()` after connect + after agent join; `attachAllRemoteAudio`; Enable sound button; `AudioPlaybackStatusChanged`.
- **Execution Strategy:** Manual talk check on http://127.0.0.1:5173.

## Session: 20:46 - Agent chatwindow UI in Discover app

### Thought Process & Regression Analysis

- **Problem:** New app/frontend VoiceChatModal was a JWT debug panel; chatwindow had the real Lena talk UX.
- **Regression Opportunities:** `/talk-api` proxy; `useAgentTalkSession`; `VoiceChatModal` bubbles; `VoiceTalkContext` + AI profile TALK; `src/lib/transcript.test.ts`.
- **Execution Strategy:** `npm test` in `app/frontend`.

## Session: 21:00 - Default UI is Vite, not Streamlit

### Thought Process & Regression Analysis

- **Problem:** Mistakenly treated Streamlit (`src/ui`, :8501) as the "legacy/default" UI; user clarified default is Vite `app/frontend` (:5173).
- **Regression Opportunities:** Talk left bar via `GET /api/companions` (templates + personas); `TalkPage.tsx` character select; `tests/test_companions.py`; Streamlit demoted to optional script.
- **Execution Strategy:** Tests executed via dedicated CI/CD Workflow — `uv run pytest tests/test_companions.py` in `app/backend`.

```mermaid
flowchart LR
  Talk["app/frontend TalkPage"] -->|"GET /api/companions"| BE["app/backend"]
  Talk -->|"POST /api/token"| BE
  BE --> Templates["templates/ + personas/"]
  Talk -->|"LiveKit"| Agent["app/agent"]
```

## Session: 21:05 - Restore UW-Crushes as default UI

### Thought Process & Regression Analysis

- **Problem:** `/` had been redirected to Talk; user wants the old UW-Crushes Landing + Discover shell back.
- **Regression Opportunities:** `App.tsx` routes; `api.getProfiles` companion fallback; VoiceTalk `agentId`; VoiceChatModal remains talk surface inside Discover.
- **Execution Strategy:** Manual check http://127.0.0.1:5173/ → Landing → Discover.

```mermaid
flowchart LR
  Landing["/ UW-Crushes"] --> Discover["/discover"]
  Discover --> Modal["VoiceChatModal"]
  Modal -->|"POST /api/token"| BE["app/backend"]
```

## Session: 21:10 - Isolate Streamlit under app/streamlit

### Thought Process & Regression Analysis

- **Problem:** Streamlit lived in `src/ui` and was a root dependency though the product UI is Vite.
- **Regression Opportunities:** Move to `app/streamlit/` with own `pyproject.toml`; drop streamlit from root; `scripts/run_streamlit_ui.sh`.
- **Execution Strategy:** `cd app/streamlit && uv sync`; companions path resolves to repo root.

```mermaid
flowchart TB
  Root["GirlfriendGPT root pyproject"] -.->|"no streamlit"| ST["app/streamlit pyproject"]
  ST --> UI["Companion.py :8501"]
  FE["app/frontend UW-Crushes"] --> BE["app/backend"]
```

## Session: 21:15 - Talk fills main pane (not modal)

### Thought Process & Regression Analysis

- **Problem:** Voice talk was a centered modal overlay; user wants it full-screen in the non-sidebar main area.
- **Regression Opportunities:** `AuthenticatedLayout` swaps `Outlet` ↔ talk pane; `VoiceChatModal` is full-height main content.
- **Execution Strategy:** Manual: Discover → TALK → pane fills beside sidebar; X returns to Discover.

## Session: 21:28 - Fix mid-sentence TTS cutoffs

### Thought Process & Regression Analysis

- **Problem:** Agent audio stopped mid-sentence. Logs showed repeated `resumed false interrupted speech` — speaker→mic echo barged in; Speaches TTS often cannot pause/resume, so speech stayed cut.
- **Regression Opportunities:** `turn_handling_for_local_stack()` in `voice_agent.py`; `tests/test_turn_handling.py`; greeting `allow_interruptions=False`.
- **Execution Strategy:** Tests executed via dedicated CI/CD Workflow / local `uv run pytest tests/test_turn_handling.py`.

```mermaid
sequenceDiagram
  participant TTS as Agent TTS
  participant Mic as User mic
  participant VAD as Interruption VAD
  TTS->>Mic: loudspeaker audio
  Mic->>VAD: echo blip
  Note over VAD: old: min_duration 0.5s / 0 words → interrupt
  Note over VAD: new: 1.5s + 2 words required
```

## Session: 22:06 - Local mode: no auth + agent reach WebSocket

### Thought Process & Regression Analysis

- **Problem:** UI still had Django sign-in/up; agents had no way to page the local user.
- **Regression Opportunities:** `AuthContext` local guest; `/login`→discover; `local_events.py` WS + `POST /api/agent/reach`; incoming banner in `AuthenticatedLayout`.
- **Execution Strategy:** `uv run pytest tests/test_local_events.py`.

```mermaid
sequenceDiagram
  participant Agent
  participant BE as app/backend
  participant FE as Browser
  Agent->>BE: POST /api/agent/reach
  BE->>FE: WS /api/ws/events agent_reach
  FE->>FE: Incoming banner Answer
```


## Session: 22:13 - Front↔back WebSocket voice_call

### Thought Process & Regression Analysis

- **Problem:** Agent needs to initiate voice with the user while they are on the local UI; media stays on LiveKit, but invites need a reliable FE↔BE WebSocket.
- **Regression Opportunities:** `local_events.py` voice_call/notify; `useBackendEventsSocket`; `AgentVoiceBridge` + `VoiceChatModal` autoStart; `ring_browser_for_voice` in `voice_agent.py`; `tests/test_local_events.py`, `tests/test_ring_browser.py`.
- **Execution Strategy:** Tests executed via dedicated CI/CD Workflow / local `uv run pytest`.

```mermaid
sequenceDiagram
  participant Agent as Voice worker
  participant BE as app/backend
  participant FE as Browser WS
  participant LK as LiveKit
  Agent->>BE: POST /api/agent/reach mode=voice_call
  BE->>FE: WS /api/ws/events voice_call
  FE->>FE: openTalk autoStart + /discover
  FE->>BE: POST /api/token
  FE->>LK: connect + mic
```

## Session: 22:17 - Companion check-up rings

### Thought Process & Regression Analysis

- **Problem:** WebSocket reach path needed for companions to *check up* on the user when they are idle on the local UI.
- **Regression Opportunities:** `checkup.py` loop; `talk_state` on WS; `greeting_context=reminder_call`; FE autoStart; `tests/test_checkup.py`.
- **Execution Strategy:** Tests executed via dedicated CI/CD Workflow / local `uv run pytest`.

```mermaid
sequenceDiagram
  participant BE as checkup loop
  participant FE as Browser
  participant LK as LiveKit
  BE->>FE: WS voice_call checking up
  FE->>FE: openTalk reminder_call
  FE->>LK: connect + mic
  Note over FE,BE: talk_state live skips next rings
```

## Session: 22:19 - Streamlit chron server (random check-ups)

### Thought Process & Regression Analysis

- **Problem:** Check-ups should be driven by Streamlit as a chron server, not an exact backend timer; timing must be inexact.
- **Regression Opportunities:** `utils/checkup_cron.py` random delay + jitter; `pages/1_Checkup_Cron.py`; backend `CHECKUP_ENABLED` default off; `tests/test_checkup_cron.py`.
- **Execution Strategy:** Tests executed via dedicated CI/CD Workflow / local `uv run python -m unittest`.

```mermaid
sequenceDiagram
  participant ST as Streamlit chron
  participant BE as app/backend
  participant FE as Vite WS
  participant AG as Voice agent
  ST->>ST: sleep random min-max ±jitter
  ST->>BE: POST /api/agent/reach checkup
  BE->>FE: WS voice_call
  FE->>AG: LiveKit session + reminder_call greeting
```
