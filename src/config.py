"""Configuration management for GirlfriendGPT."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration for GirlfriendGPT."""
    
    CONFIG_DIR = Path.home() / ".gfgpt"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    STATE_FILE = CONFIG_DIR / "state.json"
    LOGS_DIR = CONFIG_DIR / "logs"
    
    DEFAULT_CONFIG = {
        "name": "Luna",
        "byline": "Your AI Companion",
        "identity": "A helpful and supportive AI assistant",
        "behavior": "Be warm, engaging, and intelligent",
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
    }
    
    @classmethod
    def ensure_config_dir(cls) -> Path:
        """Ensure config directory exists."""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        return cls.CONFIG_DIR
    
    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Load configuration from file."""
        cls.ensure_config_dir()
        
        if cls.CONFIG_FILE.exists():
            with open(cls.CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create default config
            return cls.DEFAULT_CONFIG.copy()
    
    @classmethod
    def save_config(cls, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        cls.ensure_config_dir()
        
        with open(cls.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuration saved to {cls.CONFIG_FILE}")
    
    @classmethod
    def update_config(cls, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration with new values."""
        config = cls.load_config()
        config.update(updates)
        cls.save_config(config)
        return config
    
    @classmethod
    def get_config(cls, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        config = cls.load_config()
        return config.get(key, default)
    
    @classmethod
    def load_state(cls) -> Dict[str, Any]:
        """Load application state (gateway PID, etc)."""
        cls.ensure_config_dir()
        
        if cls.STATE_FILE.exists():
            try:
                with open(cls.STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading state: {e}")
                return {}
        return {}
    
    @classmethod
    def save_state(cls, state: Dict[str, Any]) -> None:
        """Save application state."""
        cls.ensure_config_dir()
        
        with open(cls.STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    
    @classmethod
    def get_log_file(cls, name: str = "gateway") -> Path:
        """Get log file path."""
        cls.ensure_config_dir()
        return cls.LOGS_DIR / f"{name}.log"
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate configuration.
        
        Returns:
            (is_valid, error_message)
        """
        required_keys = ["name", "model_provider", "model"]
        
        for key in required_keys:
            if key not in config:
                return False, f"Missing required key: {key}"
        
        if config["model_provider"] not in ["openai", "anthropic", "cohere"]:
            return False, f"Unknown model provider: {config['model_provider']}"
        
        return True, None
    
    @classmethod
    def reset_to_defaults(cls) -> Dict[str, Any]:
        """Reset configuration to defaults."""
        cls.save_config(cls.DEFAULT_CONFIG.copy())
        return cls.load_config()
