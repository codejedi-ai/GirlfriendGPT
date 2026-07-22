"""Standalone launcher for the harness chat UI.

Serves the exact same router that is wired into the ConfigClaw gateway
(``configclaw.api.harness_gateway.router``) on its own port, so you can drive
the cold -> reflect -> warm loop from a browser without booting the full
gateway (or colliding with whatever else is on :8000).

Run:
    source .venv/bin/activate
    python3 scripts/harness_ui.py          # serves on http://127.0.0.1:8099
    HARNESS_UI_PORT=9100 python3 scripts/harness_ui.py

Then open:  http://127.0.0.1:8099/api/v1/harness/ui
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # the new-UI/ folder
# new-UI/ is the package root: `harness` (engine) and `harness_gateway` live here.
sys.path.insert(0, str(ROOT))

os.environ.setdefault("HARNESS_LLM_BASE_URL", "http://localhost:11434/v1")
os.environ.setdefault("HARNESS_LLM_MODEL", "qwen3.5:latest")
os.environ.setdefault("HARNESS_LLM_API_KEY", "local")

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from harness_gateway import router

# Serve the React SPA built to new-UI/frontend/dist (build it in the target
# project from frontend/HarnessPage.tsx). The harness API stays under
# /api/v1/harness/* (registered first, so it wins over the SPA catch-all).
DIST = ROOT / "frontend" / "dist"
INDEX = DIST / "index.html"

app = FastAPI(title="Harness UI")
app.include_router(router)


if DIST.is_dir() and INDEX.is_file():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/")
    async def _root() -> FileResponse:
        # The harness IS the default page — serve the React app at the root.
        return FileResponse(INDEX)

    @app.get("/{full_path:path}")
    async def _spa(full_path: str):
        # Unknown API paths are 404s, not the SPA shell.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        # Real static file (favicon, vite.ico, …) if present; else the SPA
        # entry so React Router handles client-side routing.
        candidate = DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(INDEX)
else:
    @app.get("/")
    async def _root_fallback() -> RedirectResponse:
        # SPA not built — fall back to the inline page.
        return RedirectResponse("/api/v1/harness/ui")


if __name__ == "__main__":
    port = int(os.environ.get("HARNESS_UI_PORT", "8099"))
    # Default localhost; in a container set HARNESS_UI_HOST=0.0.0.0 and publish
    # the port to 127.0.0.1 on the host so it stays localhost-only externally.
    host = os.environ.get("HARNESS_UI_HOST", "127.0.0.1")
    print(f"Harness UI →  http://127.0.0.1:{port}/api/v1/harness/ui")
    uvicorn.run(app, host=host, port=port, log_level="info")
