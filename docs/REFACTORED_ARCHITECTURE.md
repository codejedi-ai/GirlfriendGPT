# Refactored Architecture - GirlfriendGPT

This document describes the new domain-driven architecture for GirlfriendGPT, based on the Nanobot Structure Cleanup Plan.

## Directory Structure

```
src/
├── core/                    # 🧠 Core engine
│   ├── __init__.py
│   ├── loop.py              # Main agent loop (thread pool execution)
│   ├── context.py           # Agent context management
│   └── memory/              # Memory sub-package
│       ├── __init__.py
│       ├── store.py         # Session history storage
│       ├── consolidation.py # Message compression
│       └── archival.py      # Long-term memory
│
├── agents/                  # 🤖 Agent definitions
│   ├── __init__.py
│   ├── registry.py          # Agent registry
│   └── subagent.py          # Subagent spawning
│
├── tools/                   # 🔧 Tool system
│   ├── __init__.py
│   ├── registry.py          # Tool registration & discovery
│   ├── builtin/             # Built-in tools
│   │   └── __init__.py
│   └── mcp/                 # MCP tools
│       └── __init__.py
│
├── channels/                # 📡 Chat platforms
│   ├── __init__.py
│   └── base.py              # Abstract base channel class
│
├── providers/               # 🔌 LLM providers
│   ├── __init__.py
│   ├── base.py              # Abstract base provider
│   ├── registry.py          # Provider registry
│   └── litellm_adapter.py   # LiteLLM adapter
│
├── bus/                     # 📨 Message bus
│   ├── __init__.py
│   ├── events.py            # Event definitions
│   └── queue.py             # Message queue & bus
│
├── services/                # ⏰ Background services
│   ├── __init__.py
│   ├── cron.py              # Scheduled tasks
│   └── heartbeat.py         # Health checks
│
├── config/                  # ⚙️ Configuration
│   ├── __init__.py
│   ├── schema.py            # Config schema
│   ├── loader.py            # Config loader
│   └── defaults.py          # Default values
│
├── utils/                   # 🛠️ Utilities
│   ├── __init__.py
│   └── errors.py            # Exception hierarchy
│
├── agent/                   # 📦 Legacy (backward compat)
│   ├── agent.py
│   ├── loop.py
│   └── tools/
│
├── gateway/                 # 🌐 Gateway server
│   ├── gateway.py
│   └── telegram.py
│
├── cli/                     # 💻 CLI
│   └── start_personality.py
│
└── templates/               # 📄 Templates
    ├── config.json
    ├── tools.md
    └── personalities/
```

## Key Components

### Core (`src/core/`)

The core engine provides the fundamental agent execution infrastructure:

- **`AgentRunLoop`**: Non-blocking run loop that dispatches agent calls to worker threads
- **`AgentContext`**: Manages conversation context and tool results
- **`MemoryStore`**: In-memory storage for session message history
- **`MemoryConsolidator`**: Compresses old messages to save context window
- **`MemoryArchive`**: Long-term memory storage and retrieval

### Agents (`src/agents/`)

Agent definitions and management:

- **`AgentRegistry`**: Singleton registry for agent definitions
- **`Subagent`**: Spawns specialized subagents for delegated tasks

### Tools (`src/tools/`)

Tool system with decorator-based registration:

```python
from src.tools import register_tool

@register_tool(
    name="read_file",
    description="Read the contents of a file",
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"}
        },
        "required": ["path"]
    }
)
async def read_file(path: str) -> str:
    ...
```

### Channels (`src/channels/`)

Abstract base class for communication channels:

```python
from src.channels.base import BaseChannel

class TelegramChannel(BaseChannel):
    async def start(self) -> None:
        ...
    
    async def stop(self) -> None:
        ...
    
    async def send(self, message: OutboundMessage) -> None:
        ...
```

### Providers (`src/providers/`)

