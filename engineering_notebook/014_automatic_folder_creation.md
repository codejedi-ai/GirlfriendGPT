# Automatic Folder Creation

**Date:** 2026-03-12  
**Status:** ✅ Verified  

## Overview

All required folders are **automatically created** when you run onboarding or start the gateway. You don't need to manually create any folders!

---

## When Folders Are Created

### 1. During Onboarding ✅

```bash
gfgpt onboard
```

**What happens:**
1. `ConfigManager.ensure_config_dir()` is called
2. All folders are created automatically
3. Config file is created
4. Templates are copied

**Folders created:**
```
~/.gfgpt/
├── config.json          ← Created
├── logs/               ← Created
├── media/              ← Created
│   ├── img/           ← Created
│   ├── video/         ← Created
│   └── audio/         ← Created
└── templates/          ← Created (with files)
```

### 2. When Gateway Starts ✅

```bash
gfgpt gateway start
```

**What happens:**
1. `ConfigManager.load_config()` is called
2. `ConfigManager.ensure_config_dir()` is called
3. Log file is created
4. All missing folders are created

**Output:**
```
🚀 Starting AI Influencer Gateway
   Agent: Luna
   Server: 127.0.0.1:18789
   Logs: /home/vscode/.gfgpt/logs/gateway.log    ← Log file location
   Media: /home/vscode/.gfgpt/media              ← Media folder location
```

### 3. When Loading Config ✅

```python
from src.config import ConfigManager

# This automatically creates all folders
config = ConfigManager.load_config()
```

**Behind the scenes:**
```python
@classmethod
def load_config(cls) -> Dict[str, Any]:
    cls.ensure_config_dir()  # ← Creates all folders!
    
    if cls.CONFIG_FILE.exists():
        # Load existing config
    else:
        # Create from template
```

---

## What Gets Created

### Folders (7 total)

| Folder | Purpose | Created When |
|--------|---------|--------------|
| `~/.gfgpt/` | Root config folder | Always |
| `~/.gfgpt/logs/` | Log files | Always |
| `~/.gfgpt/media/` | Media root | Always |
| `~/.gfgpt/media/img/` | Generated images | Always |
| `~/.gfgpt/media/video/` | Generated videos | Always |
| `~/.gfgpt/media/audio/` | Generated audio | Always |
| `~/.gfgpt/templates/` | Templates | Always |

### Files (varies)

| File | Purpose | Created When |
|------|---------|--------------|
| `config.json` | Active config | Onboarding or first run |
| `logs/gateway.log` | Gateway logs | When gateway starts |
| `templates/config.json` | Config template | Onboarding (copied) |
| `templates/tools.md` | System prompt | Onboarding (copied) |
| `templates/personalities/*.json` | Personalities | Onboarding (copied) |

---

## Verification Tests

### Test 1: Fresh Install

```bash
# Remove everything
rm -rf ~/.gfgpt

# Run onboarding
gfgpt onboard

# Check folders
tree ~/.gfgpt -L 2
```

**Result:**
```
✅ All folders created automatically
```

### Test 2: Gateway Start

```bash
# Remove everything
rm -rf ~/.gfgpt

# Start gateway
gfgpt gateway start

# Check folders (in another terminal)
tree ~/.gfgpt -L 2
```

**Result:**
```
✅ All folders created automatically
✅ Log file created: logs/gateway.log
```

### Test 3: Programmatic Access

```python
from src.config import ConfigManager

# Just import and call ensure_config_dir
ConfigManager.ensure_config_dir()

# Check what was created
import os
os.system('tree ~/.gfgpt -L 2')
```

**Result:**
```
✅ All folders created automatically
```

---

## Code Reference

### ensure_config_dir() Method

```python
@classmethod
def ensure_config_dir(cls) -> Path:
    """Ensure config directory exists with all subdirectories."""
    cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    cls.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    cls.MEDIA_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    cls.MEDIA_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    cls.MEDIA_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    cls.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    return cls.CONFIG_DIR
```

**Key points:**
- `parents=True` - Creates parent directories if needed
- `exist_ok=True` - Doesn't fail if directory exists
- Called automatically by `load_config()`, `save_config()`, etc.

---

## What You DON'T Need to Do

### ❌ Don't Manually Create Folders

```bash
# DON'T do this - it's automatic!
mkdir -p ~/.gfgpt/logs
mkdir -p ~/.gfgpt/media/img
mkdir -p ~/.gfgpt/media/video
mkdir -p ~/.gfgpt/media/audio
```

### ❌ Don't Check if Folders Exist

```python
# DON'T do this - it's automatic!
import os
if not os.path.exists('~/.gfgpt'):
    os.makedirs('~/.gfgpt')
```

### ✅ Just Run Onboarding or Gateway

```bash
# This is all you need!
gfgpt onboard
# or
gfgpt gateway start
```

---

## Troubleshooting

### Folders Not Created

**Symptom:** Folders missing after onboarding

**Check:**
```bash
# Verify onboarding ran
ls -la ~/.gfgpt/

# Check for errors
gfgpt onboard 2>&1 | grep -i error
```

**Solution:**
```bash
# Manually trigger folder creation
python -c "from src.config import ConfigManager; ConfigManager.ensure_config_dir()"

# Then run onboarding
gfgpt onboard
```

### Permission Denied

**Symptom:** "Permission denied" error

**Solution:**
```bash
# Fix permissions
chmod -R 755 ~/.gfgpt/

# Or delete and recreate
rm -rf ~/.gfgpt
gfgpt onboard
```

### Wrong Location

**Symptom:** Folders created in wrong location

**Check:**
```bash
# Verify home directory
echo $HOME

# Check where folders were created
python -c "from src.config import ConfigManager; print(ConfigManager.CONFIG_DIR)"
```

---

## Summary

| Action | Folders Created? | Files Created? |
|--------|-----------------|----------------|
| `gfgpt onboard` | ✅ Yes | ✅ Config + Templates |
| `gfgpt gateway start` | ✅ Yes | ✅ Log file |
| `ConfigManager.load_config()` | ✅ Yes | ❌ No (unless missing) |
| `ConfigManager.ensure_config_dir()` | ✅ Yes | ❌ No |

**Bottom line:** Just run `gfgpt onboard` or `gfgpt gateway start` and everything is created automatically! 🎉

---

**Last Updated:** 2026-03-12
