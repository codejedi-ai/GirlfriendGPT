# GirlfriendGPT → Intimate Companion 

**An OpenClaw-style AI companion framework for engineers.** Your personal code-writing, intimate AI assistant with websocket support and CLI integration.

This is an enhanced version of GirlfriendGPT that adds professional websocket support, CLI tools for code generation, and code refactoring capabilities.

## 🚀 Features

* **WebSocket Server**: Direct real-time communication with your AI agent (low-latency)
* **CLI Tool**: Command-line interface for easy interaction
* **AI Agent**: Powered by OpenAI GPT models with extensible tool system
* **Personality System**: Fully customizable agent with unique voice and behavior
* **Configuration Management**: Hot-reload configuration without restarting
* **Multi-tool Support**: Content writing, image/video/audio generation, social media posting
* **Session Management**: Multiple concurrent user sessions with independent contexts

## Features (Capabilities through Chat)

* **Content Writing**: Generate articles, social media posts, creative content
* **Media Generation**: Image, video, and audio generation capabilities
* **Social Media**: Post to social platforms directly
* **Custom Voice**: Utilize ElevenLabs for unique voice synthesis
* **Personality**: Fully customizable AI personality, name, and behavior

## Getting Started

### Quick Start with WebSocket Gateway

Install dependencies and start the gateway server:

```bash
pip install -r requirements.txt
```

Start the gateway in one terminal:

```bash
gfgpt gateway start
```

In another terminal, start chatting:

```bash
gfgpt chat          # Interactive chat with agent
gfgpt health        # Check gateway health
gfgpt onboard       # Run setup/onboarding wizard
```

### Gateway Management

```bash
# Start gateway in background
gfgpt gateway start --daemon

# Check gateway status
gfgpt gateway status

# Stop gateway
gfgpt gateway stop

# Restart gateway
gfgpt gateway restart
```

## CLI Commands

```bash
# Interactive chat with the agent
gfgpt chat

# Single message to the agent  
gfgpt chat "Your message here"

# Check if gateway is running and get status
gfgpt health

# Run initial setup/configuration
gfgpt onboard

# Gateway management
gfgpt gateway start       # Start WebSocket gateway server
gfgpt gateway stop        # Stop WebSocket gateway server  
gfgpt gateway restart     # Restart WebSocket gateway server
gfgpt gateway status      # Check gateway status
```

## Gateway REST API

The WebSocket gateway provides these HTTP endpoints for management:

- `GET /health` - Gateway health status and active sessions
- `GET /info` - Agent metadata (name, model, available tools)
- `POST /reload` - Reload agent configuration from file
- `WS /ws/{session_id}` - WebSocket endpoint for real-time communication

## Architecture

GirlfriendGPT is built as a modular AI agent system with WebSocket-based communication:

**Core Components:**
- **Agent** (`src/agent/`) - AI logic powered by OpenAI GPT models
- **Gateway** (`src/gateway/`) - WebSocket server (FastAPI + Uvicorn) for real-time bidirectional communication
- **CLI** (`cli.py`) - Command-line interface for user interaction
- **Config** (`src/config.py`) - Centralized configuration management with hot-reload support
- **Tools** (`src/agent/tools/`) - Agent capabilities (content writing, image/video/audio generation)

**Communication Flow:**
```
[CLI User] --websocket--> [Gateway Server] ---> [Agent] ---> [LLM (OpenAI)]
                                ^                   |
                                |___________________|
                           (hot-reload config)
```

**Technology Stack:**
- **Framework**: FastAPI + Uvicorn (HTTP/WebSocket server)
- **LLM**: OpenAI GPT-4 / GPT-3.5-turbo
- **CLI**: Click (command-line framework)
- **Communication**: WebSockets for real-time bidirectional messaging

## Project Structure

```
src/
├── agent/              # AI agent implementation
│   ├── agent.py       # Agent logic and message handling
│   └── tools/         # Agent capabilities
│       ├── audio_generation.py
│       ├── content_writing.py
│       ├── image_generation.py
│       ├── social_media.py
│       └── video_generation.py
├── gateway/           # WebSocket server  
│   └── server.py      # FastAPI app with WS endpoint
├── config.py          # Configuration management
└── ui/                # Legacy UI components (Streamlit)

cli.py                 # CLI entry point
requirements.txt       # Python dependencies

templates/
├── config.json        # Agent configuration template
├── tools.md          # Tool documentation
└── personalities/    # Personality definitions (JSON)
```

## Advanced Usage

See [WEBSOCKET_CLI_GUIDE.md](docs/WEBSOCKET_CLI_GUIDE.md) for detailed documentation on:
- WebSocket protocol and messages
- Custom personality configuration
- Agent tool usage
- Configuration management
- Architecture deep-dive

## Configuration

Configuration is managed through `~/.gfgpt/config.json`. You can:

1. **Set via environment variables** (applied on startup):
```bash
export OPENAI_API_KEY="your-openai-key"
export OPENAI_MODEL="gpt-4"  # or gpt-3.5-turbo
```

2. **Edit config file directly**:
```bash
~/.gfgpt/config.json
```

3. **Reload configuration** without restarting the gateway:
```bash
curl -X POST http://localhost:18789/reload
# or use the gateway: gfgpt gateway restart
```

**Configuration Options:**
```json
{
  "name": "Luna",
  "byline": "Your AI companion",
  "identity": "A helpful AI assistant",
  "behavior": "Be engaging and helpful",
  "gateway_port": 18789,
  "gateway_host": "127.0.0.1",
  "model_provider": {
    "openai": {
      "api_key": "sk-...",
      "model": "gpt-4"
    }
  },
  "elevenlabs_api_key": "optional",
  "elevenlabs_voice_id": "optional"
}
```

## Custom Personalities

Personality templates are stored in `src/templates/personalities/`. Each personality is a JSON file defining:
- Name, byline, identity, and behavior
- Custom system prompts
- Tool availability
- Voice settings

See the example personalities (luna.json, alix_earle.json, etc.) for reference.

## Roadmap

* Long-term memory for context awareness
* Persistent conversation history across sessions
* Multi-user sessions with shared contexts
* Voice cloning capabilities
* Advanced tool integration (web search, file operations)
* Persistent conversation database

## Technical Notes

**Design Principles:**
- **Modular architecture**: Agent logic, gateway, and CLI are decoupled
- **Real-time communication**: WebSocket for low-latency bidirectional messaging
- **Hot-reload configuration**: Update agent settings without restarting the gateway
- **Simple deployment**: Single Python module, minimal dependencies
- **Thread-safe agent access**: Safe concurrent access with thread locks

**Key Technologies:**
- OpenAI GPT models for intelligence
- FastAPI + WebSockets for real-time communication
- Click for CLI with intuitive commands
- Configuration-based agent customization

## Contributing

Pull requests welcome! Areas for contribution:

### 🤖 Add a New Personality
Personalities are JSON files in `src/templates/personalities/` that define:
- Name, byline, identity statement  
- Behavior instructions for the agent
- Tool availability
- Voice settings (optional)

1. Create a new JSON file in `src/templates/personalities/`
2. Define your personality (see luna.json as an example)
3. Test with the CLI: `gfgpt chat`
4. Submit PR with title: "{name} - {description}"

### 🛠️ Contribute Code
- Add new tools in `src/agent/tools/`
- Improve agent logic in `src/agent/agent.py`
- Enhance CLI commands in `cli.py`
- Fix bugs and add features!





## License
This project is licensed under the MIT License. 
