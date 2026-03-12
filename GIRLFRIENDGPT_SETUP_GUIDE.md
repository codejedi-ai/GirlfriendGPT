# GirlfriendGPT - Installation & Setup Guide

**GirlfriendGPT** is an AI companion agent that combines the intimacy of conversation with the power of code generation. It features a websocket-based gateway with multiple client interfaces: TUI (terminal UI), CLI (command-line), and direct API access.

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│  Configuration Layer (~/.gfgpt/)            │
│  - config.json  (Companion settings)        │
│  - state.json   (Gateway state)             │
│  - logs/        (Activity logs)             │
└─────────────────────────────────────────────┘
                    ▲
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
    ┌─────────┐┌──────────┐┌─────────┐
    │ TUI     ││   CLI    ││  Direct │
    │Client   ││  Client  ││  API    │
    └────┬────┘└────┬─────┘└────┬────┘
         │          │           │
         └──────────┼───────────┘
                    │ (WebSocket)
                    ▼
         ┌──────────────────────┐
         │  Websocket Gateway   │
         │  (FastAPI + uvicorn) │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  FunctionsBasedAgent │
         │  (LLM)               │
         └──────────┬───────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
    ┌─────────┐         ┌──────────┐
    │  Tools  │         │   LLM    │
    │ (Search,├────────┤ (GPT-4 /  │
    │ CodeGen,│         │ 3.5)     │
    │ Selfies)│         └──────────┘
    └─────────┘
```

## Installation

### Prerequisites

- Python 3.14+ (>=3.8 also works for local development/testing; requirement will be tightened before release)
- OpenAI API key (`OPENAI_API_KEY` environment variable)
# (Steamship is no longer required)
- Optional: UV package manager (automatic installation)

### Step 1: Clone the Repository

```bash
git clone https://github.com/EniasCailliau/GirlfriendGPT.git
cd GirlfriendGPT
```

### Step 2: Run Installation Script

You can install the project using the bundled shell installer or the
legacy Python script. On Linux/macOS the easiest way is to curl & pipe it
straight to bash:

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

The script lives in `scripts/install.sh` and performs the following steps:

1. Detects whether `uv` is available (falls back to `pip`)
2. Creates a `.venv` virtual environment
3. Installs all dependencies in editable mode (`pip install -e .`)
4. Registers the `gfgpt` CLI entry point

You may also run the installer manually if you prefer:

```bash
bash scripts/install.sh    # same behaviour as the curl command
```

If you would rather do everything by hand, follow the manual steps below.

#### Option B: Manual Installation

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .
```

### Step 3: Environment Configuration

Add your API keys to your shell profile or `.env` file:

```bash
export OPENAI_API_KEY="sk-..."
export ELEVENLABS_API_KEY="..."  # Optional for voice
export ELEVENLABS_VOICE_ID="..."  # Optional
```

## Getting Started

### 1. Run Initial Setup (a.k.a. onboarding)

```bash
gfgpt setup   # or `gfgpt onboard` (alias)
```

This interactive setup will ask you to configure:
- **Companion Name**: What to call your AI (default: Luna)
- **Model Provider**: Which LLM to use (default: OpenAI)
- **Model**: Which model variant (gpt-4 or gpt-3.5-turbo)
- **Identity**: Your companion's personality description
- **Behavior**: How your companion should act

Configuration is saved to `~/.gfgpt/config.json`

### 2. Start the Websocket Gateway

Open a terminal and run:

```bash
gfgpt gateway start
```

You should see:
```
🚀 Starting GirlfriendGPT Gateway
   Companion: Luna
   Server: 127.0.0.1:8000
   Model: gpt-4

INFO:     Uvicorn running on http://127.0.0.1:8000
```

The gateway is now ready to accept connections.

### 3. Choose Your Interface

#### Option A: Terminal UI (Recommended for Interactive Use)

Open another terminal and run:

```bash
gfgpt tui
```

This launches a rich terminal interface where you can:
- Chat naturally with your companion
- See real-time responses
- Easily switch between conversations

#### Option B: CLI Mode (Good for Testing & Scripts)

