"""Entry point for AI Influencer Agent."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from gateway.server import run_gateway

if __name__ == "__main__":
    run_gateway()
