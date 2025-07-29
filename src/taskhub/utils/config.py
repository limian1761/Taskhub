"""
配置管理模块

该模块提供了配置文件的加载、管理和访问功能。
支持从文件加载配置，也支持通过环境变量覆盖配置。
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """配置管理类"""
    
    def __init__(self):
        """
        初始化配置管理器
        
        配置路径将自动解析到 src/configs 目录。
        """
        # 基准路径设置为本文件所在目录的父目录的父目录 (项目根目录)
        base_path = Path(__file__).parent.parent.parent
        
        # 配置文件路径
        self.config_dir = base_path / "configs"
        self.config_file = self.config_dir / "config.json"
        self.logging_file = self.config_dir / "logging.json"
        
        # 数据目录
        self.data_dir = base_path / "data"
        
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
                "data_dir": str(self.data_dir)  # 相对于工作目录的数据存储路径
            },
            "task": {
                "default_lease_duration": 30,
                "max_lease_duration": 120,
                "cleanup_interval": 300
            }
        }
    
    def _get_default_logging_config(self):
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
        """保存主配置文件"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
    
    def _save_logging_config(self):
        """保存日志配置文件"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.logging_file, 'w', encoding='utf-8') as f:
            json.dump(self._logging_config, f, indent=2, ensure_ascii=False)
    
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

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，使用点号分隔，如 "server.host"
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        设置配置值
        
        Args:
            key_path: 配置键路径，使用点号分隔，如 "server.host"
            value: 要设置的值
        """
        keys = key_path.split('.')
        config = self._config
        
        # 导航到倒数第二层
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 设置最后一层的值
        config[keys[-1]] = value
        
        # 保存配置
        self._save_config()


# 全局配置实例
config = Config()