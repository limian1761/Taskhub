"""
JSON存储实现

该模块提供了基于JSON文件的任务和代理的临时存储功能。
适用于开发环境或轻量级部署。
"""
import json
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from ..models.task import Task
from ..models.agent import Agent
from ..utils.config import config


class JsonStore:
    """基于JSON文件的存储实现，用于活跃任务和代理数据"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化JSON存储
        
        Args:
            data_dir: 数据存储目录路径。如果为None，则从全局配置中获取
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # 从全局配置中获取数据目录
            self.data_dir = Path(config.get("storage.data_dir"))
            
        self.data_dir.mkdir(exist_ok=True)
        
        self.tasks_file = self.data_dir / "tasks.json"
        self.agents_file = self.data_dir / "agents.json"
        
        # 初始化文件
        self._init_storage()
    
    def _init_storage(self):
        """初始化存储文件"""
        if not self.tasks_file.exists():
            self._save_json(self.tasks_file, {})
        if not self.agents_file.exists():
            self._save_json(self.agents_file, {})
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """
        加载JSON文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            JSON数据字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        """
        保存JSON文件
        
        Args:
            file_path: 文件路径
            data: 要保存的数据
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    # Task相关操作
    
    def save_task(self, task: Task) -> bool:
        """
        保存任务
        
        Args:
            task: 任务对象
            
        Returns:
            是否保存成功
        """
        tasks = self._load_json(self.tasks_file)
        tasks[task.id] = task.model_dump()
        self._save_json(self.tasks_file, tasks)
        return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        tasks = self._load_json(self.tasks_file)
        if task_id in tasks:
            return Task(**tasks[task_id])
        return None

    def list_tasks(self, status: Optional[str] = None, 
                   capability: Optional[str] = None) -> List[Task]:
        """
        列出任务
        
        Args:
            status: 任务状态过滤
            capability: 能力要求过滤
            
        Returns:
            任务列表
        """
        tasks = self._load_json(self.tasks_file)
        task_list = [Task(**task_data) for task_data in tasks.values()]
        
        if status:
            task_list = [t for t in task_list if t.status == status]
        if capability:
            task_list = [t for t in task_list if t.capability == capability]
        
        return task_list

    def update_task(self, task_id: str, **updates) -> bool:
        """
        更新任务
        
        Args:
            task_id: 任务ID
            **updates: 要更新的字段
            
        Returns:
            是否更新成功
        """
        tasks = self._load_json(self.tasks_file)
        if task_id in tasks:
            task_data = tasks[task_id]
            task_data.update(updates)
            # 更新时间戳
            task_data['updated_at'] = datetime.utcnow().isoformat()
            tasks[task_id] = task_data
            self._save_json(self.tasks_file, tasks)
            return True
        return False

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        tasks = self._load_json(self.tasks_file)
        if task_id in tasks:
            del tasks[task_id]
            self._save_json(self.tasks_file, tasks)
            return True
        return False

    # Agent相关操作
    
    def save_agent(self, agent: Agent) -> bool:
        """
        保存代理
        
        Args:
            agent: 代理对象
            
        Returns:
            是否保存成功
        """
        agents = self._load_json(self.agents_file)
        agents[agent.id] = agent.model_dump()
        self._save_json(self.agents_file, agents)
        return True

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        获取代理
        
        Args:
            agent_id: 代理ID
            
        Returns:
            代理对象，如果不存在则返回None
        """
        agents = self._load_json(self.agents_file)
        if agent_id in agents:
            return Agent(**agents[agent_id])
        return None

    def update_agent(self, agent_id: str, **updates) -> bool:
        """
        更新代理
        
        Args:
            agent_id: 代理ID
            **updates: 要更新的字段
            
        Returns:
            是否更新成功
        """
        agents = self._load_json(self.agents_file)
        if agent_id in agents:
            agent_data = agents[agent_id]
            agent_data.update(updates)
            # 更新时间戳
            agent_data['updated_at'] = datetime.utcnow().isoformat()
            agents[agent_id] = agent_data
            self._save_json(self.agents_file, agents)
            return True
        return False

    def delete_agent(self, agent_id: str) -> bool:
        """
        删除代理
        
        Args:
            agent_id: 代理ID
            
        Returns:
            是否删除成功
        """
        agents = self._load_json(self.agents_file)
        if agent_id in agents:
            del agents[agent_id]
            self._save_json(self.agents_file, agents)
            return True
        return False