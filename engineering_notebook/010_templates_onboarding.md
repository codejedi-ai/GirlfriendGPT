# Templates Onboarding

**Date:** 2026-03-12  
**Status:** ✅ Complete  

## Overview

During onboarding (`gfgpt setup`), the templates folder is automatically copied from the source (`src/templates/`) to the user's configuration folder (`~/.gfgpt/templates/`).

---

## Directory Structure

### Source Templates (Package)
```
/workspaces/GirlfriendGPT/
└── src/
    └── templates/
        ├── config.json               # Default config template
        ├── tools.md                  # System prompt template
        └── personalities/            # Personality presets
```

### User Templates (After Onboarding)
```
~/.gfgpt/
└── templates/
    ├── config.json                   # User's config template
    ├── tools.md                      # User's system prompt
    └── personalities/                # User's personality presets
```

---

## Onboarding Flow

### Step 1: Run Setup
```bash
gfgpt setup
```

### Step 2: Templates Copied
```
✅ Copied templates to ~/.gfgpt/templates/
   You can edit these to customize your agent
```

### Step 3: Configuration Wizard
```
🤖 AI Influencer Agent Setup

Agent name [Luna]: 
Personality identity []:
Behavior description []:
OpenAI API Key []: 
```

### Step 4: Config Saved
```
✓ Configuration saved to ~/.gfgpt/config.json

Next steps:
  gfgpt gateway start    # Start the gateway
  gfgpt chat             # Start chatting
```

---

## Template Loading Priority

The system loads templates in this order:

1. **`~/.gfgpt/templates/config.json`** (User's template) ✅ **Highest Priority**
2. **`src/templates/config.json`** (Source template)
3. **Hardcoded defaults** (Fallback)

This means:
- User templates **always** take precedence
- You can customize templates without modifying source code
- Source templates are only used if user templates don't exist

---

## Files Copied During Onboarding

| File | Purpose | Customizable |
|------|---------|--------------|
| `config.json` | Default bot configuration | ✅ Yes |
| `tools.md` | System prompt instructions | ✅ Yes |
| `personalities/` | Personality presets folder | ✅ Yes |

---

## Customization Workflow

### After Onboarding

1. **Edit user templates:**
   ```bash
   nano ~/.gfgpt/templates/config.json
   nano ~/.gfgpt/templates/tools.md
   ```

2. **Reset config to use new templates:**
   ```python
   from src.config import ConfigManager
   ConfigManager.reset_to_defaults()
   ```

3. **Restart gateway:**
   ```bash
   gfgpt gateway restart
   ```

---

## Re-copy Templates

If you want to refresh templates from source:

```bash
# Delete user templates
rm -rf ~/.gfgpt/templates

# Run setup again
gfgpt setup
```

Or programmatically:
```python
from src.config import ConfigManager
import shutil
from pathlib import Path

# Remove user templates
shutil.rmtree(Path.home() / ".gfgpt/templates")

# Copy fresh templates
ConfigManager.copy_templates_to_user_dir()
```

---

## Template Loading Logic

```python
def _load_template(cls) -> Dict[str, Any]:
    # 1. Check user's templates folder first
    user_template = Path.home() / ".gfgpt/templates/config.json"
    if user_template.exists():
        return json.load(open(user_template))
    
    # 2. Fall back to source templates
    source_template = Path(__file__).parent / "templates/config.json"
    if source_template.exists():
        return json.load(open(source_template))
    
    # 3. Last resort: hardcoded defaults
    return HARDCODED_DEFAULTS
```

---

## Benefits

### ✅ User-Centric
- Templates live in user's home directory
- Easy to find and edit (`~/.gfgpt/templates/`)
- No need to navigate source code

### ✅ Version Control Friendly
- Source templates tracked in git
- User templates ignored (personal config)
- Updates don't overwrite user customizations

### ✅ Upgrade Safe
- Package updates don't affect user templates
- Users keep their customizations
- Can optionally refresh from source

### ✅ Consistent Structure
- Same folder structure in source and user dir
- Easy to understand and navigate
- Predictable file locations

---

## Example: First Run

```bash
# Fresh installation
$ gfgpt setup

🤖 AI Influencer Agent Setup

✅ Copied templates to ~/.gfgpt/templates/
   You can edit these to customize your agent

Agent name [Luna]: Sasha
Personality identity [A creative AI influencer]: A fitness coach...
Behavior description [Be engaging]: Be motivational...
OpenAI API Key []: sk-...

✓ Configuration saved

Next steps:
  gfgpt gateway start
  gfgpt chat
```

### What Happened:
1. ✅ Created `~/.gfgpt/` directory
2. ✅ Copied `src/templates/` → `~/.gfgpt/templates/`
3. ✅ Loaded config from `~/.gfgpt/templates/config.json`
4. ✅ Updated config with user inputs
5. ✅ Saved to `~/.gfgpt/config.json`

---

## Troubleshooting

### Templates Not Copied

**Symptom:** "User templates folder already exists"

**Solution:**
```bash
# Check if templates exist
ls -la ~/.gfgpt/templates/

# Remove and re-copy
rm -rf ~/.gfgpt/templates
gfgpt setup
```

### Config Not Using User Templates

**Symptom:** Changes to `~/.gfgpt/templates/config.json` not reflected

**Solution:**
```bash
# Verify file exists
ls -la ~/.gfgpt/templates/config.json

# Check JSON validity
python -m json.tool ~/.gfgpt/templates/config.json

# Reset config to use template
gfgpt setup  # Or use ConfigManager.reset_to_defaults()
```

### Source Templates Missing

**Symptom:** "Source templates not found"

**Solution:**
```bash
# Check source templates exist
ls -la src/templates/

# Reinstall package
pip install -e .
```

---

## API Reference

### ConfigManager Methods

```python
from src.config import ConfigManager

# Copy templates to user folder
copied = ConfigManager.copy_templates_to_user_dir()  # Returns bool

# Load config (uses user templates first)
config = ConfigManager.load_config()

# Reset to defaults (from user templates)
config = ConfigManager.reset_to_defaults()

# Check template locations
user_templates = ConfigManager.TEMPLATES_DIR  # ~/.gfgpt/templates/
source_templates = ConfigManager.SOURCE_TEMPLATES  # src/templates/
```

---

## Related Files

- `/workspaces/GirlfriendGPT/src/config.py` - Template management
- `/workspaces/GirlfriendGPT/cli.py` - Setup command
- `/workspaces/GirlfriendGPT/src/templates/` - Source templates
- `~/.gfgpt/templates/` - User templates

---

**Last Updated:** 2026-03-12
