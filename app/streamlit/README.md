# Chron + CLI sub-agent server (`app/streamlit`)

**http://127.0.0.1:8501** — single companion-server page (no tabs):

- CLI sub-agent WebSocket gateway (`app/companion`)
- Random check-up chron → `POST /api/agent/reach`

Product Talk/Discover stays at **http://127.0.0.1:5173**.

```bash
./scripts/run_streamlit_ui.sh
# → http://127.0.0.1:8501
```

Headless chron only: `./scripts/run_checkup_cron.sh`

Leave backend `CHECKUP_ENABLED=0` so Streamlit owns the schedule.
