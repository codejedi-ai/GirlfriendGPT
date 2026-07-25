"""Configuration management for GirlfriendGPT."""

from .schema import ConfigSchema
from .loader import ConfigLoader
from .defaults import DEFAULT_CONFIG
from .watcher import ConfigWatcher

# Backward compatibility - alias ConfigLoader as ConfigManager
ConfigManager = ConfigLoader

__all__ = ["ConfigSchema", "ConfigLoader", "DEFAULT_CONFIG", "ConfigManager", "ConfigWatcher"]
