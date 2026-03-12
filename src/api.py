"""Minimal agent configuration and implementation for SmolAgent.

This module replaces the previous Steamship-based `GirlfriendGPT` service
with a lightweight client that talks directly to OpenAI (or another LLM).
The `SmolAgent` is the "spinal cord" mentioned in the conversation; it is
responsible for generating responses to user messages and supports simple
code requests.

Because the Steamship service is no longer used, all imports from the
`steamship` package have been removed.  The configuration class is now a
plain dataclass and the agent itself wraps the OpenAI SDK.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI


@dataclass
class AgentConfig:
    """Configuration for the companion agent."""
    name: str = "Companion"
    byline: str = "Your AI companion"
    identity: str = "A helpful AI assistant"
    behavior: str = "Be helpful, supportive, and engaging"
    use_gpt4: bool = True
    model: str = field(init=False)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    def __post_init__(self):
        # determine model string based on flag
        self.model = "gpt-4" if self.use_gpt4 else "gpt-3.5-turbo"


class SmolAgent:
    """Lightweight agent client that uses OpenAI directly."""

    def __init__(self, config: AgentConfig):
        self.config = config
        api_key = os.environ.get("OPENAI_API_KEY", "")
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return (
            f"You are {self.config.name}, {self.config.byline}.\n"
            f"{self.config.identity}\n\n"
            f"Behavior: {self.config.behavior}\n"
            "Provide helpful, detailed responses to user questions."
        )

    def respond(self, user_message: str) -> str:
        """Generate a response from the LLM."""
        if not self.client:
            return "Error: OpenAI API key not configured"
        
        try:
            resp = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def code(self, request: str) -> str:
        """Convenience wrapper for code generation."""
        prompt = f"Write code for: {request}"
        return self.respond(prompt)


# export names for other modules
Agent = SmolAgent
Config = AgentConfig
