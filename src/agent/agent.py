"""SmolAgent - Lightweight AI Agent for Media Influencer.

This is the core agent implementation that powers the AI influencer.
It uses OpenAI's API directly (no Steamship dependency) and supports
tool integration for media creation and social media management.
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

# Keep OpenAI import inside module to avoid issues if not installed
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# Get the templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


@dataclass
class AgentConfig:
    """Configuration for the AI influencer agent."""
    name: str = "Luna"
    byline: str = "AI Media Influencer"
    identity: str = "A creative AI influencer and content creator"
    behavior: str = "Be engaging, creative, and social media savvy"
    use_gpt4: bool = True
    model: str = field(init=False)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    tools: Optional[List[str]] = None  # List of tool names to enable

    def __post_init__(self):
        self.model = "gpt-4" if self.use_gpt4 else "gpt-3.5-turbo"


class SmolAgent:
    """Lightweight AI agent using OpenAI API with tool support."""

    def __init__(self, config: AgentConfig):
        self.config = config
        api_key = os.environ.get("OPENAI_API_KEY", "")
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.tools = self._load_tools()
        self.system_prompt = self._build_system_prompt()
        self.conversation_history = []

    def _load_tools(self) -> List[Any]:
        """Load enabled tools."""
        from agent.tools import (
            ImageGenerationTool,
            VideoGenerationTool,
            AudioGenerationTool,
            InstagramPostTool,
            TwitterPostTool,
            TikTokPostTool,
            YouTubePostTool,
            CaptionWriterTool,
            ScriptWriterTool,
            HashtagGeneratorTool,
            ContentCalendarTool,
        )

        # Load all tools by default (can be filtered by config later)
        return [
            ImageGenerationTool(),
            VideoGenerationTool(),
            AudioGenerationTool(),
            InstagramPostTool(),
            TwitterPostTool(),
            TikTokPostTool(),
            YouTubePostTool(),
            CaptionWriterTool(),
            ScriptWriterTool(),
            HashtagGeneratorTool(),
            ContentCalendarTool(),
        ]

    def _load_template(self) -> str:
        """Load the system prompt template from file."""
        template_path = TEMPLATES_DIR / "tools.md"
        
        if template_path.exists():
            with open(template_path, 'r') as f:
                return f.read()
        else:
            # Fallback to basic template if file not found
            return self._get_fallback_template()

    def _get_fallback_template(self) -> str:
        """Return a fallback template if file is not found."""
        return """# AI Influencer Agent

You are {name}, {byline}.
{identity}
Behavior: {behavior}

## Tools
{tool_descriptions}

## Instructions
- Respond naturally and engage with the user
- Use tools when user requests media creation or social media posting
- After using a tool, explain what you did and offer further help
- Be creative and think like a social media influencer
"""

    def _build_system_prompt(self) -> str:
        """Build the system prompt from template with config values."""
        template = self._load_template()
        
        tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.human_description}"
            for tool in self.tools
        ])
        
        # Replace placeholders with actual values
        system_prompt = template.format(
            name=self.config.name,
            byline=self.config.byline,
            identity=self.config.identity,
            behavior=self.config.behavior,
            tool_descriptions=tool_descriptions,
        )
        
        return system_prompt

    def _refresh_runtime_config(self):
        """Refresh mutable runtime config from disk before each invocation."""
        try:
            from config import ConfigManager

            latest = ConfigManager.load_config()
            openai_cfg = latest.get("model_provider", {}).get("openai", {})

            latest_model = openai_cfg.get("model", self.config.model)
            self.config.model = latest_model
            self.config.name = latest.get("name", self.config.name)
            self.config.byline = latest.get("byline", self.config.byline)
            self.config.identity = latest.get("identity", self.config.identity)
            self.config.behavior = latest.get("behavior", self.config.behavior)

            latest_key = openai_cfg.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
            if latest_key:
                os.environ["OPENAI_API_KEY"] = latest_key

            # Reinitialize client if needed and rebuild prompt from latest settings.
            self.client = OpenAI(api_key=latest_key) if OpenAI and latest_key else None
            self.system_prompt = self._build_system_prompt()
        except Exception:
            # Keep serving with in-memory settings if config refresh fails.
            pass

    def respond(self, user_message: str) -> str:
        """Generate a response from the LLM."""
        self._refresh_runtime_config()

        if not self.client:
            return "Error: OpenAI API key not configured"

        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            resp = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    *self.conversation_history[-10:],  # Keep last 10 messages for context
                ],
            )
            response = resp.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        except Exception as e:
            return f"Error: {str(e)}"

    def reset(self):
        """Clear conversation history."""
        self.conversation_history = []

    def get_tools_info(self) -> List[Dict[str, str]]:
        """Get information about available tools."""
        return [
            {
                "name": tool.name,
                "description": tool.human_description,
            }
            for tool in self.tools
        ]


# Export names for other modules
Agent = SmolAgent
Config = AgentConfig
