# Personality Templates

**Date:** 2026-03-12  
**Status:** ✅ Complete  

## Overview

Converted the legacy `girlfriends.json` catalog into individual personality template files that can be selected during onboarding or swapped at runtime.

---

## What Was Done

### Before: Single Catalog File
```
girlfriends.json (8 personalities in one array)
```

### After: Individual Personality Files
```
src/templates/personalities/
├── README.md
├── sandra.json           # VC girlboss
├── jordan_belfort.json   # Sales master
├── alix_earle.json       # TikTok star
├── jack_dawson.json      # Free-spirited artist
├── makima.json           # Mysterious intellectual
├── angele.json           # Mother & GenZ enthusiast
├── sacha.json            # Wellness advocate
└── luna.json             # Caring confidant
```

---

## Personality Structure

Each personality file contains:

```json
{
  "name": "Personality Name",
  "byline": "Short tagline",
  "description": "Brief overview",
  "identity": "Detailed identity (who they are)",
  "behavior": "Behavior guidelines (how they act)",
  "profile_image": "URL or path to image",
  "tags": ["tag1", "tag2", "tag3"]
}
```

### Field Mapping from girlfriends.json

| Old Field (girlfriends.json) | New Field | Notes |
|------------------------------|-----------|-------|
| `name` | `name` | Same |
| `description` | `description` | Same |
| `behavior[]` | `behavior` | Array → String (joined) |
| `identity[]` | `identity` | Array → String (joined) |
| - | `byline` | New field |
| `profile_image` | `profile_image` | Same |
| - | `tags` | New field for discovery |

---

## Available Personalities

### 1. Sandra - VC Girlboss
**File:** `sandra.json`  
**Tags:** business, tech, venture capital, startups, crypto  
**Description:** Young venture capitalist passionate about startups and innovation  
**Use Case:** Business content, tech reviews, startup advice

### 2. Jordan Belfort - Sales Master
**File:** `jordan_belfort.json`  
**Tags:** sales, motivation, business, finance, persuasion  
**Description:** Charismatic sales master and motivational speaker  
**Use Case:** Sales training, motivation, business content

### 3. Alix Earle - TikTok Star
**File:** `alix_earle.json`  
**Tags:** tiktok, social media, gen-z, content creator, lifestyle  
**Description:** Charismatic TikTok personality and content creator  
**Use Case:** Gen-Z content, lifestyle, social media tips

### 4. Jack Dawson - Free-Spirited Artist
**File:** `jack_dawson.json`  
**Tags:** art, adventure, travel, romantic, free spirit  
**Description:** Free-spirited artist and adventurer  
**Use Case:** Travel content, art, lifestyle

### 5. Makima - Mysterious Intellectual
**File:** `makima.json`  
**Tags:** mysterious, philosophical, intellectual, occult, deep  
**Description:** Mysterious and enigmatic intellectual  
**Use Case:** Deep conversations, philosophy, intellectual content

### 6. Angèle - Mother & GenZ Enthusiast
**File:** `angele.json`  
**Tags:** mother, family, gen-z, cooking, lifestyle  
**Description:** Mother, wife, and GenZ chat enthusiast  
**Use Case:** Family content, cooking, lifestyle

### 7. Sacha - Wellness Advocate
**File:** `sacha.json`  
**Tags:** mother, wellness, health, fitness, lifestyle  
**Description:** Loving mother and wellness advocate  
**Use Case:** Health content, fitness, wellness

### 8. Luna - Caring Confidant
**File:** `luna.json`  
**Tags:** friendly, caring, travel, books, confidant  
**Description:** Caring friend and confidant  
**Use Case:** Friendly conversations, travel, books

---

## Usage

### During Setup

```bash
gfgpt setup
```

Future enhancement: Add personality selection menu

### Manual Selection

```bash
# List available personalities
ls src/templates/personalities/*.json

# Copy personality to user config
cp src/templates/personalities/sandra.json ~/.gfgpt/config.json

# Add API keys
nano ~/.gfgpt/config.json

# Start gateway
gfgpt gateway start
```

