"""Entry point for the CLI companion gateway.

Run from repo root::

    PYTHONPATH=app uv run python -m companion
"""

from __future__ import annotations

import sys
from pathlib import Path

# ``app/`` must be on path so ``companion`` resolves as a top-level package.
_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from companion.gateway.gateway import run_gateway  # noqa: E402

if __name__ == "__main__":
    run_gateway()
