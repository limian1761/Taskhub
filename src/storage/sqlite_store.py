import sqlite3
import json
import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from src.models.task import Task
from src.models.agent import Agent
from src.models.report import Report


class SQLiteStore:
    """统一的SQLite存储实现，管理任务、代理和报告"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.tasks_db = self.data_dir / "tasks.db"
        self.reports_db = self.data_dir / "reports.db"
        
        self._init_databases()
    
    def _init_databases(self):
        """初始化所有数据库"""
        self._init_tasks_db()
        self._init_reports_db()
        self._init_agents_db()
    
    def _init_tasks_db(self):
        """初始化任务数据库"""
        with sqlite3.connect(self.tasks_db) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    details TEXT,
                    capability TEXT,
                    created_by TEXT,
                    assignee TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    updated_at TEXT,
                    lease_expires_at TEXT,
                    lease_id TEXT,
                    evaluation TEXT,
                    is_archived INTEGER DEFAULT 0,
                    dependencies TEXT
                )
            ''')
            conn.commit()
    
    def _init_reports_db(self):
        """初始化报告数据库"""
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
    
    def _init_agents_db(self):
        """初始化代理数据库"""
        with sqlite3.connect(self.tasks_db) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    capabilities TEXT,
                    capability_levels TEXT,
                    reputation INTEGER DEFAULT 100,
                    current_tasks TEXT,
                    completed_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            conn.commit()
    
    # Task相关操作
    def save_task(self, task: Task) -> bool:
        """保存任务"""
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO tasks 
                    (id, name, details, capability, created_by, assignee, status, 
                     created_at, updated_at, lease_expires_at, lease_id, evaluation, is_archived, dependencies)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(task.id), task.name, task.details, task.capability, 
                    task.created_by, task.assignee, task.status,
                    task.created_at.isoformat(), task.updated_at.isoformat(), 
                    task.lease_expires_at.isoformat() if task.lease_expires_at else None,
                    task.lease_id,
                    json.dumps(task.evaluation.model_dump() if task.evaluation else None),
                    1 if task.is_archived else 0,
                    json.dumps(task.depends_on) if task.depends_on else None
                ))
                conn.commit()
                print(f"任务保存成功: {task.id}")
                return True
        except Exception as e:
            print(f"保存任务失败: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        with sqlite3.connect(self.tasks_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                if data['evaluation']:
                    try:
                        eval_data = json.loads(data['evaluation'])
                        if eval_data:
                            data['evaluation'] = eval_data
                        else:
                            data['evaluation'] = None
                    except:
                        data['evaluation'] = None
                if data['dependencies']:
                    data['depends_on'] = json.loads(data['dependencies'])
                else:
                    data['depends_on'] = []
                data['is_archived'] = bool(data['is_archived'])
                
                # 处理datetime字段
                from datetime import datetime
                if data['created_at']:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if data['updated_at']:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                if data['lease_expires_at']:
                    data['lease_expires_at'] = datetime.fromisoformat(data['lease_expires_at'])
                
                return Task(**data)
            return None
    
    def list_tasks(self, status: Optional[str] = None, 
                   capability: Optional[str] = None) -> List[Task]:
        """列出任务"""
        with sqlite3.connect(self.tasks_db) as conn:
            conn.row_factory = sqlite3.Row
            query = 'SELECT * FROM tasks WHERE 1=1'
            params = []
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            if capability:
                query += ' AND capability = ?'
                params.append(capability)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            tasks = []
            for row in rows:
                data = dict(row)
                if data['evaluation']:
                    try:
                        eval_data = json.loads(data['evaluation'])
                        if eval_data:
                            data['evaluation'] = eval_data
                        else:
                            data['evaluation'] = None
                    except:
                        data['evaluation'] = None
                if data['dependencies']:
                    data['depends_on'] = json.loads(data['dependencies'])
                else:
                    data['depends_on'] = []
                data['is_archived'] = bool(data['is_archived'])
                
                # 处理datetime字段
                from datetime import datetime
                if data['created_at']:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if data['updated_at']:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                if data['lease_expires_at']:
                    data['lease_expires_at'] = datetime.fromisoformat(data['lease_expires_at'])
                
                tasks.append(Task(**data))
            
            return tasks
    
    def update_task(self, task_id: str, **updates) -> bool:
        """更新任务"""
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                # 自动添加更新时间
                from datetime import datetime, timezone
                updates['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                # 构建更新语句
                set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
                values = list(updates.values())
                values.append(str(task_id))
                
                cursor = conn.execute(
                    f'UPDATE tasks SET {set_clause} WHERE id = ?',
                    values
                )
                conn.commit()
                print(f"任务更新成功: {task_id}, 影响行数: {cursor.rowcount}")
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新任务失败: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                cursor = conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除任务失败: {e}")
            return False
    
    def get_all_task_ids(self) -> List[str]:
        """获取所有任务ID"""
        with sqlite3.connect(self.tasks_db) as conn:
            cursor = conn.execute('SELECT id FROM tasks')
            return [row[0] for row in cursor.fetchall()]
    
    # Agent相关操作
    def save_agent(self, agent: Agent) -> bool:
        """保存代理"""
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO agents 
                    (id, name, capabilities, capability_levels, reputation, 
                     current_tasks, completed_tasks, failed_tasks, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent.id, agent.name, json.dumps(agent.capabilities),
                    json.dumps(agent.capability_levels), agent.reputation,
                    json.dumps(agent.current_tasks), agent.completed_tasks,
                    agent.failed_tasks, agent.created_at, agent.updated_at
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"保存代理失败: {e}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取代理"""
        with sqlite3.connect(self.tasks_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['capabilities'] = json.loads(data['capabilities'])
                data['capability_levels'] = json.loads(data['capability_levels'])
                data['current_tasks'] = json.loads(data['current_tasks'])
                return Agent(**data)
            return None
    
    def list_agents(self, capability: Optional[str] = None) -> List[Agent]:
        """列出代理"""
        with sqlite3.connect(self.tasks_db) as conn:
            conn.row_factory = sqlite3.Row
            query = 'SELECT * FROM agents WHERE 1=1'
            params = []
            
            if capability:
                query += ' AND capabilities LIKE ?'
                params.append(f'%{capability}%')
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            agents = []
            for row in rows:
                data = dict(row)
                data['capabilities'] = json.loads(data['capabilities'])
                data['capability_levels'] = json.loads(data['capability_levels'])
                data['current_tasks'] = json.loads(data['current_tasks'])
                agents.append(Agent(**data))
            
            return agents
    
    def update_agent(self, agent_id: str, **updates) -> bool:
        """更新代理"""
        try:
            with sqlite3.connect(self.tasks_db) as conn:
                from datetime import datetime, timezone
                updates['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                # 处理current_tasks的JSON序列化
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
                print(f"代理更新成功: {agent_id}, 影响行数: {cursor.rowcount}")
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新代理失败: {e}")
            return False
    
    def get_all_agent_ids(self) -> List[str]:
        """获取所有代理ID"""
        with sqlite3.connect(self.tasks_db) as conn:
            cursor = conn.execute('SELECT id FROM agents')
            return [row[0] for row in cursor.fetchall()]
    
    # Report相关操作
    def save_report(self, report: Report) -> bool:
        """保存报告"""
        try:
            with sqlite3.connect(self.reports_db) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO reports 
                    (id, task_id, agent_id, status, details, result, evaluation, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report.id, report.task_id, report.agent_id, report.status,
                    report.details, report.result, 
                    json.dumps(report.evaluation.model_dump() if report.evaluation else None),
                    report.created_at, report.updated_at
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"保存报告失败: {e}")
            return False
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """获取报告"""
        from src.models.report import ReportEvaluation
        with sqlite3.connect(self.reports_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                if data['evaluation']:
                    try:
                        eval_data = json.loads(data['evaluation'])
                        if eval_data:
                            data['evaluation'] = ReportEvaluation(**eval_data)
                        else:
                            data['evaluation'] = None
                    except:
                        data['evaluation'] = None
                else:
                    data['evaluation'] = None
                return Report(**data)
            return None
    
    def get_reports_by_task(self, task_id: str) -> List[Report]:
        """获取任务的所有报告"""
        from src.models.report import ReportEvaluation
        with sqlite3.connect(self.reports_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM reports WHERE task_id = ? ORDER BY created_at DESC',
                (task_id,)
            )
            rows = cursor.fetchall()
            reports = []
            for row in rows:
                data = dict(row)
                if data['evaluation']:
                    try:
                        eval_data = json.loads(data['evaluation'])
                        if eval_data:
                            data['evaluation'] = ReportEvaluation(**eval_data)
                        else:
                            data['evaluation'] = None
                    except:
                        data['evaluation'] = None
                else:
                    data['evaluation'] = None
                reports.append(Report(**data))
            return reports
    
    def get_reports_by_agent(self, agent_id: str) -> List[Report]:
        """获取代理的所有报告"""
        from src.models.report import ReportEvaluation
        with sqlite3.connect(self.reports_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM reports WHERE agent_id = ? ORDER BY created_at DESC',
                (agent_id,)
            )
            rows = cursor.fetchall()
            reports = []
            for row in rows:
                data = dict(row)
                if data['evaluation']:
                    try:
                        eval_data = json.loads(data['evaluation'])
                        if eval_data:
                            data['evaluation'] = ReportEvaluation(**eval_data)
                        else:
                            data['evaluation'] = None
                    except:
                        data['evaluation'] = None
                else:
                    data['evaluation'] = None
                reports.append(Report(**data))
            return reports
    
    def list_reports(self, status: Optional[str] = None) -> List[Report]:
        """列出所有报告"""
        from src.models.report import ReportEvaluation
        with sqlite3.connect(self.reports_db) as conn:
            conn.row_factory = sqlite3.Row
            query = 'SELECT * FROM reports WHERE 1=1'
            params = []
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            reports = []
            for row in rows:
                data = dict(row)
                if data['evaluation']:
                    try:
                        eval_data = json.loads(data['evaluation'])
                        if eval_data:
                            data['evaluation'] = ReportEvaluation(**eval_data)
                        else:
                            data['evaluation'] = None
                    except:
                        data['evaluation'] = None
                else:
                    data['evaluation'] = None
                reports.append(Report(**data))
            return reports
    
    def update_report(self, report_id: str, **updates) -> bool:
        """更新报告"""
        try:
            with sqlite3.connect(self.reports_db) as conn:
                from datetime import datetime, timezone
                updates['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                # 处理evaluation的JSON序列化
                if 'evaluation' in updates and isinstance(updates['evaluation'], dict):
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
        """删除报告"""
        try:
            with sqlite3.connect(self.reports_db) as conn:
                cursor = conn.execute('DELETE FROM reports WHERE id = ?', (report_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除报告失败: {e}")
            return False