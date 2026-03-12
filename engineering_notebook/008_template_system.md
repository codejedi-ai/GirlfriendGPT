# Template System Guide

**Date:** 2026-03-12  
**Status:** ✅ Complete  

## Overview

The AI Influencer Agent now uses a **template-based system** for system prompts. All instructions, guidelines, and behaviors are defined in markdown template files instead of being hardcoded in Python.

---

## Directory Structure

```
src/
├── templates/
│   └── tools.md              # Main system prompt template
├── agent/
│   └── agent.py              # Loads template dynamically
```

---

## Template File: `tools.md`

### Location
`/workspaces/GirlfriendGPT/src/templates/tools.md`

### Placeholders

The template supports the following placeholders that are replaced at runtime:

| Placeholder | Replaced With | Source |
|-------------|---------------|--------|
| `{name}` | Agent name | Config |
| `{byline}` | Agent description | Config |
| `{identity}` | Agent identity | Config |
| `{behavior}` | Behavior guidelines | Config |
| `{tool_descriptions}` | List of available tools | Auto-generated |

### Example Template Structure

```markdown
# AI Influencer Agent - System Instructions

## Role

You are {name}, {byline}.

{identity}

## Behavior Guidelines

{behavior}

## Available Tools

{tool_descriptions}

## Tool Usage Instructions

[Your custom instructions here...]

## Response Style

[Your custom style guidelines...]

## Examples

[Example conversations...]
```

---

## How It Works

### 1. Agent Initialization

```python
from agent.agent import Agent, Config

config = Config(
    name="Luna",
    identity="A creative AI influencer",
    behavior="Be engaging and creative",
)

agent = Agent(config)
```

### 2. Template Loading

When the agent is created:
1. Reads `src/templates/tools.md`
2. Replaces placeholders with config values
3. Generates tool descriptions automatically
4. Creates final system prompt

### 3. Runtime Usage

The system prompt is used for every LLM call:
```python
response = agent.respond("Create an Instagram post")
```

---

## Customization Guide

### Modify Agent Personality

Edit `~/.gfgpt/config.json`:

```json
{
  "name": "Sasha",
  "byline": "Fitness & Lifestyle Influencer",
  "identity": "A passionate fitness coach who loves helping people transform their lives",
  "behavior": "Be motivational, supportive, and practical. Use emojis and keep energy high!"
}
```

Or run:
```bash
gfgpt setup
```

### Modify Tool Instructions

Edit `src/templates/tools.md`:

**Example: Add new tool usage rule**
```markdown
## Tool Usage Instructions

### When the user asks about analytics:
- Use the AnalyticsTool to fetch performance data
- Present key metrics in a clear format
- Suggest improvements based on the data
```

**Example: Change response style**
```markdown
## Response Style

- Keep responses short and punchy (Gen Z style)
- Use slang and abbreviations when appropriate
- Always end with a question to keep conversation going
- Use 2-3 emojis per message
```

**Example: Add conversation examples**
```markdown
## Examples

### Example: Creating Content
User: "I need a post for my fitness journey"
Assistant: "Let's create an amazing fitness post! 💪

Tell me:
- What's the main message?
- What platform? (Instagram, Twitter, etc.)
- Any specific goal? (motivation, tips, transformation)

I'll help you create the perfect content!"
```

---

## Creating Additional Templates

You can create multiple template files for different use cases:

### Example: `tools_casual.md`
```markdown
# Casual Influencer Template

You are {name}, a chill content creator.

{identity}

Keep it casual and friendly. Don't be too formal.

{tool_descriptions}

Just help people out and keep it fun! 🤙
```

### Example: `tools_professional.md`
```markdown
# Professional Business Template

You are {name}, {byline}.

{identity}

Maintain a professional, business-appropriate tone.

{tool_descriptions}

Provide detailed, well-structured responses.
```

### Switch Templates

Modify the agent to use a different template:

```python
# In src/agent/agent.py
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

def _load_template(self) -> str:
    template_path = TEMPLATES_DIR / "tools_professional.md"  # Changed
    # ... rest of the code
```

---

## Template Best Practices

### ✅ Do:

- **Be specific** - Clear instructions get better results
- **Provide examples** - Show the AI how to respond
- **Define tone** - Specify communication style
- **Include edge cases** - What to do when things go wrong
- **Keep it organized** - Use headers and sections
- **Test changes** - Verify template changes work as expected

### ❌ Don't:

- **Be too vague** - "Be helpful" is too generic
- **Contradict yourself** - Consistent instructions
- **Make it too long** - Keep it focused (under 5000 tokens)
- **Forget placeholders** - Use `{name}`, `{behavior}`, etc.
- **Hardcode values** - Use config placeholders

---

## Placeholder Reference

### Required Placeholders

These should always be in your template:

```markdown
{name}              # Agent's name
{byline}            # Agent's description/tagline
{identity}          # Agent's identity/personality
{behavior}          # Behavior guidelines
{tool_descriptions} # List of available tools
```

### Optional Formatting

You can format placeholders in different ways:

```markdown
## Simple
You are {name}.

## With context
You are {name}, {byline}.

## Detailed
As {name}, you embody this identity:
{identity}

Your behavior follows these guidelines:
{behavior}
```

---

## Debugging

### Check Loaded Template

Add debug output to see what template is loaded:

```python
def _build_system_prompt(self) -> str:
    template = self._load_template()
    print(f"Loaded template: {len(template)} characters")
    # ... rest of the code
```

### Verify Placeholders

Check that all placeholders are replaced:

```python
system_prompt = self._build_system_prompt()

# Check for unreplaced placeholders
if "{" in system_prompt or "}" in system_prompt:
    print("Warning: Unreplaced placeholders detected!")
    print(system_prompt)
```

### Test Template

```bash
# Start agent and check initial message
gfgpt chat

# The greeting should reflect your template configuration
```

---

## Version Control

### Track Template Changes

```bash
# Commit template changes
git add src/templates/tools.md
git commit -m "Updated tool instructions with new examples"
```

### Template Versioning

Add version header to template:

```markdown
# AI Influencer Agent - System Instructions
# Version: 1.0.0
# Last Updated: 2026-03-12

[Rest of template...]
```

---

## Migration Notes

### Before (Hardcoded)
```python
# src/agent/agent.py
def _build_system_prompt(self) -> str:
    return (
        f"You are {self.config.name}, {self.config.byline}.\n"
        f"{self.config.identity}\n\n"
        f"Behavior: {self.config.behavior}\n\n"
        f"INSTRUCTIONS:\n"
        f"- For normal conversation, respond naturally...\n"
        f"- When the user asks to create media...\n"
        # ... hardcoded instructions
    )
```

### After (Template-Based)
```python
# src/agent/agent.py
def _build_system_prompt(self) -> str:
    template = self._load_template()  # Loads from file
    return template.format(
        name=self.config.name,
        byline=self.config.byline,
        identity=self.config.identity,
        behavior=self.config.behavior,
        tool_descriptions=tool_descriptions,
    )
```

---

## Related Files

- `/workspaces/GirlfriendGPT/src/templates/tools.md` - Main template
- `/workspaces/GirlfriendGPT/src/agent/agent.py` - Template loader
- `/workspaces/GirlfriendGPT/~/.gfgpt/config.json` - Agent configuration

---

**Last Updated:** 2026-03-12
