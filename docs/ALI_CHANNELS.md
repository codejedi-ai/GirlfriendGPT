# GirlfriendGPT — ALI channels

## Voice agent (LiveKit worker)

- **Path:** `GirlfriendGPT/app/agent/` (`voice_agent.py`, `data/agents/*.json`)
- **Started by:** ALI `agent_lifecycle` / `dev.sh` using `config.json` → `agent_package_path`
- **ALI has no `app/agent`** — orchestration only

## CLI sub-agent

- **Path:** `GirlfriendGPT/cli.py` + `GirlfriendGPT/src/`
- **Role:** second agent kind ALI can orchestrate (text/websocket companion stack)
- **Tools:** same shared catalog as voice — `shared/tools/<id>.json`; personas/CLI list ids only
- **Loader:** `src/tools/json_catalog.py`

## Shared tools

```
Hack49-.../shared/tools/
  report_adherence_intent.json
  empathy.json
```

Agent JSON example:

```json
"tools": ["report_adherence_intent"]
```
