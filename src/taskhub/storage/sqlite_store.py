"""
SQLite存储实现 (FTS5 Optimized) - Full Async Version
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
import threading
import time
from functools import wraps

import anyio

from ..models.hunter import Hunter
from ..models.discussion import DiscussionMessage
from ..models.report import Report, ReportEvaluation
from ..models.task import Task, TaskStatus
from ..config import get_config


class SQLiteStore:
    def __init__(self, db_path: str | None = None):
        config = get_config()
        self.db_path = Path(db_path or config.get("database.path", "data/taskhub.db"))
        self.db_path.parent.mkdir(exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._local = threading.local()
        self._pool_size = 10
        self._timeout = 30.0
        
        # Cache configuration
        self._cache = {}
        cache_config = config.get_cache_config()
        self._cache_ttl = cache_config["ttl"]
        self._max_cache_size = cache_config["max_size"]
        
    def _cache_key(self, prefix: str, *args) -> str:
        """Generate cache key from prefix and arguments."""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"
    
    def _get_from_cache(self, key: str) -> Any:
        """Get value from cache if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return value
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any) -> None:
        """Set value in cache with TTL."""
        if len(self._cache) >= self._max_cache_size:
            # Simple LRU: remove oldest entries
            oldest_keys = sorted(self._cache.keys(), 
                               key=lambda k: self._cache[k][1])[:self._max_cache_size//10]
            for k in oldest_keys:
                del self._cache[k]
        
        self._cache[key] = (value, time.time())
    
    def _invalidate_cache(self, prefix: str) -> None:
        """Invalidate all cache entries with given prefix."""
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            del self._cache[key]

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection or create new one."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self._timeout,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
            conn.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and performance
            conn.execute("PRAGMA cache_size=10000")  # Increase cache size
            conn.execute("PRAGMA temp_store=memory")  # Use memory for temp operations
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
            self._local.connection = conn
        return self._local.connection

    async def connect(self) -> None:
        """Initialize connection pool settings."""
        if self._conn is None:
            self._conn = self._get_connection()
            await self._init_tables()

    async def close(self) -> None:
        """Close all connections."""
        if hasattr(self._local, 'connection') and self._local.connection:
            await anyio.to_thread.run_sync(self._local.connection.close)
            self._local.connection = None
        if self._conn:
            await anyio.to_thread.run_sync(self._conn.close)
            self._conn = None

    async def _execute_sync(self, sql: str, parameters: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL with connection from pool."""
        def db_op() -> sqlite3.Cursor:
            conn = self._get_connection()
            with conn as c:
                return c.execute(sql, parameters)

        return await anyio.to_thread.run_sync(db_op)

    async def _init_tables(self) -> None:
        """Initialize database tables if they don't exist."""
        # Create tables if they don't exist (fallback when Alembic is not used)
        await self._execute_sync("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                details TEXT,
                required_skill TEXT,
                status TEXT NOT NULL,
                hunter_id TEXT,
                lease_id TEXT,
                lease_expires_at TEXT,
                depends_on TEXT,
                parent_task_id TEXT,
                published_by_hunter_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                evaluation TEXT,
                is_archived BOOLEAN DEFAULT 0
            )
        """)
        
        await self._execute_sync("""
            CREATE TABLE IF NOT EXISTS hunters (
                id TEXT PRIMARY KEY,
                skills TEXT NOT NULL,
                status TEXT NOT NULL,
                current_tasks TEXT NOT NULL,
                completed_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_read_discussion_timestamp TEXT
            )
        """)
        
        await self._execute_sync("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                hunter_id TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                result TEXT,
                evaluation TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        await self._execute_sync("""
            CREATE TABLE IF NOT EXISTS discussion_messages (
                id TEXT PRIMARY KEY,
                hunter_id TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Backward compatibility: add columns that might be missing
        try:
            await self._execute_sync("ALTER TABLE hunters ADD COLUMN last_read_discussion_timestamp TEXT")
        except sqlite3.OperationalError as e:
            # Ignore "duplicate column" errors
            if "duplicate column name" not in str(e).lower():
                raise

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
                task.published_by_hunter_id,
                task.created_at.isoformat(),
                task.updated_at.isoformat(),
                json.dumps(task.evaluation.model_dump()) if task.evaluation else None,
                task.is_archived,
            ),
        )
        # Invalidate task cache when saving
        self._invalidate_cache("task:")

    async def get_task(self, task_id: str) -> Task | None:
        # Check cache first
        cache_key = self._cache_key("task", task_id)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
            
        cursor = await self._execute_sync("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await anyio.to_thread.run_sync(cursor.fetchone)
        if row:
            data = dict(row)
            data["status"] = TaskStatus(data["status"])
            data["depends_on"] = json.loads(data["depends_on"]) if data["depends_on"] else []
            data["created_at"] = datetime.fromisoformat(data["created_at"]) if data["created_at"] else None
            data["updated_at"] = datetime.fromisoformat(data["updated_at"]) if data["updated_at"] else None
            if data["lease_expires_at"]:
                data["lease_expires_at"] = datetime.fromisoformat(data["lease_expires_at"])
            if data["evaluation"]:
                try:
                    eval_data = json.loads(data["evaluation"])
                    data["evaluation"] = TaskEvaluation(**eval_data) if eval_data else None
                except (json.JSONDecodeError, TypeError):
                    data["evaluation"] = None
            task = Task(**data)
            # Cache the result
            self._set_cache(cache_key, task)
            return task
        return None

    async def delete_task(self, task_id: str) -> None:
        await self._execute_sync("DELETE FROM tasks WHERE id = ?", (task_id,))

    async def delete_hunter(self, hunter_id: str) -> None:
        await self._execute_sync("DELETE FROM hunters WHERE id = ?", (hunter_id,))

    async def delete_report(self, report_id: str) -> None:
        await self._execute_sync("DELETE FROM reports WHERE id = ?", (report_id,))

    async def save_hunter(self, hunter: Hunter) -> None:
        await self._execute_sync(
            "INSERT OR REPLACE INTO hunters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                hunter.id,
                json.dumps(hunter.skills),
                hunter.status,
                json.dumps(hunter.current_tasks),
                hunter.completed_tasks,
                hunter.failed_tasks,
                hunter.created_at.isoformat(),
                hunter.updated_at.isoformat(),
                hunter.last_read_discussion_timestamp.isoformat() if hunter.last_read_discussion_timestamp else None,
            ),
        )
        # Invalidate hunter cache when saving
        self._invalidate_cache("hunter:")

    async def get_hunter(self, hunter_id: str) -> Hunter | None:
        # Check cache first
        cache_key = self._cache_key("hunter", hunter_id)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
            
        cursor = await self._execute_sync("SELECT * FROM hunters WHERE id = ?", (hunter_id,))
        row = await anyio.to_thread.run_sync(cursor.fetchone)
        if row:
            data = dict(row)
            data["skills"] = json.loads(data["skills"])
            data["current_tasks"] = json.loads(data["current_tasks"])
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            if data["last_read_discussion_timestamp"]:
                data["last_read_discussion_timestamp"] = datetime.fromisoformat(data["last_read_discussion_timestamp"])
            hunter = Hunter(**data)
            # Cache the result
            self._set_cache(cache_key, hunter)
            return hunter
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
            if data["created_at"]:
                data["created_at"] = datetime.fromisoformat(data["created_at"])
            if data["updated_at"]:
                data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            if data["evaluation"]:
                try:
                    eval_data = json.loads(data["evaluation"])
                    data["evaluation"] = ReportEvaluation(**eval_data)
                except (json.JSONDecodeError, TypeError):
                    data["evaluation"] = None
            return Report(**data)
        return None

    async def save_discussion_message(self, message: DiscussionMessage) -> None:
        await self._execute_sync(
            "INSERT OR REPLACE INTO discussion_messages (id, hunter_id, content, created_at) VALUES (?, ?, ?, ?)",
            (
                message.id,
                message.hunter_id,
                message.content,
                message.created_at.isoformat(),
            ),
        )

    async def get_messages_after_timestamp(self, timestamp: datetime, limit: int = 50) -> list[DiscussionMessage]:
        cursor = await self._execute_sync(
            "SELECT * FROM discussion_messages WHERE created_at > ? ORDER BY created_at ASC LIMIT ?",
            (timestamp.isoformat(), limit)
        )
        rows = await anyio.to_thread.run_sync(cursor.fetchall)
        messages = []
        for row in rows:
            data = dict(row)
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            messages.append(DiscussionMessage(**data))
        return messages

    async def get_latest_messages(self, limit: int = 100) -> list[DiscussionMessage]:
        cursor = await self._execute_sync("SELECT * FROM discussion_messages ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = await anyio.to_thread.run_sync(cursor.fetchall)
        messages = []
        for row in reversed(rows):
            data = dict(row)
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            messages.append(DiscussionMessage(**data))
        return messages

    async def update_hunter_last_read_timestamp(self, hunter_id: str, timestamp: datetime) -> None:
        await self._execute_sync(
            "UPDATE hunters SET last_read_discussion_timestamp = ? WHERE id = ?",
            (timestamp.isoformat(), hunter_id)
        )

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
        tasks = []
        for row in rows:
            data = dict(row)
            data["status"] = TaskStatus(data["status"])
            data["depends_on"] = json.loads(data["depends_on"]) if data["depends_on"] else []
            data["created_at"] = datetime.fromisoformat(data["created_at"]) if data["created_at"] else None
            data["updated_at"] = datetime.fromisoformat(data["updated_at"]) if data["updated_at"] else None
            if data["lease_expires_at"]:
                data["lease_expires_at"] = datetime.fromisoformat(data["lease_expires_at"])
            if data["evaluation"]:
                try:
                    eval_data = json.loads(data["evaluation"])
                    data["evaluation"] = TaskEvaluation(**eval_data) if eval_data else None
                except (json.JSONDecodeError, TypeError):
                    data["evaluation"] = None
            tasks.append(Task(**data))
        return tasks

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
        reports = []
        for row in rows:
            data = dict(row)
            if data["created_at"]:
                data["created_at"] = datetime.fromisoformat(data["created_at"])
            if data["updated_at"]:
                data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            if data["evaluation"]:
                try:
                    eval_data = json.loads(data["evaluation"])
                    data["evaluation"] = ReportEvaluation(**eval_data)
                except (json.JSONDecodeError, TypeError):
                    data["evaluation"] = None
            reports.append(Report(**data))
        return reports