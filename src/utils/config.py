import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """配置管理类"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.logging_file = self.config_dir / "logging.json"
        
        self._config = {}
        self._logging_config = {}
        self._load_configs()
    
    def _load_configs(self):
        """加载配置文件"""
        # 加载主配置
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f) or {}
        else:
            self._config = self._get_default_config()
            self._save_config()
        
        # 加载日志配置
        if self.logging_file.exists():
            with open(self.logging_file, 'r', encoding='utf-8') as f:
                self._logging_config = json.load(f) or {}
        else:
            self._logging_config = self._get_default_logging_config()
            self._save_logging_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "server": {
                "host": "localhost",
                "port": 8000,
                "transport": "stdio"
            },
            "storage": {
                "type": "json",
                "data_dir": "data"
            },
            "task": {
                "default_lease_duration": 30,
                "max_lease_duration": 120,
                "cleanup_interval": 300
            }
        }
    
    def _get_default_logging_config(self) -> Dict[str, Any]:
        """获取默认日志配置"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.FileHandler",
                    "level": "DEBUG",
                    "formatter": "standard",
                    "filename": "logs/taskhub.log"
                }
            },
            "loggers": {
                "": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False
                },
                "taskhub": {
                    "handlers": ["console", "file"],
                    "level": "DEBUG",
                    "propagate": False
                }
            }
        }
    
    def _save_config(self):
        """保存配置文件"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
    
    def _save_logging_config(self):
        """保存日志配置"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.logging_file, 'w', encoding='utf-8') as f:
            json.dump(self._logging_config, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config()
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self._logging_config


# 全局配置实例
config = Config()