### Runtime Swap (Hot-Reload)

```bash
# Gateway is running with Luna
gfgpt chat "Hi!"

# Copy new personality
cp src/templates/personalities/jordan_belfort.json ~/.gfgpt/config.json

# Gateway auto-reloads (within 2 seconds)
gfgpt chat "Hi!"  # Now Jordan Belfort responds!
```

### Programmatically

```python
from src.config import ConfigManager
import json

# Load personality
with open('src/templates/personalities/sandra.json') as f:
    personality = json.load(f)

# Get current config
config = ConfigManager.load_config()

# Update with personality (preserve API keys)
config.update({
    'name': personality['name'],
    'byline': personality['byline'],
    'identity': personality['identity'],
    'behavior': personality['behavior'],
})

# Save
ConfigManager.save_config(config)

# Gateway auto-reloads
```

---

## Creating Custom Personalities

### Step 1: Create JSON File

```json
{
  "name": "Coach Mike",
  "byline": "Certified personal trainer",
  "description": "Passionate fitness coach with 10 years experience",
  "identity": "You are a man, 32 years old, certified personal trainer...",
  "behavior": "Be motivational but realistic. Use fitness terminology...",
  "profile_image": "path/to/image.jpg",
  "tags": ["fitness", "health", "nutrition"]
}
```

### Step 2: Save to Templates

```bash
cp coach_mike.json src/templates/personalities/
```

### Step 3: Test

```bash
# Copy to user config
cp src/templates/personalities/coach_mike.json ~/.gfgpt/config.json

# Add API keys and test
nano ~/.gfgpt/config.json
gfgpt gateway start
gfgpt chat "Give me a workout tip"
```

---

## Migration from girlfriends.json

### Automatic Conversion

The personalities have already been converted from `girlfriends.json`:

```python
import json

# Load old format
with open('girlfriends.json') as f:
    girlfriends = json.load(f)

# Each entry converted to individual file
for gf in girlfriends:
    personality = {
        'name': gf['name'],
        'byline': gf['description'],
        'description': gf['description'],
        'identity': ' '.join(gf['identity']) if isinstance(gf['identity'], list) else gf['identity'],
        'behavior': ' '.join(gf['behavior']) if isinstance(gf['behavior'], list) else gf['behavior'],
        'profile_image': gf.get('profile_image', ''),
        'tags': []  # Add relevant tags
    }
    
    # Save to file
    filename = f"src/templates/personalities/{gf['name'].lower().replace(' ', '_')}.json"
    with open(filename, 'w') as f:
        json.dump(personality, f, indent=2)
```

### Keep or Delete girlfriends.json?

**Option A: Keep as catalog**
- Keep `girlfriends.json` for reference
- Shows all personalities in one file
- Useful for browsing

**Option B: Delete (Recommended)**
- Individual files are cleaner
- Easier to maintain
- Better for version control

---

## Benefits

### ✅ Modular
- Each personality is independent
- Easy to add/remove personalities
- No monolithic catalog file

### ✅ Discoverable
- Tags for search/filtering
- README with personality table
- Easy to browse

### ✅ Customizable
- Users can create their own
- Mix and match traits
- Version control friendly

### ✅ Runtime Swappable
- Hot-reload supports personality changes
- No gateway restart needed
- Test personalities quickly

---

## File Locations

| Location | Purpose |
|----------|---------|
| `src/templates/personalities/` | Source personality templates |
| `~/.gfgpt/templates/personalities/` | User's personality collection |
| `src/templates/personalities/README.md` | Personality documentation |

---

## Related Files

- `/workspaces/GirlfriendGPT/src/templates/personalities/` - Personality templates folder
- `/workspaces/GirlfriendGPT/girlfriends.json` - Legacy catalog (can be deleted)
- `/workspaces/GirlfriendGPT/src/templates/config.json` - Config template
- `/workspaces/GirlfriendGPT/engineering_notebook/012_personality_templates.md` - This doc

---

**Last Updated:** 2026-03-12
