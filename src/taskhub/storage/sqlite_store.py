"""
SQLite存储实现
"""
import sqlite3
import json
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from ..models.task import Task, TaskEvaluation
from ..models.agent import Agent
from ..models.report import Report, ReportEvaluation
from ..models.domain import Domain
from ..models.knowledge import KnowledgeItem
from ..utils.config import config

class SQLiteStore:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or config.get("database.path", "data/taskhub.db"))
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = None

    async def connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    async def close(self):
        if self.conn:
            self.conn.close()
    
    def _init_tables(self):
        with self.conn:
            self.conn.execute('CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, name TEXT, details TEXT, capability TEXT, status TEXT, assignee TEXT, lease_id TEXT, lease_expires_at TEXT, depends_on TEXT, parent_task_id TEXT, created_by TEXT, created_at TEXT, updated_at TEXT, evaluation TEXT, is_archived INTEGER)')
            self.conn.execute('CREATE TABLE IF NOT EXISTS agents (id TEXT PRIMARY KEY, name TEXT, capabilities TEXT, domain_scores TEXT, status TEXT, current_tasks TEXT, completed_tasks INTEGER, failed_tasks INTEGER, created_at TEXT, updated_at TEXT)')
            self.conn.execute('CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, task_id TEXT, agent_id TEXT, status TEXT, details TEXT, result TEXT, evaluation TEXT, created_at TEXT, updated_at TEXT)')
            self.conn.execute('CREATE TABLE IF NOT EXISTS domains (id TEXT PRIMARY KEY, name TEXT UNIQUE, description TEXT, created_at TEXT)')
            self.conn.execute('CREATE TABLE IF NOT EXISTS knowledge_items (id TEXT PRIMARY KEY, title TEXT, content TEXT, source TEXT, domain_tags TEXT, created_by TEXT, created_at TEXT)')

    # Agent Methods
    def save_agent(self, agent: Agent):
        with self.conn:
            self.conn.execute('INSERT OR REPLACE INTO agents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                              (agent.id, agent.name, json.dumps(agent.capabilities), json.dumps(agent.domain_scores), agent.status, json.dumps(agent.current_tasks), agent.completed_tasks, agent.failed_tasks, agent.created_at.isoformat(), agent.updated_at.isoformat()))

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        cursor = self.conn.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data['capabilities'] = json.loads(data['capabilities'])
            data['domain_scores'] = json.loads(data['domain_scores'])
            data['current_tasks'] = json.loads(data['current_tasks'])
            data['created_at'] = datetime.fromisoformat(data['created_at'])
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            return Agent(**data)
        return None
        
    def update_agent(self, agent_id: str, **updates):
        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list(updates.values())
        values.append(agent_id)
        with self.conn:
            self.conn.execute(f'UPDATE agents SET {set_clause} WHERE id = ?', values)

    # Domain Methods
    def save_domain(self, domain: Domain):
        with self.conn:
            self.conn.execute('INSERT OR REPLACE INTO domains VALUES (?, ?, ?, ?)',
                              (domain.id, domain.name, domain.description, domain.created_at.isoformat()))

    def get_domain(self, domain_id: str) -> Optional[Domain]:
        cursor = self.conn.execute('SELECT * FROM domains WHERE id = ?', (domain_id,))
        row = cursor.fetchone()
        return Domain(**dict(row)) if row else None

    def list_domains(self) -> List[Domain]:
        cursor = self.conn.execute('SELECT * FROM domains')
        return [Domain(**dict(row)) for row in cursor.fetchall()]

    # KnowledgeItem Methods
    def save_knowledge_item(self, item: KnowledgeItem):
        with self.conn:
            self.conn.execute('INSERT OR REPLACE INTO knowledge_items VALUES (?, ?, ?, ?, ?, ?, ?)',
                              (item.id, item.title, item.content, item.source, json.dumps(item.domain_tags), item.created_by, item.created_at.isoformat()))

    def get_knowledge_item(self, item_id: str) -> Optional[KnowledgeItem]:
        cursor = self.conn.execute('SELECT * FROM knowledge_items WHERE id = ?', (item_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data['domain_tags'] = json.loads(data['domain_tags'])
            return KnowledgeItem(**data)
        return None

    def list_knowledge_items(self, domain_tag: Optional[str] = None) -> List[KnowledgeItem]:
        query = 'SELECT * FROM knowledge_items'
        params = []
        if domain_tag:
            query += " WHERE json_search(domain_tags, 'one', ?) IS NOT NULL"
            params.append(domain_tag)
        cursor = self.conn.execute(query, params)
        return [KnowledgeItem(**dict(row)) for row in cursor.fetchall()]

    # Task Methods
    def save_task(self, task: Task):
        with self.conn:
            self.conn.execute('INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                              (task.id, task.name, task.details, task.capability, task.status, task.assignee, task.lease_id, task.lease_expires_at.isoformat() if task.lease_expires_at else None, json.dumps(task.depends_on), task.parent_task_id, task.created_by, task.created_at.isoformat(), task.updated_at.isoformat(), json.dumps(task.evaluation.model_dump()) if task.evaluation else None, task.is_archived))

    def get_task(self, task_id: str) -> Optional[Task]:
        cursor = self.conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data['depends_on'] = json.loads(data['depends_on'])
            data['evaluation'] = TaskEvaluation(**json.loads(data['evaluation'])) if data['evaluation'] else None
            data['created_at'] = datetime.fromisoformat(data['created_at'])
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            data['lease_expires_at'] = datetime.fromisoformat(data['lease_expires_at']) if data['lease_expires_at'] else None
            return Task(**data)
        return None

    def list_tasks(self, status: Optional[str] = None, capability: Optional[str] = None) -> List[Task]:
        query = 'SELECT * FROM tasks WHERE 1=1'
        params = []
        if status:
            query += ' AND status = ?'
            params.append(status)
        if capability:
            query += ' AND capability = ?'
            params.append(capability)
        cursor = self.conn.execute(query, params)
        return [self.get_task(row['id']) for row in cursor.fetchall()]

    def update_task(self, task_id: str, **updates):
        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list(updates.values())
        values.append(task_id)
        with self.conn:
            self.conn.execute(f'UPDATE tasks SET {set_clause} WHERE id = ?', values)

    def delete_task(self, task_id: str):
        with self.conn:
            self.conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

    # Report Methods
    def save_report(self, report: Report):
        with self.conn:
            self.conn.execute('INSERT OR REPLACE INTO reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                              (report.id, report.task_id, report.agent_id, report.status, report.details, report.result, json.dumps(report.evaluation.model_dump()) if report.evaluation else None, report.created_at, report.updated_at))

    def get_report(self, report_id: str) -> Optional[Report]:
        cursor = self.conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data['evaluation'] = ReportEvaluation(**json.loads(data['evaluation'])) if data['evaluation'] else None
            return Report(**data)
        return None

    def list_reports(self, task_id: Optional[str] = None, agent_id: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> List[Report]:
        query = 'SELECT * FROM reports WHERE 1=1'
        params = []
        if task_id:
            query += ' AND task_id = ?'
            params.append(task_id)
        if agent_id:
            query += ' AND agent_id = ?'
            params.append(agent_id)
        if status:
            query += ' AND status = ?'
            params.append(status)
        query += ' LIMIT ?'
        params.append(limit)
        cursor = self.conn.execute(query, params)
        return [self.get_report(row['id']) for row in cursor.fetchall()]

    def update_report(self, report_id: str, **updates):
        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list(updates.values())
        values.append(report_id)
        with self.conn:
            self.conn.execute(f'UPDATE reports SET {set_clause} WHERE id = ?', values)

    def delete_report(self, report_id: str):
        with self.conn:
            self.conn.execute('DELETE FROM reports WHERE id = ?', (report_id,))
