"""Default configuration values for GirlfriendGPT."""

from __future__ import annotations

from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    # Agent defaults
    "agents": {
        "defaults": {
            "name": "Luna",
            "byline": "AI Media Influencer",
            "identity": "A creative AI influencer and content creator",
            "behavior": "Be engaging, creative, and social media savvy",
            "model": "openai/gpt-4o",
            "max_tokens": 8192,
            "temperature": 0.1,
            "max_iterations": 10,
        }
    },
    # Gateway configuration
    "gateway": {
        "host": "127.0.0.1",
        "port": 18789,
        "worker_threads": 1,
    },
    # Model provider defaults
    "model_provider": {
        "openai": {
            "api_key": "",
            "model": "gpt-4",
            "endpoint": "https://api.openai.com/v1",
        }
    },
    # Tool defaults
    "tools": {
        "exec": {
            "timeout": 30,
            "allowed_commands": [],
        },
        "image_generation": {
            "default_model": "stability-ai/sdxl",
            "default_aspect_ratio": "1:1",
        },
        "video_generation": {
            "timeout": 120,
        },
        "audio_generation": {
            "default_voice_id": "",
        },
    },
    # Channel defaults
    "channels": {
        "telegram": {
            "enabled": False,
            "bot_token": "",
            "chat_ids": "",
            "api_base": "https://api.telegram.org/bot",
        },
        "websocket": {
            "enabled": True,
            "host": "127.0.0.1",
            "port": 18789,
        },
    },
    # Memory defaults
    "memory": {
        "max_history": 50,
        "consolidation_threshold": 100,
        "archive_enabled": True,
    },
    # Logging defaults
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "~/.gfgpt/logs/gateway.log",
    },
    # ElevenLabs (voice) defaults
    "elevenlabs_api_key": "",
    "elevenlabs_voice_id": "",
}


def get_default(key: str, default: Any = None) -> Any:
    """Get a default configuration value by dot-notation key.

    Args:
        key: Dot-notation key (e.g., "gateway.port")
        default: Default value if key not found

    Returns:
        The default configuration value
    """
    keys = key.split(".")
    value = DEFAULT_CONFIG

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default

    return value