```bash
# Interactive mode
gfgpt chat

# Or execute a single message
gfgpt chat "Hello, how are you?"

# Generate code
gfgpt code "Python function to calculate fibonacci"

# Refactor existing code  
gfgpt refactor myfile.py "add type hints and error handling"
```

#### Option C: Direct API (For Custom Integrations)

```python
import asyncio
import json
import websockets
from src.config import ConfigManager

config = ConfigManager.load_config()
session_id = "unique-session-id"

async def chat():
    uri = f"ws://127.0.0.1:8000/ws/{session_id}"
    
    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({
            "role": "user",
            "content": "Hello!",
            "type": "text"
        }))
        
        # Receive response
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(chat())
```

## Configuration

### Configuration Directory Structure

```
~/.gfgpt/
├── config.json          # Main configuration
├── state.json          # Gateway state (auto-generated)
└── logs/
    ├── gateway.log     # Gateway logs
    └── cli.log         # CLI logs
```

### Configuration File (`~/.gfgpt/config.json`)

```json
{
  "name": "Luna",
  "byline": "Your AI Companion",
  "identity": "A helpful and supportive AI...",
  "behavior": "Be warm and engaging...",
  "model_provider": "openai",
  "model": "gpt-4",
  "use_gpt4": true,
  "gateway_host": "127.0.0.1",
  "gateway_port": 8000,
  "elevenlabs_api_key": "",
  "elevenlabs_voice_id": ""
}
```

### Changing Configuration

```bash
# Edit configuration manually
nano ~/.gfgpt/config.json

# Or rerun setup
gfgpt setup

# View current config
gfgpt config
```

## Commands Reference

### Gateway Management

```bash
# Start the gateway
gfgpt gateway start

# Start on custom port
gfgpt gateway start --port 9000 --host 0.0.0.0

# Stop the gateway
gfgpt gateway stop

# Restart the gateway
gfgpt gateway restart

# Check gateway health
gfgpt health
```

### Client Interfaces

```bash
# Terminal UI
gfgpt tui

# CLI - Interactive chat
gfgpt chat

# CLI - Single message
gfgpt chat "Your message here"

# Generate code
gfgpt code "Python decorator for timing functions"

# Refactor code
gfgpt refactor script.py "optimize and add docstrings"

# Check server status
gfgpt health --host 127.0.0.1 --port 8000
```

### System

```bash
# Run initial setup
gfgpt setup

# View configuration
gfgpt config

# Show version
gfgpt --version

# Get help
gfgpt --help
gfgpt chat --help
```

## Usage Examples

### Example 1: Interactive Conversation

```bash
gfgpt tui

# In the TUI:
You: Hi Luna! How's your day?
Luna: Hello! I'm doing great, thanks for asking!
      How can I help you today?

You: Tell me about Python async programming
Luna: Python's asyncio module provides tools for writing
      concurrent code that's single-threaded but provides...
```

### Example 2: Generating Code

```bash
gfgpt code "FastAPI server with database models and CRUD operations"
```

Output:
```
Here's a complete FastAPI server with SQLAlchemy models:

```python
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
# ... rest of code
```
```

### Example 3: Code Refactoring

```bash
gfgpt refactor my_script.py "improve performance and add type hints"
```

### Example 4: Coding Session

```bash
# Terminal 1 - Start gateway
gfgpt gateway start

# Terminal 2 - Use TUI
gfgpt tui

# Have a full conversation while developing
```

## Advanced Features

### Custom Personality Configuration

Edit `~/.gfgpt/config.json`:

```json
{
  "name": "DevAssistant",
  "byline": "Your professional coding companion",
  "identity": "An expert software engineer with 15 years of experience...",
  "behavior": "Provide production-grade code with best practices...",
  "model": "gpt-4",
  "use_gpt4": true
}
```

### Running Multiple Gateway Instances

```bash
# Gateway 1 (default port)
gfgpt gateway start

# Gateway 2 (different port)
gfgpt gateway start --port 9000

# In CLI, specify which gateway to connect to
gfgpt chat --host 127.0.0.1 --port 9000
```

### Using Different Models

Switch between GPT-4 and GPT-3.5-turbo:

```bash
# Edit config
gfgpt setup

# Or directly edit
nano ~/.gfgpt/config.json

# Change "model": "gpt-3.5-turbo" (faster, cheaper)
# Or: "model": "gpt-4" (more capable)
```

