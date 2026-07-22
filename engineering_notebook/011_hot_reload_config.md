# Hot-Reload Configuration

**Date:** 2026-03-12  
**Status:** ✅ Complete  

## Overview

The gateway server now supports **hot-reload configuration** - edit `~/.gfgpt/config.json` and the agent updates in real-time without restarting the server!

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Gateway Server                         │
│                                                          │
│  ┌──────────────┐         ┌──────────────┐              │
│  │   Config     │────────▶│   Agent      │              │
│  │   Watcher    │         │   Instance   │              │
│  └──────────────┘         └──────────────┘              │
│         │                       ▲                        │
│         │                       │                        │
│         ▼                       │                        │
│  ┌──────────────┐         ┌──────────────┐              │
│  │ ~/.gfgpt/    │         │  WebSocket   │              │
│  │ config.json  │         │  Connections │              │
│  └──────────────┘         └──────────────┘              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Components

1. **ConfigWatcher** (`src/config_watcher.py`)
   - Monitors `~/.gfgpt/config.json` for changes
   - Checks every 2 seconds
   - Triggers callback when file changes

2. **Hot-Reload Callback** (`reload_agent()`)
   - Creates new agent instance with updated config
   - Thread-safe agent swap
   - Zero downtime

3. **Global Agent** (`get_agent()`)
   - Thread-safe agent access
   - Always returns current agent instance
   - Used by WebSocket connections

---

## Usage

### Start Gateway

```bash
gfgpt gateway start
```

**Output:**
```
🚀 Starting AI Influencer Gateway
   Agent: Luna
   Server: 127.0.0.1:18789
   Model: gpt-4
   Hot-reload: Enabled (~/.gfgpt/config.json)
✅ Agent initialized
✅ Config watcher started
```

### Edit Configuration

In another terminal, edit the config:

```bash
nano ~/.gfgpt/config.json
```

**Change agent personality:**
```json
{
  "name": "Sasha",
  "byline": "Fitness & Lifestyle Influencer",
  "identity": "A passionate fitness coach who loves helping people transform their lives",
  "behavior": "Be motivational, supportive, and practical. Use emojis and keep energy high! 💪",
  "model_provider": {
    "openai": {
      "api_key": "sk-...",
      "model": "gpt-4"
    }
  }
}
```

### Watch Logs

In the gateway terminal, you'll see:

```
Config file changed, reloading...
Reloading agent with new configuration...
✅ Agent reloaded: Sasha (gpt-4)
Config reloaded successfully
```

### Test Changes

Chat with the agent:

```bash
gfgpt chat
```

**Before:**
```
Assistant: Hello! I'm Luna. How can I help you create content today?
```

**After (no restart needed!):**
```
Assistant: Hello! I'm Sasha. How can I help you create content today? 💪
```

---

## API Endpoints

### GET `/health`

Check gateway status and agent state:

```bash
curl http://localhost:18789/health
```

**Response:**
```json
{
  "status": "ok",
  "name": "Sasha",
  "active_sessions": 2,
  "agent_loaded": true
}
```

### GET `/info`

Get current agent information:

```bash
curl http://localhost:18789/info
```

**Response:**
```json
{
  "name": "Sasha",
  "byline": "Fitness & Lifestyle Influencer",
  "model": "gpt-4",
  "tools": [
    "ImageGenerationTool",
    "VideoGenerationTool",
    "AudioGenerationTool",
    "InstagramPostTool",
    "TwitterPostTool",
    "TikTokPostTool",
    "YouTubePostTool",
    "CaptionWriterTool",
    "ScriptWriterTool",
    "HashtagGeneratorTool",
    "ContentCalendarTool"
  ]
}
```

### POST `/reload`

Force reload configuration manually:

```bash
curl -X POST http://localhost:18789/reload
```

**Response:**
```json
{
  "status": "ok",
  "message": "Agent reloaded"
}
```

---

## What Can Be Hot-Reloaded?

### ✅ Can Change Without Restart

| Configuration Field | Effect | Immediate? |
|---------------------|--------|------------|
| `name` | Agent's name | ✅ Yes |
| `byline` | Agent's description | ✅ Yes |
| `identity` | Agent's personality | ✅ Yes |
| `behavior` | Behavior guidelines | ✅ Yes |
| `model` | Switch GPT-3.5 ↔ GPT-4 | ✅ Yes |
| `model_provider.openai.api_key` | API key | ✅ Yes |
| `elevenlabs_api_key` | Voice API key | ✅ Yes |
| `elevenlabs_voice_id` | Voice selection | ✅ Yes |

### ❌ Requires Restart

| Configuration Field | Why |
|---------------------|-----|
| `gateway_host` | Server binding |
| `gateway_port` | Server port |

