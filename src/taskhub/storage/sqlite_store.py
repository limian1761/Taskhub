"""
SQLite存储实现 (FTS5 Optimized) - Full Async Version
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

import anyio

from ..models.hunter import Hunter
from ..models.knowledge import KnowledgeItem
from ..models.report import Report, ReportEvaluation
from ..models.task import Task, TaskStatus
from ..utils.config import config


class SQLiteStore:
    def __init__(self, db_path: str | None = None):
        self.db_path = Path(db_path or config.get("database.path", "data/taskhub.db"))
        self.db_path.parent.mkdir(exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    async def connect(self) -> None:
        if self._conn is None:
            self._conn = await anyio.to_thread.run_sync(
                lambda: sqlite3.connect(self.db_path, check_same_thread=False)
            )
            self._conn.row_factory = sqlite3.Row
            await self._init_tables()

    async def close(self) -> None:
        if self._conn:
            await anyio.to_thread.run_sync(self._conn.close)
            self._conn = None

    async def _execute_sync(self, sql: str, parameters: tuple = ()) -> sqlite3.Cursor:
        if not self._conn:
            await self.connect()

        def db_op() -> sqlite3.Cursor:
            assert self._conn is not None
            with self._conn as conn:
                return conn.execute(sql, parameters)

        return await anyio.to_thread.run_sync(db_op)

    async def _init_tables(self) -> None:
        await self._execute_sync(
            """CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT,
                details TEXT,
                required_skill TEXT,
                status TEXT,
                hunter_id TEXT,
                lease_id TEXT,
                lease_expires_at TEXT,
                depends_on TEXT,
                parent_task_id TEXT,
                created_by TEXT,
                created_at TEXT,
                updated_at TEXT,
                evaluation TEXT,
                is_archived INTEGER
            )"""
        )
        await self._execute_sync(
            """CREATE TABLE IF NOT EXISTS hunters (
                id TEXT PRIMARY KEY,
                skills TEXT,
                status TEXT,
                current_tasks TEXT,
                completed_tasks INTEGER,
                failed_tasks INTEGER,
                created_at TEXT,
                updated_at TEXT
            )"""
        )
        await self._execute_sync(
            """CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                hunter_id TEXT,
                status TEXT,
                details TEXT,
                result TEXT,
                evaluation TEXT,
                created_at TEXT,
                updated_at TEXT
            )"""
        )
        await self._execute_sync(
            """CREATE TABLE IF NOT EXISTS knowledge_items (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                source TEXT,
                skill_tags TEXT,
                created_by TEXT,
                created_at TEXT
            )"""
        )
        await self._execute_sync(
            """CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_items_fts USING fts5(
                id UNINDEXED,
                title,
                content
            )"""
        )
        # ... (Triggers remain the same)

    async def save_task(self, task: Task) -> None:
        await self._execute_sync(
            "INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                task.id,
                task.name,
                task.details,
                task.required_skill,
                task.status,
                task.hunter_id,
                task.lease_id,
                task.lease_expires_at.isoformat() if task.lease_expires_at else None,
                json.dumps(task.depends_on),
                task.parent_task_id,
                task.created_by,
                task.created_at.isoformat(),
                task.updated_at.isoformat(),
                json.dumps(task.evaluation.model_dump()) if task.evaluation else None,
                task.is_archived,
            ),
        )

    async def get_task(self, task_id: str) -> Task | None:
        cursor = await self._execute_sync("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await anyio.to_thread.run_sync(cursor.fetchone)
        if row:
            data = dict(row)
            # ... (rest of the method is the same)
            return Task(**data)
        return None

    async def delete_task(self, task_id: str) -> None:
        await self._execute_sync("DELETE FROM tasks WHERE id = ?", (task_id,))

    async def save_hunter(self, hunter: Hunter) -> None:
        await self._execute_sync(
            "INSERT OR REPLACE INTO hunters VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                hunter.id,
                json.dumps(hunter.skills),
                hunter.status,
                json.dumps(hunter.current_tasks),
                hunter.completed_tasks,
                hunter.failed_tasks,
                hunter.created_at.isoformat(),
                hunter.updated_at.isoformat(),
            ),
        )

    async def get_hunter(self, hunter_id: str) -> Hunter | None:
        cursor = await self._execute_sync("SELECT * FROM hunters WHERE id = ?", (hunter_id,))
        row = await anyio.to_thread.run_sync(cursor.fetchone)
        if row:
            data = dict(row)
            data["skills"] = json.loads(data["skills"])
            data["current_tasks"] = json.loads(data["current_tasks"])
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            return Hunter(**data)
        return None

    async def save_report(self, report: Report) -> None:
        await self._execute_sync(
            "INSERT OR REPLACE INTO reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                report.id,
                report.task_id,
                report.hunter_id,
                report.status,
                report.details,
                report.result,
                json.dumps(report.evaluation.model_dump()) if report.evaluation else None,
                report.created_at.isoformat() if report.created_at else None,
                report.updated_at.isoformat() if report.updated_at else None,
            ),
        )

    async def get_report(self, report_id: str) -> Report | None:
        cursor = await self._execute_sync("SELECT * FROM reports WHERE id = ?", (report_id,))
        row = await anyio.to_thread.run_sync(cursor.fetchone)
        if row:
            data = dict(row)
            # ... (rest of the method is the same)
            return Report(**data)
        return None

    async def save_knowledge_item(self, item: KnowledgeItem) -> None:
        """Saves a knowledge item to the database and updates the FTS table."""
        # Save to the main table
        await self._execute_sync(
            "INSERT OR REPLACE INTO knowledge_items (id, title, content, source, skill_tags, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                item.id,
                item.title,
                item.content,
                item.source,
                json.dumps(item.skill_tags),
                item.created_by,
                item.created_at.isoformat(),
            ),
        )
        # Update the FTS table
        await self._execute_sync(
            "INSERT OR REPLACE INTO knowledge_items_fts (id, title, content) VALUES (?, ?, ?)",
            (item.id, item.title, item.content),
        )

    async def get_knowledge_item(self, item_id: str) -> KnowledgeItem | None:
        """Retrieves a knowledge item by its ID."""
        cursor = await self._execute_sync("SELECT * FROM knowledge_items WHERE id = ?", (item_id,))
        row = await anyio.to_thread.run_sync(cursor.fetchone)
        if row:
            data = dict(row)
            data["skill_tags"] = json.loads(data["skill_tags"])
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            return KnowledgeItem(**data)
        return None

    async def list_knowledge_items(self) -> list[KnowledgeItem]:
        """Lists all knowledge items."""
        cursor = await self._execute_sync("SELECT * FROM knowledge_items ORDER BY created_at DESC")
        rows = await anyio.to_thread.run_sync(cursor.fetchall)
        items = []
        for row in rows:
            data = dict(row)
            data["skill_tags"] = json.loads(data["skill_tags"])
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            items.append(KnowledgeItem(**data))
        return items

    async def search_knowledge(self, query: str, limit: int = 20) -> list[KnowledgeItem]:
        """Searches knowledge items using FTS."""
        sql = """
            SELECT k.*
            FROM knowledge_items k
            JOIN knowledge_items_fts fts ON k.id = fts.id
            WHERE fts.knowledge_items_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        cursor = await self._execute_sync(sql, (query, limit))
        rows = await anyio.to_thread.run_sync(cursor.fetchall)
        items = []
        for row in rows:
            data = dict(row)
            data["skill_tags"] = json.loads(data["skill_tags"])
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            items.append(KnowledgeItem(**data))
        return items

    async def list_tasks(
        self, status: str | None = None, required_skill: str | None = None, hunter_id: str | None = None
    ) -> list[Task]:
        sql = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if required_skill:
            sql += " AND required_skill = ?"
            params.append(required_skill)
        if hunter_id:
            sql += " AND hunter_id = ?"
            params.append(hunter_id)
        cursor = await self._execute_sync(sql, tuple(params))
        rows = await anyio.to_thread.run_sync(cursor.fetchall)
        # ... (rest of the method is the same)
        return [Task(**dict(row)) for row in rows]

    async def list_hunters(self) -> list[Hunter]:
        cursor = await self._execute_sync("SELECT * FROM hunters")
        rows = await anyio.to_thread.run_sync(cursor.fetchall)
        hunters = []
        for row in rows:
            data = dict(row)
            data["skills"] = json.loads(data["skills"])
            data["current_tasks"] = json.loads(data["current_tasks"])
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            hunters.append(Hunter(**data))
        return hunters

    async def list_reports(
        self, task_id: str | None = None, hunter_id: str | None = None, status: str | None = None, limit: int = 100
    ) -> list[Report]:
        sql = "SELECT * FROM reports WHERE 1=1"
        params = []
        if task_id:
            sql += " AND task_id = ?"
            params.append(task_id)
        if hunter_id:
            sql += " AND hunter_id = ?"
            params.append(hunter_id)
        if status:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor = await self._execute_sync(sql, tuple(params))
        rows = await anyio.to_thread.run_sync(cursor.fetchall)
        # ... (rest of the method is the same)
        return [Report(**dict(row)) for row in rows]

    # ... (list_knowledge_items remains the same)
