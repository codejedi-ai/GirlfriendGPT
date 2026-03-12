# 🚀 Quick Start Guide - Intimate Companion

Welcome! This guide will get you up and running with the Intimate Companion agent in 5 minutes.

## Prerequisites

- Python 3.8+
- OpenAI API key (`OPENAI_API_KEY`)
- Steamship API key (`STEAMSHIP_API_KEY`)

Get free keys at:
- [OpenAI](https://platform.openai.com/api-keys)
- [Steamship](https://steamship.com)

## Installation

```bash
# 1. Clone/navigate to the repository
cd GirlfriendGPT

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Install CLI globally
python setup_cli.py
```

## Set Up Environment

```bash
# Add your API keys
export OPENAI_API_KEY="sk-..."
export STEAMSHIP_API_KEY="..."

# Optional: Voice synthesis keys
export ELEVENLABS_API_KEY="..."
export ELEVENLABS_VOICE_ID="..."
```

## Option 1: Use the CLI (Easiest)

```bash
# Terminal 1 - Start the websocket server
python run_websocket.py --name "Luna"

# Terminal 2 - Chat with your companion
companion chat
```

Then interact:
```
You: hello
Companion: Hello! How can I help you today?

You: write a python function to calculate fibonacci
Companion: Here's a fibonacci function...

You: exit
Goodbye!
```

## Option 2: Write Code

```bash
# Generate code
companion code "FastAPI REST API with database models"

# Refactor existing code
companion refactor myfile.py "add error handling and type hints"

# Ask questions
companion ask --message "Best practices for Python projects?"
```

## Option 3: Use Python Directly

```python
import asyncio
from examples.websocket_client import IntimateCompanionClient

async def main():
    client = IntimateCompanionClient()
    response = await client.code_generation(
        "Python function to sum a list"
    )
    print(response)

asyncio.run(main())
```

## Customizing Your Companion

Edit `run_websocket.py` or command line:

```bash
python run_websocket.py \
    --name "DevGirl" \
    --byline "Your personal AI engineer" \
    --identity "Expert software developer with 10 years experience" \
    --behavior "Write clean, efficient, well-documented code" \
    --use-gpt4 True
```

## Available Tools

Once the server is running, your companion has these abilities:

- 🤖 **Chat** - Natural conversation
- 💻 **Write Code** - Generate production-ready code
- 🔧 **Refactor** - Improve existing code
- 🔍 **Search** - Look up information
- 📸 **Selfies** - Generate profile pictures
- 🎬 **Videos** - Create video messages
- 🎤 **Voice** - Text-to-speech responses

## Troubleshooting

### "Cannot connect to server"
```bash
# Make sure server is running
companion health

# Check port availability
lsof -i :8000
```

### "API key not found"
```bash
# Verify environment variables
echo $OPENAI_API_KEY
echo $STEAMSHIP_API_KEY

# Add keys if needed
export OPENAI_API_KEY="..."
export STEAMSHIP_API_KEY="..."
```

### "Module not found"
```bash
# Reinstall requirements
pip install -r requirements.txt --upgrade
```

## Next Steps

1. **Read** [WEBSOCKET_CLI_GUIDE.md](WEBSOCKET_CLI_GUIDE.md) for detailed commands
2. **Explore** [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
3. **Try** the examples in `agent/`
4. **Customize** your companion's personality and voice
5. **Deploy** to production using Docker or Kubernetes

## Example Workflows

### Research & Coding Session
```bash
companion chat
> I need to build a web scraper in Python
> (Companion explains approach)
> Can you write the code?
> (Companion generates code)
> Now add error handling
> (Companion refactors)
```

### Code Review Assistant
```bash
companion refactor myapi.py "improve performance"
companion refactor models.py "add type hints"
companion code "write unit tests for myapi.py"
```

### Learn by Building
```bash
companion ask "What's the best way to structure a Flask app?"
companion code "Basic Flask app with authentication"
companion ask "How should I handle database migrations?"
```

## Key Features

✨ **Real-time WebSocket** - No polling, instant responses
🎯 **Code-Aware** - Understands context and best practices
🗣️ **Voice-Enabled** - Optional text-to-speech
🎨 **Customizable** - Full personality control
🚀 **Fast** - GPT-4 quality at GPT-3.5 speeds (with optimization)

## Architecture Highlights

- **Framework**: Steamship (proven AI agent framework)
- **LLM**: OpenAI GPT-4/3.5-turbo (configurable)
- **Transport**: WebSocket (real-time) + Telegram (optional)
- **Tools**: Code generation, refactoring, search, multimedia

## Getting Help

- 📖 See [WEBSOCKET_CLI_GUIDE.md](WEBSOCKET_CLI_GUIDE.md) for full documentation
- 🏗️ See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- 💬 [GitHub Issues](https://github.com/EniasCailliau/GirlfriendGPT/issues)

## What's New vs Original

| Feature | Before | Now |
|---------|--------|-----|
| Connection | Telegram only | WebSocket + Telegram |
| Code Tools | None | CodeGen + CodeRefactor |
| CLI | No | Yes (full featured) |
| Sessions | No | Persistent |
| Real-time | Through Telegram | Direct WebSocket |
| Direct API | No | Yes |

## Tips & Tricks

```bash
# Use different models for speed vs quality
python run_websocket.py --use-gpt4 false  # Faster, cheaper
python run_websocket.py --use-gpt4 true   # Better quality

# Custom personality
python run_websocket.py --name "PyMaster" --identity "Python expert"

# Different port
python run_websocket.py --port 8001

# Connect from another machine
companion --server ws://192.168.1.100:8000 chat
```

## Production Deployment

```bash
# Using environment variables
OPENAI_API_KEY="..." \
STEAMSHIP_API_KEY="..." \
python run_websocket.py --host 0.0.0.0

# Using Docker
docker build -t companion .
docker run -e OPENAI_API_KEY="..." -p 8000:8000 companion

# Using Steamship Cloud
ship serve remote
```

---

**Ready to go!** Start with `python run_websocket.py` and `companion chat` 🚀