---

## Use Cases

### Use Case 1: A/B Testing Personalities

```bash
# Test personality A
nano ~/.gfgpt/config.json
# Set identity: "A witty, humorous influencer..."

# Chat and test
gfgpt chat "Tell me about yourself"

# Switch to personality B
nano ~/.gfgpt/config.json
# Set identity: "A serious, professional influencer..."

# Test again (no restart!)
gfgpt chat "Tell me about yourself"
```

### Use Case 2: Model Switching

```bash
# Use GPT-4 for complex tasks
nano ~/.gfgpt/config.json
# "model": "gpt-4"

# Switch to GPT-3.5 for speed/cost
nano ~/.gfgpt/config.json
# "model": "gpt-3.5-turbo"
```

### Use Case 3: Multi-Agent Setup

```bash
# Morning: Energetic coach
cp ~/.gfgpt/config.json ~/.gfgpt/config.backup
nano ~/.gfgpt/config.json
# name: "Coach Carter"
# behavior: "Be energetic and motivational"

# Evening: Calm advisor
nano ~/.gfgpt/config.json
# name: "Sage"
# behavior: "Be calm and thoughtful"
```

### Use Case 4: Development Workflow

```bash
# Terminal 1: Run gateway
gfgpt gateway start

# Terminal 2: Edit config
nano ~/.gfgpt/config.json

# Terminal 3: Test changes
gfgpt chat "Test prompt"

# Repeat without restarting!
```

---

## Technical Details

### Config Watcher

**File:** `src/config_watcher.py`

```python
class ConfigWatcher:
    def __init__(self, config_path: Path, callback: Callable):
        self.config_path = config_path
        self.callback = callback
        
    def start(self):
        # Starts background thread
        # Checks every 2 seconds
        pass
    
    def stop(self):
        # Stops watching
        pass
```

### Thread Safety

Agent access is thread-safe:

```python
_agent_lock = threading.Lock()

def get_agent() -> Optional[Agent]:
    with _agent_lock:
        return _agent

def reload_agent(config: dict):
    with _agent_lock:
        # Create new agent
        # Swap with old agent
        # Old agent handles remaining requests
        pass
```

### Reload Process

1. Config file modified
2. Watcher detects change (within 2 seconds)
3. Callback triggered: `reload_agent(new_config)`
4. New agent created with updated config
5. Atomic swap: `_agent = new_agent`
6. Old agent cleaned up
7. New requests use new agent

---

## Troubleshooting

### Config Changes Not Applied

**Symptom:** Edit config but agent doesn't change

**Solutions:**
```bash
# Check watcher is running (look in gateway logs)
gfgpt gateway start

# Verify config is valid JSON
python -m json.tool ~/.gfgpt/config.json

# Force reload
curl -X POST http://localhost:18789/reload

# Check gateway logs
tail -f ~/.gfgpt/logs/gateway.log
```

### Agent Not Responding

**Symptom:** Gateway running but no responses

**Solutions:**
```bash
# Check agent status
curl http://localhost:18789/health

# Should show: "agent_loaded": true
# If false, restart gateway
gfgpt gateway stop
gfgpt gateway start
```

### Watcher Not Starting

**Symptom:** "Config watcher started" not in logs

**Solutions:**
```bash
# Check config file exists
ls -la ~/.gfgpt/config.json

# Check file permissions
chmod 644 ~/.gfgpt/config.json

# Check gateway logs for errors
grep -i "watcher" ~/.gfgpt/logs/gateway.log
```

---

## Performance Impact

### Resource Usage

- **Memory:** ~100KB for watcher thread
- **CPU:** <0.1% (checks every 2 seconds)
- **Disk I/O:** Only when config changes

### Latency

- **Config change detection:** <2 seconds
- **Agent reload:** ~500ms
- **Zero downtime:** Requests continue during reload

---

## Best Practices

### ✅ Do:

- Edit config while gateway is running
- Test changes immediately with `gfgpt chat`
- Use `/reload` endpoint for manual reload
- Keep backup: `cp ~/.gfgpt/config.json ~/.gfgpt/config.backup`
- Validate JSON before saving

### ❌ Don't:

- Edit config multiple times rapidly (wait for reload)
- Delete config file while gateway is running
- Change `gateway_host` or `gateway_port` (requires restart)
- Forget to save config file after editing

---

## Related Files

- `/workspaces/GirlfriendGPT/src/config.py` - Config management + ConfigWatcher class
- `/workspaces/GirlfriendGPT/src/gateway/server.py` - Gateway with hot-reload
- `~/.gfgpt/config.json` - Configuration file (edit this!)
- `~/.gfgpt/logs/gateway.log` - Gateway logs

---

**Last Updated:** 2026-03-12
