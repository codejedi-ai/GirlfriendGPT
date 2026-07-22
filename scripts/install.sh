#!/usr/bin/env bash
# installer for GirlfriendGPT
# usage: curl -fsSL https://openclaw.ai/install.sh | bash

set -euo pipefail

echo "🚀 Installing GirlfriendGPT via shell installer"

dir=$(pwd)

# create virtual environment
if command -v uv >/dev/null 2>&1; then
    echo "📦 Creating virtual environment using uv"
    uv venv .venv
else
    echo "📦 Creating virtual environment using python3 -m venv"
    python3 -m venv .venv
fi

# install dependencies
if command -v uv >/dev/null 2>&1; then
    echo "📚 Installing dependencies with uv"
    uv pip install -e .
else
    echo "📚 Installing dependencies with pip"
    # activate just for install
    # shellcheck disable=SC1091
    source .venv/bin/activate
    pip install -e .
fi

echo "\n✓ Installation complete!"

echo "\nNext steps:"
echo "  1. Activate virtual environment:"
echo "     source ".venv"/bin/activate"
echo "  2. Run onboarding:" 

echo "     gfgpt setup   # or 'gfgpt onboard'"
echo "  3. Start the gateway:" 

echo "     gfgpt gateway start"
echo "  4. In another terminal use the CLI/TUI:" 

echo "     gfgpt tui    # Terminal UI"
echo "     gfgpt chat   # CLI chat"
