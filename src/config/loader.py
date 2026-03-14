"""Configuration loader for GirlfriendGPT."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .schema import ConfigSchema
from .defaults import DEFAULT_CONFIG, get_default

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and manages configuration.

    This class provides:
    - Configuration file loading
    - Configuration file saving
    - Default value merging
    - Configuration watching (optional)
    """

    CONFIG_DIR = Path.home() / ".gfgpt"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize the configuration loader.

        Args:
            config_path: Path to configuration file (uses default if not specified)
        """
        self._config_path = config_path or self.CONFIG_FILE
        self._config: Optional[ConfigSchema] = None

    @classmethod
    def ensure_config_dir(cls) -> Path:
        """Ensure configuration directory exists.

        Returns:
            Configuration directory path
        """
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return cls.CONFIG_DIR

    def load(self) -> ConfigSchema:
        """Load configuration from file.

        Returns:
            Configuration schema
        """
        self.ensure_config_dir()

        if self._config_path.exists():
            try:
                with open(self._config_path, "r") as f:
                    data = json.load(f)
                    self._config = ConfigSchema.from_dict(data)
                    logger.info(f"Loaded configuration from {self._config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                self._config = ConfigSchema.from_dict(DEFAULT_CONFIG)
        else:
            # Create default configuration
            logger.info("Configuration file not found, using defaults")
            self._config = ConfigSchema.from_dict(DEFAULT_CONFIG)
            self.save()

        return self._config

    def save(self, config: Optional[ConfigSchema] = None) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save (uses current if not specified)
        """
        self.ensure_config_dir()

        config_to_save = config or self._config
        if not config_to_save:
            raise ValueError("No configuration to save")

        try:
            with open(self._config_path, "w") as f:
                json.dump(config_to_save.to_dict(), f, indent=2)
            logger.info(f"Saved configuration to {self._config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise

    def get(self) -> ConfigSchema:
        """Get the current configuration.

        Returns:
            Current configuration
        """
        if self._config is None:
            return self.load()
        return self._config

    def update(self, updates: Dict[str, Any]) -> ConfigSchema:
        """Update configuration with new values.

        Args:
            updates: Dictionary of updates

        Returns:
            Updated configuration
        """
        config = self.get()

        # Apply updates to the schema
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self.save(config)
        return config

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value
        """
        config = self.get()
        return getattr(config, key, default)

    def reset_to_defaults(self) -> ConfigSchema:
        """Reset configuration to defaults.

        Returns:
            Default configuration
        """
        self._config = ConfigSchema.from_dict(DEFAULT_CONFIG)
        self.save()
        return self._config

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate the current configuration.

        Returns:
            (is_valid, error_message)
        """
        config = self.get()
        return config.validate()
