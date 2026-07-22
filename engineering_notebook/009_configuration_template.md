# Configuration Template Guide

**Date:** 2026-03-12  
**Status:** ✅ Complete  

## Overview

The bot configuration is now driven by a **template file** (`config.json`) that serves as the default configuration for all new installations.

---

## File Locations

| File | Purpose | Location |
|------|---------|----------|
| **Template** | Default configuration | `src/templates/config.json` |
| **Active Config** | Bot's current configuration | `~/.gfgpt/config.json` |
| **State** | Runtime state (PID, etc) | `~/.gfgpt/state.json` |

---

## Configuration Template

### Location
`/workspaces/GirlfriendGPT/config.json`

### Structure

```json
{
  "name": "Luna",
  "byline": "AI Media Influencer",
  "identity": "A creative AI influencer and content creator",
  "behavior": "Be engaging, creative, and social media savvy",
  
  "model_provider": {
    "openai": {
      "api_key": "",
      "model": "gpt-4",
      "endpoint": "https://api.openai.com/v1"
    }
  },
  
  "elevenlabs_api_key": "",
  "elevenlabs_voice_id": "",
  
  "gateway_host": "127.0.0.1",
  "gateway_port": 18789,
  
  "telegram": {
    "bot_token": "",
    "chat_ids": ""
  }
}
```

---

## Configuration Fields

### Core Agent Settings

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Agent's name (e.g., "Luna", "Sasha") |
| `byline` | string | ✅ | Agent's description/tagline |
| `identity` | string | ✅ | Agent's personality and background |
| `behavior` | string | ✅ | Behavior guidelines and tone |

### LLM Settings

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_provider.openai.api_key` | string | ✅ | OpenAI API key |
| `model_provider.openai.model` | string | ✅ | Model to use (gpt-4, gpt-3.5-turbo) |
| `model_provider.openai.endpoint` | string | ❌ | API endpoint (default: official OpenAI) |

### Voice Settings (ElevenLabs)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `elevenlabs_api_key` | string | ❌ | ElevenLabs API key for voice generation |
| `elevenlabs_voice_id` | string | ❌ | Specific voice ID to use |

### Gateway Settings

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `gateway_host` | string | ❌ | Host to bind to (default: 127.0.0.1) |
| `gateway_port` | int | ❌ | Port for websocket server (default: 18789) |

### Telegram Integration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `telegram.bot_token` | string | ❌ | Telegram bot token from @BotFather |
| `telegram.chat_ids` | string | ❌ | Comma-separated list of allowed chat IDs |

---

## How It Works

### 1. First Run (No Config Exists)

When the bot runs for the first time:
1. Checks `~/.gfgpt/config.json`
2. File doesn't exist
3. Loads `config.json` from project root
4. Copies it to `~/.gfgpt/config.json`
5. Bot uses this configuration

### 2. Subsequent Runs

1. Checks `~/.gfgpt/config.json`
2. File exists
3. Loads existing configuration
4. Template is ignored (unless reset)

### 3. Reset to Defaults

```bash
# In Python
from src.config import ConfigManager
ConfigManager.reset_to_defaults()
```

This:
1. Loads `config.json`
2. Overwrites `~/.gfgpt/config.json`
3. Returns fresh configuration

---

## Customization Guide

### Method 1: Edit Template (For New Installations)

Edit the template file before first run:

```bash
nano config.json
```

**Changes will apply to:**
- New installations
- Users who run `gfgpt setup`
- Configs that are reset to defaults

### Method 2: Edit Active Config (For Existing Installation)

Edit the active configuration:

```bash
nano ~/.gfgpt/config.json
```

**Changes apply immediately** to the running bot.

### Method 3: Use Setup Wizard

```bash
gfgpt setup
```

Interactive wizard that updates the active config.

---

## Example Configurations

### Example 1: Fitness Influencer

```json
{
  "name": "Sasha",
  "byline": "Fitness & Lifestyle Influencer",
  "identity": "A passionate fitness coach and wellness advocate who loves helping people transform their lives",
  "behavior": "Be motivational, supportive, and practical. Share workout tips, nutrition advice, and wellness wisdom. Use emojis and keep energy high!",
  "model_provider": {
    "openai": {
      "api_key": "sk-...",
      "model": "gpt-4"
    }
  },
  "gateway_host": "0.0.0.0",
  "gateway_port": 8080
}
```

### Example 2: Tech Reviewer

```json
{
  "name": "Alex",
  "byline": "Tech Reviewer & Gadget Enthusiast",
  "identity": "A knowledgeable tech expert who breaks down complex gadgets into simple reviews",
  "behavior": "Be analytical but accessible. Use technical terms when appropriate but explain them. Stay objective and honest in reviews.",
  "model_provider": {
    "openai": {
      "api_key": "sk-...",
      "model": "gpt-4"
    }
  }
}
```

### Example 3: Travel Blogger

```json
{
  "name": "Maya",
  "byline": "World Traveler & Adventure Seeker",
  "identity": "A globetrotting adventurer who's visited 50+ countries and loves sharing travel stories",
  "behavior": "Be enthusiastic, curious, and inspiring. Share travel tips, cultural insights, and adventure stories. Use vivid descriptions.",
  "model_provider": {
    "openai": {
      "api_key": "sk-...",
      "model": "gpt-4"
    }
  },
  "elevenlabs_api_key": "...",
  "elevenlabs_voice_id": "Rachel"
}
```

---

## Validation

The configuration is validated when loaded:

```python
from src.config import ConfigManager

