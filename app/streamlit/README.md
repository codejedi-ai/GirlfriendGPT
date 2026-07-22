# Optional Streamlit companion UI (`app/streamlit`)

Isolated from the default product stack (**GirlfriendGPT** Vite UI at `app/frontend`).

Left sidebar lists characters from:

- `src/templates/personalities/` (Luna, Sandra, … — text)
- `templates/` (Lena, Nia, medication_companion)
- `app/agent/personas/` (live voice personas)

**Voice** companions embed Vite Talk (`app/frontend` → `app/backend` → LiveKit → `app/agent`).

**Text** companions keep the classic spin-up + gateway chat flow.

```bash
# From repo root (or from this directory):
./scripts/run_streamlit_ui.sh
# → http://127.0.0.1:8501

# Or:
cd app/streamlit && uv sync && uv run streamlit run Companion.py \
  --server.port 8501 --server.address 127.0.0.1
```