LLM provider abstraction via LiteLLM:

```python
from src.providers import BaseProvider, ProviderRegistry
from src.providers.litellm_adapter import LiteLLMAdapter

provider = LiteLLMAdapter(ProviderConfig(
    api_key="...",
    model="openai/gpt-4o",
))
```

### Bus (`src/bus/`)

Event-driven message bus:

- **`InboundMessage`**: Messages from channels
- **`OutboundMessage`**: Messages to channels
- **`MessageBus`**: Pub/sub event bus
- **`MessageQueue`**: Async queue for event processing

### Services (`src/services/`)

Background services:

- **`CronService`**: Interval-based task scheduling
- **`HeartbeatService`**: Periodic health checks

### Config (`src/config/`)

Configuration management:

- **`ConfigSchema`**: Type-safe configuration
- **`ConfigLoader`**: File-based loading/saving
- **`DEFAULT_CONFIG`**: Default values

### Utils (`src/utils/`)

Shared utilities:

- **Exception hierarchy**: `GirlfriendGPTError`, `ChannelError`, `ToolExecutionError`, etc.

## Migration Guide

### Old → New Imports

| Old | New |
|-----|-----|
| `from src.agent.loop import AgentRunLoop` | `from src.core.loop import AgentRunLoop` |
| `from src.config import ConfigManager` | `from src.config.loader import ConfigLoader` |
| N/A | `from src.tools import register_tool` |
| N/A | `from src.bus import MessageBus` |

### Backward Compatibility

The old `src/agent/` module is kept for backward compatibility. All new code should use the new structure.

## Usage Examples

### Creating a Custom Tool

```python
from src.tools import register_tool

@register_tool(
    name="get_weather",
    description="Get current weather for a location",
    schema={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"]
    }
)
async def get_weather(location: str) -> str:
    # Implementation
    return f"Weather in {location}: Sunny, 25°C"
```

### Creating a Custom Channel

```python
from src.channels.base import BaseChannel
from src.bus import InboundMessage, OutboundMessage

class DiscordChannel(BaseChannel):
    async def start(self) -> None:
        # Initialize Discord bot
        ...
    
    async def stop(self) -> None:
        # Cleanup
        ...
    
    async def send(self, message: OutboundMessage) -> None:
        # Send to Discord
        ...
```

### Using the Message Bus

```python
from src.bus import MessageBus, InboundMessage

bus = MessageBus()
await bus.start()

# Publish a message
msg = InboundMessage(
    session_id="session-123",
    content="Hello!",
    sender_id="user-456",
    channel="telegram",
)
await bus.publish(msg)

# Subscribe to events
from src.bus.events import EventType

def handler(event):
    print(f"Received: {event}")

bus.subscribe(EventType.INBOUND_MESSAGE, handler)
```

### Using Memory

```python
from src.core.memory import MemoryStore, MemoryConsolidator, MemoryArchive

store = MemoryStore(max_messages_per_session=100)
consolidator = MemoryConsolidator()
archive = MemoryArchive()

# Store messages
await store.append("session-123", "user", "Hello!")
await store.append("session-123", "assistant", "Hi there!")

# Get history
history = await store.get_history("session-123", limit=50)

# Consolidate old messages
if len(history) > 100:
    summary = await consolidator.consolidate(history)
    await archive.archive("session-123", summary)
```

## Testing

```bash
# Run tests
pytest tests/

# Type checking
mypy src/

# Linting
black src/
isort src/
```

## Next Steps

1. **Migrate existing tools** to use the new registry pattern
2. **Implement channel integrations** (Telegram, Discord, etc.)
3. **Add MCP support** for external tool discovery
4. **Implement semantic search** in MemoryArchive
5. **Add streaming support** in providers

## References

- [Nanobot Structure Cleanup Plan](../docs/NANOBOT_REFACTOR.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Configuration Examples](CONFIGURATION_EXAMPLES.md)
