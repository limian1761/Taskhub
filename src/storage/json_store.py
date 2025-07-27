import json
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from src.models.task import Task
from src.models.agent import Agent


class JsonStore:
    """基于JSON文件的存储实现，用于活跃任务和代理数据"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
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
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        """保存JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    # Task相关操作
    def save_task(self, task: Task) -> bool:
        """保存任务"""
        tasks = self._load_json(self.tasks_file)
        tasks[task.id] = task.model_dump()
        self._save_json(self.tasks_file, tasks)
        return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        tasks = self._load_json(self.tasks_file)
        if task_id in tasks:
            return Task(**tasks[task_id])
        return None

    def list_tasks(self, status: Optional[str] = None, 
                   capability: Optional[str] = None) -> List[Task]:
        """列出任务"""
        tasks = self._load_json(self.tasks_file)
        task_list = [Task(**task_data) for task_data in tasks.values()]
        
        if status:
            task_list = [t for t in task_list if t.status == status]
        if capability:
            task_list = [t for t in task_list if t.capability == capability]
        
        return task_list

    def update_task(self, task_id: str, **updates) -> bool:
        """更新任务"""
        tasks = self._load_json(self.tasks_file)
        if task_id not in tasks:
            return False
        
        task_data = tasks[task_id]
        task_data.update(updates)
        task_data['updated_at'] = datetime.utcnow().isoformat()
        self._save_json(self.tasks_file, tasks)
        return True

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        tasks = self._load_json(self.tasks_file)
        if task_id in tasks:
            del tasks[task_id]
            self._save_json(self.tasks_file, tasks)
            return True
        return False

    # Agent相关操作
    def save_agent(self, agent: Agent) -> bool:
        """保存代理"""
        agents = self._load_json(self.agents_file)
        agents[agent.id] = agent.model_dump()
        self._save_json(self.agents_file, agents)
        return True

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取代理"""
        agents = self._load_json(self.agents_file)
        if agent_id in agents:
            return Agent(**agents[agent_id])
        return None

    def list_agents(self, capability: Optional[str] = None) -> List[Agent]:
        """列出代理"""
        agents = self._load_json(self.agents_file)
        agent_list = [Agent(**agent_data) for agent_data in agents.values()]
        
        if capability:
            agent_list = [a for a in agent_list if capability in a.capabilities]
        
        return agent_list

    def update_agent(self, agent_id: str, **updates) -> bool:
        """更新代理"""
        agents = self._load_json(self.agents_file)
        if agent_id not in agents:
            return False
        
        agent_data = agents[agent_id]
        agent_data.update(updates)
        agent_data['updated_at'] = datetime.utcnow().isoformat()
        self._save_json(self.agents_file, agents)
        return True
    
    def get_all_task_ids(self) -> List[str]:
        """获取所有任务ID"""
        tasks = self._load_json(self.tasks_file)
        return list(tasks.keys())
    
    def get_all_agent_ids(self) -> List[str]:
        """获取所有代理ID"""
        agents = self._load_json(self.agents_file)
        return list(agents.keys())