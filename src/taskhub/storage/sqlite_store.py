"""
SQLite存储实现

该模块提供了基于SQLite的任务、代理和报告的持久化存储功能。
"""
import sqlite3
import json
import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import os

from ..models.task import Task
from ..models.agent import Agent
from ..models.report import Report
from ..utils.config import config


class SQLiteStore:
    """统一的SQLite存储实现，管理任务、代理和报告"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化SQLite存储
        
        Args:
            data_dir: 数据存储目录路径，如果为None则从全局配置中获取
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # 从全局配置中获取数据目录
            self.data_dir = Path(config.get("storage.data_dir"))
        
        self.data_dir.mkdir(exist_ok=True)
        
        self.tasks_db = self.data_dir / "tasks.db"
        self.reports_db = self.data_dir / "reports.db"
        
        # 初始化数据库表
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据库表"""
        # 初始化任务表
        with sqlite3.connect(self.tasks_db) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    details TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    assignee TEXT,
                    lease_id TEXT,
                    lease_expires_at TEXT,
                    depends_on TEXT,
                    parent_task_id TEXT,
                    created_by TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    evaluation TEXT,
                    is_archived INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
        
        # 初始化代理表
        with sqlite3.connect(self.tasks_db) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    capabilities TEXT NOT NULL,
                    capability_levels TEXT NOT NULL,
                    reputation INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    current_tasks TEXT,
                    completed_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            conn.commit()
            
        # 初始化报告表
        with sqlite3.connect(self.reports_db) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    result TEXT,
                    evaluation TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            conn.commit()

    # --- 任务相关操作 ---
    
    def save_task(self, task: Task) -> bool:
        """
        保存任务
        
        Args:
            task: 任务对象
            
        Returns:
            是否保存成功
        """
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                # 序列化复杂字段
                depends_on_json = json.dumps(task.depends_on)
                evaluation_json = json.dumps(task.evaluation.model_dump() if task.evaluation else None)
                
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO tasks 
                    (id, name, details, capability, status, assignee, lease_id, lease_expires_at,
                     depends_on, parent_task_id, created_by, created_at, updated_at, evaluation, is_archived)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.id, task.name, task.details, task.capability, task.status,
                    task.assignee, task.lease_id, 
                    task.lease_expires_at.isoformat() if task.lease_expires_at else None,
                    depends_on_json, task.parent_task_id, task.created_by,
                    task.created_at.isoformat(), task.updated_at.isoformat(),
                    evaluation_json, task.is_archived
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"保存任务失败: {e}")
            return False

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                cursor = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
                row = cursor.fetchone()
                if row:
                    # 反序列化复杂字段
                    data = dict(zip([column[0] for column in cursor.description], row))
                    data['depends_on'] = json.loads(data['depends_on']) if data['depends_on'] else []
                    
                    # 处理时间字段
                    if data['created_at']:
                        data['created_at'] = datetime.fromisoformat(data['created_at'])
                    if data['updated_at']:
                        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    if data['lease_expires_at']:
                        data['lease_expires_at'] = datetime.fromisoformat(data['lease_expires_at'])
                    
                    # 处理评价信息
                    if data['evaluation']:
                        eval_data = json.loads(data['evaluation'])
                        if eval_data:
                            from ..models.task import TaskEvaluation
                            data['evaluation'] = TaskEvaluation(**eval_data)
                        else:
                            data['evaluation'] = None
                    else:
                        data['evaluation'] = None
                    
                    return Task(**data)
            return None
        except Exception as e:
            print(f"获取任务失败: {e}")
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
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                query = "SELECT * FROM tasks WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                    
                if capability:
                    query += " AND capability = ?"
                    params.append(capability)
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                tasks = []
                for row in rows:
                    data = dict(zip([column[0] for column in cursor.description], row))
                    # 反序列化复杂字段
                    data['depends_on'] = json.loads(data['depends_on']) if data['depends_on'] else []
                    
                    # 处理时间字段
                    if data['created_at']:
                        data['created_at'] = datetime.fromisoformat(data['created_at'])
                    if data['updated_at']:
                        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    if data['lease_expires_at']:
                        data['lease_expires_at'] = datetime.fromisoformat(data['lease_expires_at'])
                    
                    # 处理评价信息
                    if data['evaluation']:
                        eval_data = json.loads(data['evaluation'])
                        if eval_data:
                            from ..models.task import TaskEvaluation
                            data['evaluation'] = TaskEvaluation(**eval_data)
                        else:
                            data['evaluation'] = None
                    else:
                        data['evaluation'] = None
                    
                    tasks.append(Task(**data))
                
                return tasks
        except Exception as e:
            print(f"列出任务失败: {e}")
            return []

    def update_task(self, task_id: str, **updates) -> bool:
        """
        更新任务
        
        Args:
            task_id: 任务ID
            **updates: 要更新的字段
            
        Returns:
            是否更新成功
        """
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                from datetime import datetime, timezone
                updates['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                # 处理特殊字段的序列化
                if 'depends_on' in updates and isinstance(updates['depends_on'], list):
                    updates['depends_on'] = json.dumps(updates['depends_on'])
                
                if 'evaluation' in updates and hasattr(updates['evaluation'], 'model_dump'):
                    updates['evaluation'] = json.dumps(updates['evaluation'].model_dump())
                elif 'evaluation' in updates and isinstance(updates['evaluation'], dict):
                    updates['evaluation'] = json.dumps(updates['evaluation'])
                
                if 'lease_expires_at' in updates and hasattr(updates['lease_expires_at', 'isoformat']):
                    updates['lease_expires_at'] = updates['lease_expires_at'].isoformat()
                
                set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
                values = list(updates.values())
                values.append(task_id)
                
                cursor = conn.execute(
                    f'UPDATE tasks SET {set_clause} WHERE id = ?',
                    values
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新任务失败: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                cursor = conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除任务失败: {e}")
            return False

    # --- 代理相关操作 ---
    
    def save_agent(self, agent: Agent) -> bool:
        """
        保存代理
        
        Args:
            agent: 代理对象
            
        Returns:
            是否保存成功
        """
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                # 序列化复杂字段
                capabilities_json = json.dumps(agent.capabilities)
                capability_levels_json = json.dumps(agent.capability_levels)
                current_tasks_json = json.dumps(agent.current_tasks)
                
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO agents 
                    (id, name, capabilities, capability_levels, reputation, status,
                     current_tasks, completed_tasks, failed_tasks, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent.id, agent.name, capabilities_json, capability_levels_json,
                    agent.reputation, agent.status, current_tasks_json,
                    agent.completed_tasks, agent.failed_tasks,
                    agent.created_at.isoformat(), agent.updated_at.isoformat()
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"保存代理失败: {e}")
            return False

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        获取代理
        
        Args:
            agent_id: 代理ID
            
        Returns:
            代理对象，如果不存在则返回None
        """
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                cursor = conn.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
                row = cursor.fetchone()
                if row:
                    data = dict(zip([column[0] for column in cursor.description], row))
                    # 反序列化复杂字段
                    data['capabilities'] = json.loads(data['capabilities'])
                    data['capability_levels'] = json.loads(data['capability_levels'])
                    data['current_tasks'] = json.loads(data['current_tasks']) if data['current_tasks'] else []
                    
                    # 处理时间字段
                    if data['created_at']:
                        data['created_at'] = datetime.fromisoformat(data['created_at'])
                    if data['updated_at']:
                        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    
                    return Agent(**data)
            return None
        except Exception as e:
            print(f"获取代理失败: {e}")
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
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                from datetime import datetime, timezone
                updates['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                # 处理特殊字段的序列化
                if 'capabilities' in updates and isinstance(updates['capabilities'], list):
                    updates['capabilities'] = json.dumps(updates['capabilities'])
                
                if 'capability_levels' in updates and isinstance(updates['capability_levels'], dict):
                    updates['capability_levels'] = json.dumps(updates['capability_levels'])
                
                if 'current_tasks' in updates and isinstance(updates['current_tasks'], list):
                    updates['current_tasks'] = json.dumps(updates['current_tasks'])
                
                set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
                values = list(updates.values())
                values.append(agent_id)
                
                cursor = conn.execute(
                    f'UPDATE agents SET {set_clause} WHERE id = ?',
                    values
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新代理失败: {e}")
            return False

    # --- 报告相关操作 ---
    
    def save_report(self, report: Report) -> bool:
        """
        保存报告
        
        Args:
            report: 报告对象
            
        Returns:
            是否保存成功
        """
        try:
            with sqlite3.connect(self.reports_db) as conn:
                # 序列化复杂字段
                evaluation_json = json.dumps(report.evaluation.model_dump() if report.evaluation else None)
                
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO reports 
                    (id, task_id, agent_id, status, details, result, evaluation, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report.id, report.task_id, report.agent_id, report.status,
                    report.details, report.result, evaluation_json,
                    report.created_at, report.updated_at
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"保存报告失败: {e}")
            return False

    def get_report(self, report_id: str) -> Optional[Report]:
        """
        获取报告
        
        Args:
            report_id: 报告ID
            
        Returns:
            报告对象，如果不存在则返回None
        """
        try:
            with sqlite3.connect(self.reports_db) as conn:
                cursor = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
                row = cursor.fetchone()
                if row:
                    data = dict(zip([column[0] for column in cursor.description], row))
                    # 处理评价信息
                    if data['evaluation']:
                        eval_data = json.loads(data['evaluation'])
                        if eval_data:
                            from ..models.report import ReportEvaluation
                            data['evaluation'] = ReportEvaluation(**eval_data)
                        else:
                            data['evaluation'] = None
                    else:
                        data['evaluation'] = None
                    
                    # 处理时间字段
                    if data['created_at']:
                        data['created_at'] = datetime.fromisoformat(data['created_at'])
                    if data['updated_at']:
                        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    
                    return Report(**data)
            return None
        except Exception as e:
            print(f"获取报告失败: {e}")
            return None

    def list_reports(self, **kwargs) -> List[Report]:
        """
        获取报告列表，支持按任务ID、代理ID和状态筛选
        
        Args:
            **kwargs: 筛选参数
                - task_id: 任务ID
                - agent_id: 代理ID
                - status: 报告状态
                - limit: 返回结果数量限制
                
        Returns:
            报告列表
        """
        # 解析参数
        task_id = kwargs.get('task_id')
        agent_id = kwargs.get('agent_id')
        status = kwargs.get('status')
        limit = kwargs.get('limit', 100)
        
        query = "SELECT * FROM reports WHERE 1=1"
        params = []
        
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
            
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
            
        if status:
            query += " AND status = ?"
            params.append(status)
            
        query += " ORDER BY created_at DESC"
        query += f" LIMIT {limit}"
        
        try:
            with sqlite3.connect(self.reports_db) as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                reports = []
                for row in rows:
                    data = dict(zip([column[0] for column in cursor.description], row))
                    # 处理评价信息
                    if data['evaluation']:
                        eval_data = json.loads(data['evaluation'])
                        if eval_data:
                            from ..models.report import ReportEvaluation
                            data['evaluation'] = ReportEvaluation(**eval_data)
                        else:
                            data['evaluation'] = None
                    else:
                        data['evaluation'] = None
                    
                    # 处理时间字段
                    if data['created_at']:
                        data['created_at'] = datetime.fromisoformat(data['created_at'])
                    if data['updated_at']:
                        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    
                    reports.append(Report(**data))
                return reports
        except Exception as e:
            print(f"获取报告列表失败: {e}")
            return []

    def update_report(self, report_id: str, **updates) -> bool:
        """
        更新报告
        
        Args:
            report_id: 报告ID
            **updates: 要更新的字段
            
        Returns:
            是否更新成功
        """
        try:
            with sqlite3.connect(self.reports_db) as conn:
                from datetime import datetime, timezone
                updates['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                # 处理evaluation的JSON序列化
                if 'evaluation' in updates and hasattr(updates['evaluation'], 'model_dump'):
                    updates['evaluation'] = json.dumps(updates['evaluation'].model_dump())
                elif 'evaluation' in updates and isinstance(updates['evaluation'], dict):
                    updates['evaluation'] = json.dumps(updates['evaluation'])
                
                set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
                values = list(updates.values())
                values.append(report_id)
                
                cursor = conn.execute(
                    f'UPDATE reports SET {set_clause} WHERE id = ?',
                    values
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新报告失败: {e}")
            return False

    def delete_report(self, report_id: str) -> bool:
        """
        删除报告
        
        Args:
            report_id: 报告ID
            
        Returns:
            是否删除成功
        """
        try:
            with sqlite3.connect(self.reports_db) as conn:
                cursor = conn.execute('DELETE FROM reports WHERE id = ?', (report_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除报告失败: {e}")
            return False