"""Configuration watcher for GirlfriendGPT - watches config file for changes."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ConfigWatcher:
    """Watches configuration file for changes and triggers callbacks.

    This class provides:
    - File modification monitoring
    - Automatic config reloading
    - Callback notification on changes
    """

    def __init__(
        self,
        config_path: Path,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        """Initialize config watcher.

        Args:
            config_path: Path to configuration file to watch
            callback: Function to call when config changes (receives new config)
        """
        self.config_path = config_path
        self.callback = callback
        self._watch_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_modified: float = 0
        self._last_config: Dict[str, Any] = {}

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._last_config

    def _check_for_changes(self) -> bool:
        """Check if config file has been modified."""
        if not self.config_path.exists():
            return False

        try:
            current_modified = self.config_path.stat().st_mtime

            if current_modified > self._last_modified:
                self._last_modified = current_modified
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking config modification: {e}")
            return False

    def _watch_loop(self) -> None:
        """Main watch loop."""
        logger.info(f"Starting config watcher for {self.config_path}")

        # Initialize last modified time
        if self.config_path.exists():
            self._last_modified = self.config_path.stat().st_mtime
            self._last_config = self._load_config()

        while not self._stop_event.is_set():
            if self._check_for_changes():
                logger.info("Config file changed, reloading...")
                new_config = self._load_config()
                self._last_config = new_config

                if self.callback:
                    try:
                        self.callback(new_config)
                        logger.info("Config reloaded successfully")
                    except Exception as e:
                        logger.error(f"Error in config change callback: {e}")

            # Check every 2 seconds
            self._stop_event.wait(2.0)

        logger.info("Config watcher stopped")

    def start(self) -> None:
        """Start watching for config changes."""
        if self._watch_thread and self._watch_thread.is_alive():
            logger.warning("Config watcher already running")
            return

        self._stop_event.clear()
        self._watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._watch_thread.start()
        logger.info("Config watcher started")

    def stop(self) -> None:
        """Stop watching for config changes."""
        self._stop_event.set()
        if self._watch_thread:
            self._watch_thread.join(timeout=5.0)
        logger.info("Config watcher stopped")

    def get_current_config(self) -> Dict[str, Any]:
        """Get the current cached configuration."""
        return self._last_config

    def reload_now(self) -> Dict[str, Any]:
        """Force reload configuration immediately."""
        logger.info("Forcing config reload...")
        new_config = self._load_config()
        self._last_config = new_config

        if self.callback:
            try:
                self.callback(new_config)
                logger.info("Config reloaded on demand")
            except Exception as e:
                logger.error(f"Error in config reload callback: {e}")

        return new_config
