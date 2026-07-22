"""Configuration schema for GirlfriendGPT."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ModelProviderConfig:
    """Configuration for a model provider."""

    api_key: str = ""
    model: str = "gpt-4"
    endpoint: Optional[str] = None
    max_tokens: int = 8192
    temperature: float = 0.1


@dataclass
class ChannelConfig:
    """Configuration for a channel."""

    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolConfig:
    """Configuration for a tool."""

    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigSchema:
    """Schema for GirlfriendGPT configuration.

    This class provides:
    - Type-safe configuration access
    - Validation
    - Serialization
    """

    # Agent identity
    name: str = "Luna"
    byline: str = "AI Media Influencer"
    identity: str = "A creative AI influencer and content creator"
    behavior: str = "Be engaging, creative, and social media savvy"

    # Model provider
    model_provider: Dict[str, ModelProviderConfig] = field(default_factory=dict)

    # Gateway
    gateway_host: str = "127.0.0.1"
    gateway_port: int = 18789
    agent_worker_threads: int = 1

    # Channels
    channels: Dict[str, ChannelConfig] = field(default_factory=dict)

    # Tools
    tools: Dict[str, ToolConfig] = field(default_factory=dict)

    # Memory
    memory_max_history: int = 50
    memory_consolidation_threshold: int = 100
    memory_archive_enabled: bool = True

    # ElevenLabs (voice)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # Logging
    logging_level: str = "INFO"
    logging_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging_file: str = "~/.gfgpt/logs/gateway.log"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigSchema":
        """Create a ConfigSchema from a dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            ConfigSchema instance
        """
        # Extract top-level fields
        config = cls()

        for field_name in [
            "name",
            "byline",
            "identity",
            "behavior",
            "gateway_host",
            "gateway_port",
            "agent_worker_threads",
            "memory_max_history",
            "memory_consolidation_threshold",
            "memory_archive_enabled",
            "elevenlabs_api_key",
            "elevenlabs_voice_id",
            "logging_level",
            "logging_format",
            "logging_file",
        ]:
            if field_name in data:
                setattr(config, field_name, data[field_name])

        # Parse model providers
        if "model_provider" in data:
            for name, provider_data in data["model_provider"].items():
                config.model_provider[name] = ModelProviderConfig(**provider_data)

        # Parse channels
        if "channels" in data:
            for name, channel_data in data["channels"].items():
                config.channels[name] = ChannelConfig(
                    enabled=channel_data.get("enabled", True),
                    config=channel_data,
                )

        # Parse tools
        if "tools" in data:
            for name, tool_data in data["tools"].items():
                config.tools[name] = ToolConfig(
                    enabled=tool_data.get("enabled", True),
                    config=tool_data,
                )

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema to a dictionary.

        Returns:
            Configuration dictionary
        """
        data: Dict[str, Any] = {
            "name": self.name,
            "byline": self.byline,
            "identity": self.identity,
            "behavior": self.behavior,
            "gateway_host": self.gateway_host,
            "gateway_port": self.gateway_port,
            "agent_worker_threads": self.agent_worker_threads,
            "memory_max_history": self.memory_max_history,
            "memory_consolidation_threshold": self.memory_consolidation_threshold,
            "memory_archive_enabled": self.memory_archive_enabled,
            "elevenlabs_api_key": self.elevenlabs_api_key,
            "elevenlabs_voice_id": self.elevenlabs_voice_id,
            "logging_level": self.logging_level,
            "logging_format": self.logging_format,
            "logging_file": self.logging_file,
        }

        # Add model providers
        data["model_provider"] = {
            name: {
                "api_key": provider.api_key,
                "model": provider.model,
                "endpoint": provider.endpoint,
                "max_tokens": provider.max_tokens,
                "temperature": provider.temperature,
            }
            for name, provider in self.model_provider.items()
        }

        # Add channels
        data["channels"] = {
            name: {
                "enabled": channel.enabled,
                **channel.config,
            }
            for name, channel in self.channels.items()
        }

        # Add tools
        data["tools"] = {
            name: {
                "enabled": tool.enabled,
                **tool.config,
            }
            for name, tool in self.tools.items()
        }

        return data

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate the configuration.

        Returns:
            (is_valid, error_message)
        """
        # Check required fields
        if not self.name:
            return False, "Name is required"

        # Check gateway port
        if not (1 <= self.gateway_port <= 65535):
            return False, "Gateway port must be between 1 and 65535"

        # Check model provider has at least one API key
        if self.model_provider:
            for name, provider in self.model_provider.items():
                if not provider.api_key:
                    return (
                        False,
                        f"Model provider '{name}' requires an API key",
                    )

        return True, None
