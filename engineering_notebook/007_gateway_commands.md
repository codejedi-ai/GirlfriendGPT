# Gateway Management Commands

**Date:** 2026-03-12  
**Status:** ✅ Complete  

## Overview

Added back gateway management commands to the `gfgpt` CLI for starting, stopping, and managing the gateway server.

---

## Available Commands

### `gfgpt gateway start`
Start the gateway server.

```bash
# Start in foreground
gfgpt gateway start

# Start in background (daemon mode)
gfgpt gateway start --daemon

# Custom port and host
gfgpt gateway start --port 8080 --host 0.0.0.0
```

**Options:**
- `--port` - Gateway port (default: 18789)
- `--host` - Gateway host (default: 127.0.0.1)
- `--daemon` - Run in background

### `gfgpt gateway stop`
Stop the running gateway server.

```bash
gfgpt gateway stop
```

### `gfgpt gateway restart`
Restart the gateway server.

```bash
gfgpt gateway restart
```

### `gfgpt gateway status`
Check if the gateway is running.

```bash
gfgpt gateway status
```

**Output:**
```
✅ Gateway is running
   PID: 12345
   Host: 127.0.0.1
   Port: 18789
   Status: ok
   Agent: Luna
   Sessions: 0
```

### `gfgpt chat`
Chat with the AI influencer agent.

```bash
# Interactive chat
gfgpt chat

# Single message
gfgpt chat "Create an Instagram post about fitness"
```

### `gfgpt health`
Check gateway health.

```bash
gfgpt health
```

### `gfgpt setup`
Run initial setup wizard.

```bash
gfgpt setup
```

---

## Usage Examples

### Start Server and Chat

```bash
# Start gateway in background
gfgpt gateway start --daemon

# Check it's running
gfgpt gateway status

# Start chatting
gfgpt chat
```

### Development Workflow

```bash
# Start in foreground (see logs)
gfgpt gateway start

# In another terminal, chat
gfgpt chat "Help me create content"

# Stop server (Ctrl+C in first terminal)
gfgpt gateway stop
```

### Check Health

```bash
# Quick health check
gfgpt health

# Or detailed status
gfgpt gateway status
```

---

## State Management

Gateway state is stored in `~/.gfgpt/state.json`:

```json
{
  "gateway_pid": 12345,
  "port": 18789,
  "host": "127.0.0.1"
}
```

This allows the CLI to:
- Track if the gateway is running
- Stop/restart the correct process
- Detect stale state files

---

## Log Files

When running in daemon mode, logs are stored in:
- `~/.gfgpt/gateway.log`

View logs:
```bash
tail -f ~/.gfgpt/gateway.log
```

---

## Command Hierarchy

```
gfgpt
├── gateway
│   ├── start [--daemon] [--port PORT] [--host HOST]
│   ├── stop
│   ├── restart
│   └── status
├── chat [MESSAGE]
├── health
└── setup
```

---

## Error Handling

The CLI handles:
- ✅ Already running detection
- ✅ Stale state file cleanup
- ✅ Process not found errors
- ✅ Connection failures
- ✅ Timeout handling

---

## Related Files

- `/workspaces/GirlfriendGPT/cli.py` - Main CLI with gateway commands
- `/workspaces/GirlfriendGPT/src/gateway/server.py` - Gateway server
- `/workspaces/GirlfriendGPT/src/config.py` - Configuration management
- `~/.gfgpt/state.json` - Runtime state
- `~/.gfgpt/gateway.log` - Server logs (daemon mode)

---

**Last Updated:** 2026-03-12