config = ConfigManager.load_config()
is_valid, error = ConfigManager.validate_config(config)

if not is_valid:
    print(f"Invalid config: {error}")
```

### Required Fields
- `name`
- `model_provider`
- `model_provider.openai.model`

### Optional Fields
All other fields have sensible defaults.

---

## Environment Variables

Some settings can be overridden via environment variables:

| Env Variable | Config Field | Priority |
|--------------|--------------|----------|
| `OPENAI_API_KEY` | `model_provider.openai.api_key` | Higher |
| `ELEVENLABS_API_KEY` | `elevenlabs_api_key` | Higher |

Environment variables take precedence over config file values.

---

## Backup & Restore

### Backup Configuration

```bash
# Backup current config
cp ~/.gfgpt/config.json ~/.gfgpt/config.backup.json

# Backup with timestamp
cp ~/.gfgpt/config.json ~/.gfgpt/config.$(date +%Y%m%d).json
```

### Restore Configuration

```bash
# Restore from backup
cp ~/.gfgpt/config.backup.json ~/.gfgpt/config.json

# Restart gateway to apply
gfgpt gateway restart
```

---

## Multiple Configurations

You can maintain multiple configurations:

```bash
# Create multiple configs
cp config.json config_fitness.json
cp config.json config_tech.json
cp config.json config_travel.json

# Edit each with different personalities
nano config_fitness.json
nano config_tech.json
nano config_travel.json

# Switch between them
cp config_fitness.json ~/.gfgpt/config.json
gfgpt gateway restart
```

---

## Troubleshooting

### Config Not Loading

**Symptom:** Bot uses default settings

**Solution:**
```bash
# Check if config exists
ls -la ~/.gfgpt/config.json

# Check permissions
chmod 644 ~/.gfgpt/config.json

# Validate JSON
python -m json.tool ~/.gfgpt/config.json
```

### Template Not Found

**Symptom:** Uses hardcoded defaults

**Solution:**
```bash
# Check template exists
ls -la config.json

# Check path in config.py
grep CONFIG_TEMPLATE src/config.py
```

### Reset Broken Config

```bash
# Delete corrupted config
rm ~/.gfgpt/config.json

# Bot will recreate from template on next run
gfgpt gateway start
```

---

## Best Practices

### ✅ Do:
- Keep template in version control
- Use environment variables for API keys
- Backup configs before major changes
- Validate JSON after editing
- Test changes in development first

### ❌ Don't:
- Commit API keys to git
- Edit config while gateway is running
- Use invalid JSON syntax
- Delete required fields
- Forget to restart gateway after changes

---

## Related Files

- `/workspaces/GirlfriendGPT/src/templates/config.json` - Configuration template
- `/workspaces/GirlfriendGPT/src/config.py` - Configuration manager
- `~/.gfgpt/config.json` - Active configuration
- `/workspaces/GirlfriendGPT/cli.py` - Setup wizard

---

**Last Updated:** 2026-03-12
