import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """配置管理类"""
    
    def __init__(self, config_dir: str = "configs"):
        # 获取工作目录
        self.workspace_dir = Path(os.getcwd())
        
        # 配置文件路径
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.logging_file = self.config_dir / "logging.json"
        
        self._config = {}
        self._logging_config = {}
        self._load_configs()
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
    
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
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "server": {
                "host": "localhost",
                "port": 8000,
                "transport": "stdio"
            },
            "storage": {
                "type": "json",
                "data_dir": "data"  # 相对于工作目录的数据存储路径
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
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖配置"""
        # 数据目录配置
        data_dir = os.environ.get('TASKHUB_DATA_DIR')
        if data_dir:
            self.set("storage.data_dir", data_dir)
            
        # 服务器配置
        host = os.environ.get('TASKHUB_HOST')
        if host:
            self.set("server.host", host)
            
        port = os.environ.get('TASKHUB_PORT')
        if port:
            try:
                self.set("server.port", int(port))
            except ValueError:
                pass  # 如果端口号无效，保持默认值
                
        transport = os.environ.get('TASKHUB_TRANSPORT')
        if transport:
            self.set("server.transport", transport)
            
        # 任务配置
        lease_duration = os.environ.get('TASKHUB_LEASE_DURATION')
        if lease_duration:
            try:
                self.set("task.default_lease_duration", int(lease_duration))
            except ValueError:
                pass
                
        max_lease = os.environ.get('TASKHUB_MAX_LEASE')
        if max_lease:
            try:
                self.set("task.max_lease_duration", int(max_lease))
            except ValueError:
                pass
                
        cleanup = os.environ.get('TASKHUB_CLEANUP_INTERVAL')
        if cleanup:
            try:
                self.set("task.cleanup_interval", int(cleanup))
            except ValueError:
                pass

    @property
    def logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self._logging_config


# 全局配置实例
config = Config()