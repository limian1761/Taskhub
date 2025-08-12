"""
Configuration management for Taskhub.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

# Default configuration
DEFAULT_CONFIG = {
    "server": {
        "host": "localhost",
        "port": 8000,
        "transport": "stdio"
    },
    "storage": {
        "type": "sqlite",
        "data_dir": "data",
        "namespace": "default"
    },
    "task": {
        "default_lease_duration": 30,
        "max_lease_duration": 120,
        "cleanup_interval": 300
    },
    "database": {
        "directory": "data",
        "filename_pattern": "taskhub_{namespace}.db",
        "default_namespace": "default"
    },
    "workflow": {
        "evaluation_task_timeout_hours": 24  # Timeout in hours
    },
    "llm": {
        "api_key": "your_default_key_for_dev",  # Should be set via environment variables in production
        "model_name": "gpt-3.5-turbo"
    },
    "outline": {
        "url": "http://localhost:3000",  # Outline instance URL
        "api_key": "your_outline_api_key",  # Outline API key
        "collection_id": "your_collection_id"  # Default collection ID
    },
    "defaults": {
        "hunter_id": "unknown"
    },
    "logging": {
        "directory": "logs"
    }
}


class TaskhubConfig:
    """Taskhub configuration manager."""
    
    def __init__(self, config_path: str = "src/configs/config.json"):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file.
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults.
        
        Returns:
            Configuration dictionary.
        """
        config = DEFAULT_CONFIG.copy()
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # Merge with defaults
                    self._deep_merge(config, file_config)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_path}: {e}")
                print("Using default configuration.")
        
        return config
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge two dictionaries.
        
        Args:
            base: Base dictionary.
            override: Dictionary with override values.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get_database_path(self, namespace: str) -> str:
        """Get the database path for a given namespace.
        
        Args:
            namespace: The namespace.
            
        Returns:
            Database file path.
        """
        db_config = self.config["database"]
        directory = db_config["directory"]
        filename_pattern = db_config["filename_pattern"]
        filename = filename_pattern.format(namespace=namespace)
        return f"{directory}/{filename}"
    
    def get_default_namespace(self) -> str:
        """Get the default namespace.
        
        Returns:
            Default namespace.
        """
        return self.config["database"]["default_namespace"]
    
    def get_default_hunter_id(self) -> str:
        """Get the default hunter ID.
        
        Returns:
            Default hunter ID.
        """
        return self.config["defaults"]["hunter_id"]
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration.
        
        Returns:
            Server configuration dictionary.
        """
        return self.config["server"]


# Global configuration instance
config = TaskhubConfig()