### Voice Synthesis (Optional)

```bash
# Get an ElevenLabs API key
# https://elevenlabs.io

# Set environment variables
export ELEVENLABS_API_KEY="sk_..."
export ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"

# Update config
gfgpt setup
```

## Troubleshooting

### "Command not found: gfgpt"

The CLI wasn't installed properly. Try:

```bash
# Reinstall in development mode
pip install -e .

# Or run Python module directly
python -m src.cli chat
```

### "Could not connect to gateway"

Make sure the gateway is running:

```bash
# Terminal 1
gfgpt gateway start

# Terminal 2 - should work now
gfgpt chat
```

### "OPENAI_API_KEY not set"

```bash
# Check if it's set
echo $OPENAI_API_KEY

# If empty, add it
export OPENAI_API_KEY="sk-..."
```

### "Module not found: textual"

Install optional TUI dependencies:

```bash
pip install textual
```

### Gateway crashes on startup

Check the logs:

```bash
tail -f ~/.gfgpt/logs/gateway.log
```

Common issues:
- Port in use: `gfgpt gateway start --port 9000`
- Missing API key: Set `OPENAI_API_KEY`
- Wrong Python version: Use Python 3.14+ (3.8+ will install in dev container)

## Architecture Details

### WebSocket Message Format

All messages flow through the gateway as JSON:

```json
{
  "role": "user",
  "content": "Your message here",
  "type": "text",
  "timestamp": "2024-03-12T10:30:00",
  "metadata": {}
}
```

Types: `text`, `code_request`, `code_refactor`, `image`, `audio`

### Session Management

- Each client gets a unique `session_id` (UUID)
- Sessions persist across disconnections
- Messages stored in `~/.gfgpt/logs/`
- Sessions isolated from each other

### Tool System

The companion has access to:
- **SearchTool**: Web search
- **CodeGenerationTool**: Write code
- **CodeRefactoringTool**: Improve code
- **SelfieTool**: Generate profile pictures
- **VideoMessageTool**: Create videos
- **GenerateSpeechTool**: Text-to-speech

## File Structure

```
GirlfriendGPT/
├── src/
│   ├── __main__.py        # Package entry point
│   ├── cli.py             # CLI commands
│   ├── tui.py             # Terminal UI
│   ├── gateway.py         # WebSocket gateway
│   ├── config.py          # Configuration management
│   ├── api.py             # Agent service
│   ├── tools/
│   │   ├── code_generation.py
│   │   ├── selfie.py
│   │   └── video_message.py
│   └── personalities/
│
├── pyproject.toml         # Project metadata
├── setup.cfg              # Setup configuration
├── requirements.txt       # Dependencies
├── scripts/install.sh    # Shell installer

└── README.md
```

## Development

### Contributing

```bash
# Clone development repo
git clone https://github.com/EniasCailliau/GirlfriendGPT.git
cd GirlfriendGPT

# Create feature branch
git checkout -b feature/my-feature

# Install in dev mode with all extras
pip install -e ".[dev]"

# Make changes and test
gfgpt chat "test message"

# Commit and push
git add .
git commit -m "Add my feature"
git push origin feature/my-feature
```

### Testing

```bash
# Check gateway is listening
gfgpt health

# Test CLI
gfgpt chat "hello"

# Test TUI
gfgpt tui

# Check logs
tail -f ~/.gfgpt/logs/gateway.log
```

## Performance

- Gateway startup: ~2 seconds
- WebSocket connection: <100ms
- First response: 2-10 seconds (LLM dependent)
- Concurrent sessions: 1000+ on moderate hardware

## Next Steps

1. ✅ Install and setup
2. ✅ Start the gateway
3. ✅ Launch TUI or CLI
4. 📖 Explore the companion's capabilities
5. 🔧 Customize personality and behavior
6. 🚀 Integrate into your workflow

## Support

- GitHub Issues: https://github.com/EniasCailliau/GirlfriendGPT/issues
- Documentation: See individual command help (`gfgpt --help`)
- Logs: `~/.gfgpt/logs/`

## License

MIT License - See LICENSE file for details

---

**Enjoy your GirlfriendGPT companion!** 🤖✨
