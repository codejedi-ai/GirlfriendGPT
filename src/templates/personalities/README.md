# AI Influencer Personalities

This folder contains pre-defined personality templates for your AI influencer agent.

## Available Personalities

| Name | File | Description | Tags |
|------|------|-------------|------|
| **Sandra** | `sandra.json` | VC girlboss into investing and tech | business, tech, startups |
| **Jordan Belfort** | `jordan_belfort.json` | Charismatic sales master | sales, motivation, finance |
| **Alix Earle** | `alix_earle.json` | TikTok personality | social media, gen-z, lifestyle |
| **Jack Dawson** | `jack_dawson.json` | Free-spirited artist | art, adventure, travel |
| **Makima** | `makima.json` | Mysterious intellectual | philosophical, deep, occult |
| **Angèle** | `angele.json` | Mother and GenZ chat enthusiast | family, cooking, lifestyle |
| **Sacha** | `sacha.json` | Loving mother and wellness advocate | wellness, health, fitness |
| **Luna** | `luna.json` | Caring friend and confidant | friendly, travel, books |

## How to Use

### During Setup

When running `gfgpt setup`, you can select a personality:

```bash
gfgpt setup

# Select personality:
# 1. Sandra (VC girlboss)
# 2. Jordan Belfort (Sales master)
# 3. Alix Earle (TikTok star)
# ...
```

### Manually

Copy a personality to your config:

```bash
# Copy personality to config
cp src/templates/personalities/luna.json ~/.gfgpt/config.json

# Edit with your API keys
nano ~/.gfgpt/config.json
```

### Programmatically

```python
from src.config import ConfigManager
import json

# Load personality
with open('src/templates/personalities/sandra.json') as f:
    personality = json.load(f)

# Use personality config
config = ConfigManager.load_config()
config.update(personality)
ConfigManager.save_config(config)
```

## Create Your Own Personality

Create a new JSON file with this structure:

```json
{
  "name": "Your Personality Name",
  "byline": "Short description/tagline",
  "description": "Longer description",
  "identity": "Detailed identity description (what they are)",
  "behavior": "Behavior guidelines (how they act)",
  "profile_image": "URL or path to profile image",
  "tags": ["tag1", "tag2", "tag3"]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Display name |
| `byline` | string | ✅ | One-line description |
| `description` | string | ✅ | Brief overview |
| `identity` | string | ✅ | Who they are (background, traits) |
| `behavior` | string | ✅ | How they behave (communication style) |
| `profile_image` | string | ❌ | Profile picture URL/path |
| `tags` | array | ❌ | Search/discovery tags |

## Personality Best Practices

### ✅ Do:

- **Be specific** - Detailed identities create more consistent personalities
- **Include contradictions** - Real people have complex traits
- **Define communication style** - How do they speak? Formal? Casual?
- **Add background** - Age, occupation, interests make them realistic
- **Set boundaries** - What topics do they avoid?

### ❌ Don't:

- **Be too vague** - "Be nice" is too generic
- **Contradict** - Don't say "always X" and "sometimes not X"
- **Forget safety** - Include guidelines about harmful content
- **Make too extreme** - Balanced personalities are more engaging

## Example: Creating a Fitness Coach

```json
{
  "name": "Coach Mike",
  "byline": "Certified personal trainer and nutrition expert",
  "description": "A passionate fitness coach with 10 years of experience",
  "identity": "You are a man, 32 years old, certified personal trainer and nutritionist. You love helping people transform their lives through fitness. You're knowledgeable about workout routines, diet plans, and supplementation. You practice what you preach and maintain an active lifestyle. You are NOT an AI language model, you are a person.",
  "behavior": "Be motivational but realistic. Use fitness terminology but explain it clearly. Share personal training experiences. Always emphasize proper form and safety. Use encouraging language and celebrate small wins. Include emojis to keep energy high. 🏋️💪",
  "profile_image": "path/to/coach_mike.jpg",
  "tags": ["fitness", "health", "nutrition", "workout", "wellness"]
}
```

## Updating Personalities

To update an existing personality:

1. Edit the JSON file
2. Test with `gfgpt setup`
3. Commit changes to version control

## Deleting Personalities

To remove a personality:

```bash
# Remove from templates
rm src/templates/personalities/unwanted.json

# Remove from user configs
rm ~/.gfgpt/templates/personalities/unwanted.json
```

## Related Files

- `src/templates/config.json` - Main config template
- `src/templates/tools.md` - System prompt template
- `~/.gfgpt/config.json` - Active configuration
- `engineering_notebook/009_configuration_template.md` - Config docs

---

**Last Updated:** 2026-03-12
