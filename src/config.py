"""Configuration management for GirlfriendGPT."""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Callable

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration for GirlfriendGPT."""

    CONFIG_DIR = Path.home() / ".gfgpt"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    STATE_FILE = CONFIG_DIR / "state.json"
    LOGS_DIR = CONFIG_DIR / "logs"
    TEMPLATES_DIR = CONFIG_DIR / "templates"
    
    # Path to the configuration template in project source
    PROJECT_ROOT = Path(__file__).parent.parent
    SOURCE_TEMPLATES = PROJECT_ROOT / "src" / "templates"
    CONFIG_TEMPLATE = SOURCE_TEMPLATES / "config.json"

    @classmethod
    def ensure_config_dir(cls) -> Path:
        """Ensure config directory exists."""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        return cls.CONFIG_DIR

    @classmethod
    def _load_template(cls) -> Dict[str, Any]:
        """Load default configuration from template file.
        
        Priority:
        1. ~/.gfgpt/templates/config.json (user's template)
        2. src/templates/config.json (source template)
        3. Hardcoded fallback
        """
        # First, try user's templates folder
        user_template = cls.TEMPLATES_DIR / "config.json"
        if user_template.exists():
            with open(user_template, 'r') as f:
                return json.load(f)
        
        # Second, try source templates folder
        if cls.CONFIG_TEMPLATE.exists():
            with open(cls.CONFIG_TEMPLATE, 'r') as f:
                return json.load(f)
        
        # Fallback to hardcoded defaults
        return {
            "name": "Luna",
            "byline": "AI Media Influencer",
            "identity": "A creative AI influencer and content creator",
            "behavior": "Be engaging, creative, and social media savvy",
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
            "telegram": {
                "bot_token": "",
                "chat_ids": ""
            }
        }

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Load configuration from file."""
        cls.ensure_config_dir()

        if cls.CONFIG_FILE.exists():
            with open(cls.CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create default config from template
            return cls._load_template().copy()

    @classmethod
    def copy_templates_to_user_dir(cls) -> bool:
        """Copy templates from source to user's ~/.gfgpt/templates/ folder.
        
        Returns:
            True if templates were copied, False if already exists
        """
        import shutil
        
        cls.ensure_config_dir()
        
        # Check if user templates already exist
        if cls.TEMPLATES_DIR.exists():
            logger.info("User templates folder already exists")
            return False
        
        # Copy source templates to user folder
        if cls.SOURCE_TEMPLATES.exists():
            shutil.copytree(cls.SOURCE_TEMPLATES, cls.TEMPLATES_DIR)
            logger.info(f"Copied templates to {cls.TEMPLATES_DIR}")
            return True
        else:
            logger.warning("Source templates not found")
            return False

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
        """Reset configuration to defaults from template."""
        cls.save_config(cls._load_template())
        return cls.load_config()

    @classmethod
    def get_templates_dir(cls) -> Path:
        """Get the templates directory path."""
        return cls.TEMPLATES_DIR

    @classmethod
    def get_source_templates_dir(cls) -> Path:
        """Get the source templates directory path."""
        return cls.SOURCE_TEMPLATES


class ConfigWatcher:
    """Watches configuration file for changes and triggers callbacks."""

    def __init__(self, config_path: Path, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
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
            with open(self.config_path, 'r') as f:
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

    def _watch_loop(self):
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

    def start(self):
        """Start watching for config changes."""
        if self._watch_thread and self._watch_thread.is_alive():
            logger.warning("Config watcher already running")
            return

        self._stop_event.clear()
        self._watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._watch_thread.start()
        logger.info("Config watcher started")

    def stop(self):
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
