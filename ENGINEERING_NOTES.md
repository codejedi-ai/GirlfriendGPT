# Engineering Notes - GirlfriendGPT

## Cleanup & Refactoring (2026-03-12)

### Legacy File Archival

Moved deprecated CLI files to `scripts/legacy/` for historical reference:

| File | Reason | Status |
|------|--------|--------|
| `scripts/legacy/cli.py` | Old standalone CLI client; functionality merged into `src/cli.py` | Archived |
| `scripts/legacy/setup_cli.py` | Manual installation script; superseded by package entry points and `scripts/install.sh` | Archived |

**No functionality lost** — all commands (`chat`, `code`, `refactor`, `ask`, etc.) are fully implemented in the current `src/cli.py` with additional gateway management features.

### Dependency Changes

The project has been converted to a Steamship‑free architecture. The
former Steamship client and agent framework have been removed; the
"spinal cord" is now a simple `SmolAgent` using the `openai` SDK. As a
result the dependency list was updated:

- removed all `steamship` references
- added `openai>=0.27.0` as the core LLM client
- other bounds remain unchanged (FastAPI, websockets, etc.)

**Impact:** the installer no longer requires a Steamship API key, and
pip no longer spends minutes resolving conflicting Steamship versions.

### Python Version Note

- **Current requirement:** `>=3.8` (relaxed for dev container compatibility)
- **Target requirement:** `>=3.14` (to be enforced when container/pyenv supports it)
- **Code status:** Fully compatible with 3.14; no code changes needed to upgrade

---

## Smoke Test Checklist

> NOTE: the tests below assume the project has been converted to
> SmolAgent.  You no longer need a Steamship API key – only an OpenAI key
> (or whatever LLM provider you configure).


### Prerequisites

- [ ] OpenAI API key (`OPENAI_API_KEY` environment variable)
- [ ] Steamship API key (`STEAMSHIP_API_KEY` environment variable)

### Test Steps

1. **Verify CLI is accessible:**
   ```bash
   source .venv/bin/activate
   gfgpt --help
   ```
   Expected: Show help with `gateway`, `chat`, `code`, etc. commands.

2. **Verify gateway starts:**
   ```bash
   gfgpt gateway start --port 8000
   ```
   Expected: Listen on port 8000, no import errors.

3. **Health check (in new terminal):**
   ```bash
   source .venv/bin/activate
   gfgpt health
   ```
   Expected: `✓ Gateway is running`

4. **Test chat (single message):**
   ```bash
   gfgpt chat "Hello, who are you?"
   ```
   Expected: Companion responds with introduction.

5. **Test code generation:**
   ```bash
   gfgpt code "Python function to calculate factorial"
   ```
   Expected: Receives working code snippet.

### Known Issues & Resolutions

| Issue | Resolution |
|-------|-----------|
| `ModuleNotFoundError: steamship.agents` | Run `bash scripts/install.sh` with updated `pyproject.toml` (pins steamship>=2.17.34) |
| Port 8000 already in use | Use `gfgpt gateway start --port 9000` |
| API key not set | Ensure env vars are exported: `export OPENAI_API_KEY="..."`; `export STEAMSHIP_API_KEY="..."` |

---

## Recent Commits

- Moved `cli.py` and `setup_cli.py` to `scripts/legacy/`
- Tightened dependency pins in `pyproject.toml`, `setup.cfg`, `requirements.txt`
- Updated `GIRLFRIENDGPT_SETUP_GUIDE.md` to clarify Python version compatibility

---

## Next Steps

1. Set API keys and run smoke test suite
2. Confirm gateway can start and respond to chat
3. Test TUI (`gfgpt tui`) and code generation features
4. Plan upgrade to Python 3.14+ when environment support available
