"""
Configuration management for Taskhub MCP server.
"""

import os
import json
from typing import Any, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for Taskhub."""
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._config_file: Optional[Path] = None
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file and environment variables."""
        # Load from config file
        config_path = self._find_config_file()
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                self._config_file = config_path
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")
        
        # Override with environment variables
        self._load_env_overrides()
    
    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in standard locations."""
        search_paths = [
            Path.cwd() / "config.json",
            Path.cwd() / "configs" / "config.json",
            Path.home() / ".taskhub" / "config.json",
            Path("/etc/taskhub/config.json") if os.name != 'nt' else None,
        ]
        
        for path in search_paths:
            if path and path.exists():
                return path
        return None
    
    def _load_env_overrides(self) -> None:
        """Load environment variable overrides."""
        env_mappings = {
            "TASKHUB_DB_PATH": "database.path",
            "TASKHUB_LOG_LEVEL": "logging.level",
            "TASKHUB_LOG_FILE": "logging.file",
            "TASKHUB_CACHE_TTL": "cache.ttl",
            "TASKHUB_MAX_CACHE_SIZE": "cache.max_size",
            "TASKHUB_SERVER_HOST": "server.host",
            "TASKHUB_SERVER_PORT": "server.port",
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self.set(config_key, self._convert_env_value(value))
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean values
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'off'):
            return False
        
        # Numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self, path: Optional[str] = None) -> None:
        """Save current configuration to file."""
        save_path = Path(path) if path else (self._config_file or Path.cwd() / "config.json")
        
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving config to {save_path}: {e}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            "path": self.get("database.path", "taskhub.db"),
            "pool_size": self.get("database.pool_size", 5),
            "timeout": self.get("database.timeout", 30),
            "check_same_thread": self.get("database.check_same_thread", False),
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        return {
            "ttl": self.get("cache.ttl", 300),
            "max_size": self.get("cache.max_size", 1000),
            "enabled": self.get("cache.enabled", True),
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            "level": self.get("logging.level", "INFO"),
            "file": self.get("logging.file"),
            "format": self.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            "max_bytes": self.get("logging.max_bytes", 10 * 1024 * 1024),  # 10MB
            "backup_count": self.get("logging.backup_count", 5),
        }
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration."""
        return {
            "host": self.get("server.host", "localhost"),
            "port": self.get("server.port", 8000),
            "debug": self.get("server.debug", False),
        }


# Global configuration instance
config = Config()

# Convenience functions
def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def reload_config() -> None:
    """Reload configuration from file and environment."""
    config.load_config()


# Default configuration template
DEFAULT_CONFIG = {
    "database": {
        "path": "taskhub.db",
        "pool_size": 5,
        "timeout": 30,
        "check_same_thread": False,
        "pragmas": {
            "journal_mode": "WAL",
            "synchronous": "NORMAL",
            "cache_size": 10000,
            "foreign_keys": 1,
            "temp_store": "memory",
        }
    },
    "cache": {
        "enabled": True,
        "ttl": 300,
        "max_size": 1000,
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "max_bytes": 10485760,
        "backup_count": 5,
    },
    "server": {
        "host": "localhost",
        "port": 8000,
        "debug": False,
    },
    "performance": {
        "monitoring_enabled": True,
        "slow_query_threshold": 1.0,
    }
}