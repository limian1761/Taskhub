"""
SQLite存储实现 (FTS5 Optimized) - Full Async Version
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

import anyio

from ..models.hunter import Hunter
from ..models.domain import Domain
from ..models.discussion import DiscussionMessage
from ..models.knowledge import KnowledgeItem
from ..models.report import Report, ReportEvaluation
from ..models.task import Task, TaskStatus
from ..models.discussion import DiscussionMessage
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
        # Tables are now managed by Alembic migrations
        # Only keep the ALTER TABLE statement for backward compatibility

        # Add last_read_discussion_timestamp to hunters table (if not exists)
        try:
            await self._execute_sync("ALTER TABLE hunters ADD COLUMN last_read_discussion_timestamp TEXT")
        except sqlite3.OperationalError as e:
            # Column already exists, ignore error
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

    async def get_task(self, task_id: str) -> Task | None:
        cursor = await self._execute_sync("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await anyio.to_thread.run_sync(cursor.fetchone)
        if row:
            data = dict(row)
            data["status"] = TaskStatus(data["status"])
            
            # 正确解析 depends_on 字段
            try:
                data["depends_on"] = json.loads(data["depends_on"]) if data["depends_on"] else []
            except (json.JSONDecodeError, TypeError):
                data["depends_on"] = []
            
            # 解析时间字段
            data["created_at"] = datetime.fromisoformat(data["created_at"]) if data["created_at"] else None
            data["updated_at"] = datetime.fromisoformat(data["updated_at"]) if data["updated_at"] else None
            if data["lease_expires_at"]:
                data["lease_expires_at"] = datetime.fromisoformat(data["lease_expires_at"]) if data["lease_expires_at"] else None
            
            # 解析评价信息
            if data["evaluation"]:
                try:
                    eval_data = json.loads(data["evaluation"])
                    if eval_data:
                        from ..models.task import TaskEvaluation
                        data["evaluation"] = TaskEvaluation(**eval_data)
                except (json.JSONDecodeError, TypeError):
                    data["evaluation"] = None
            
            return Task(**data)
        return None

    async def delete_task(self, task_id: str) -> None:
        await self._execute_sync("DELETE FROM tasks WHERE id = ?", (task_id,))

    async def delete_hunter(self, hunter_id: str) -> None:
        """Delete a hunter from the database."""
        await self._execute_sync("DELETE FROM hunters WHERE id = ?", (hunter_id,))

    async def delete_knowledge_item(self, knowledge_id: str) -> None:
        """Delete a knowledge item from the database."""
        await self._execute_sync("DELETE FROM knowledge_items WHERE id = ?", (knowledge_id,))
        await self._execute_sync("DELETE FROM knowledge_items_fts WHERE id = ?", (knowledge_id,))

    async def delete_report(self, report_id: str) -> None:
        """Delete a report from the database."""
        await self._execute_sync("DELETE FROM reports WHERE id = ?", (report_id,))

    # Transaction management methods
    async def begin(self) -> None:
        """Begins a new transaction."""
        await self._execute_sync("BEGIN")

    async def commit(self) -> None:
        """Commits the current transaction."""
        await self._execute_sync("COMMIT")

    async def rollback(self) -> None:
        """Rolls back the current transaction."""
        await self._execute_sync("ROLLBACK")

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

    async def get_hunter(self, hunter_id: str) -> Hunter | None:
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

    async def save_knowledge_item(self, item: KnowledgeItem) -> None:
        """Saves a knowledge item to the database and updates the FTS table."""
        # Save to the main table
        await self._execute_sync(
            "INSERT OR REPLACE INTO knowledge_items (id, title, content, source, skill_tags, created_by, created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item.id,
                item.title,
                item.content,
                item.source,
                json.dumps(item.skill_tags),
                item.created_by,
                item.created_at.isoformat(),
                item.status.value if hasattr(item.status, 'value') else item.status,
            ),
        )
        # Update the FTS table
        await self._execute_sync(
            "INSERT OR REPLACE INTO knowledge_items_fts (id, title, content) VALUES (?, ?, ?)",
            (item.id, item.title, item.content),
        )

    async def save_domain(self, domain: Domain) -> None:
        """Saves a domain to the database."""
        await self._execute_sync(
            "INSERT OR REPLACE INTO domains (id, name, description, created_at) VALUES (?, ?, ?, ?)",
            (
                domain.id,
                domain.name,
                domain.description,
                domain.created_at.isoformat(),
            ),
        )

    async def get_domain(self, domain_id: str) -> Domain | None:
        """Retrieves a domain by its ID."""
        cursor = await self._execute_sync("SELECT * FROM domains WHERE id = ?", (domain_id,))
        row = await anyio.to_thread.run_sync(cursor.fetchone)
        if row:
            data = dict(row)
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            return Domain(**data)
        return None

    async def list_domains(self) -> list[Domain]:
        """Lists all domains."""
        cursor = await self._execute_sync("SELECT * FROM domains ORDER BY created_at DESC")
        rows = await anyio.to_thread.run_sync(cursor.fetchall)
        domains = []
        for row in rows:
            data = dict(row)
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            domains.append(Domain(**data))
        return domains

    async def save_discussion_message(self, message: DiscussionMessage) -> None:
        """Saves a discussion message to the database."""
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
        """Get messages after a specific timestamp."""
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
        """Retrieves the latest messages from the discussion forum, in chronological order."""
        cursor = await self._execute_sync("SELECT * FROM discussion_messages ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = await anyio.to_thread.run_sync(cursor.fetchall)
        # Reverse the list to present messages in ascending chronological order in the UI
        messages = []
        for row in reversed(rows):
            data = dict(row)
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            messages.append(DiscussionMessage(**data))
        return messages

    async def update_hunter_last_read_timestamp(self, hunter_id: str, timestamp: datetime) -> None:
        """Update hunter's last read discussion timestamp."""
        await self._execute_sync(
            "UPDATE hunters SET last_read_discussion_timestamp = ? WHERE id = ?",
            (timestamp.isoformat(), hunter_id)
        )

    async def delete_all_hunters(self) -> None:
        """Delete all hunters from the database."""
        await self._execute_sync("DELETE FROM hunters")

    async def delete_all_tasks(self) -> None:
        """Delete all tasks from the database."""
        await self._execute_sync("DELETE FROM tasks")

    async def delete_all_reports(self) -> None:
        """Delete all reports from the database."""
        await self._execute_sync("DELETE FROM reports")

    async def delete_all_knowledge_items(self) -> None:
        """Delete all knowledge items from the database."""
        await self._execute_sync("DELETE FROM knowledge_items")
        await self._execute_sync("DELETE FROM knowledge_items_fts")

    async def get_knowledge_item(self, item_id: str) -> KnowledgeItem | None:
        """Retrieves a knowledge item by its ID."""
        cursor = await self._execute_sync("SELECT * FROM knowledge_items WHERE id = ?", (item_id,))
        row = await anyio.to_thread.run_sync(cursor.fetchone)
        if row:
            data = dict(row)
            data["skill_tags"] = json.loads(data["skill_tags"])
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            # Handle status field
            if "status" in data and data["status"]:
                from ..models.knowledge import KnowledgeStatus
                data["status"] = KnowledgeStatus(data["status"])
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
            # Handle status field
            if "status" in data and data["status"]:
                from ..models.knowledge import KnowledgeStatus
                data["status"] = KnowledgeStatus(data["status"])
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
        tasks = []
        for row in rows:
            data = dict(row)
            data["status"] = TaskStatus(data["status"])
            
            # 正确解析 depends_on 字段
            try:
                data["depends_on"] = json.loads(data["depends_on"]) if data["depends_on"] else []
            except (json.JSONDecodeError, TypeError):
                data["depends_on"] = []
            
            # 解析时间字段
            data["created_at"] = datetime.fromisoformat(data["created_at"]) if data["created_at"] else None
            data["updated_at"] = datetime.fromisoformat(data["updated_at"]) if data["updated_at"] else None
            if data["lease_expires_at"]:
                data["lease_expires_at"] = datetime.fromisoformat(data["lease_expires_at"]) if data["lease_expires_at"] else None
            
            # 解析评价信息
            if data["evaluation"]:
                try:
                    eval_data = json.loads(data["evaluation"])
                    if eval_data:
                        from ..models.task import TaskEvaluation
                        data["evaluation"] = TaskEvaluation(**eval_data)
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

    async def save_discussion_message(self, message: DiscussionMessage) -> None:
        """Saves a discussion message to the database."""
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
        """Retrieves messages created after a given timestamp."""
        cursor = await self._execute_sync(
            "SELECT * FROM discussion_messages WHERE created_at > ? ORDER BY created_at ASC LIMIT ?",
            (timestamp.isoformat(), limit),
        )
        rows = await anyio.to_thread.run_sync(cursor.fetchall)
        messages = []
        for row in rows:
            data = dict(row)
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            messages.append(DiscussionMessage(**data))
        return messages

    async def get_latest_messages(self, limit: int = 100) -> list[DiscussionMessage]:
        """Retrieves the latest messages from the discussion forum."""
        cursor = await self._execute_sync("SELECT * FROM discussion_messages ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = await anyio.to_thread.run_sync(cursor.fetchall)
        messages = []
        for row in rows:
            data = dict(row)
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            messages.append(DiscussionMessage(**data))
        return messages

    async def update_hunter_last_read_timestamp(self, hunter_id: str, timestamp: datetime) -> None:
        """Updates the last read timestamp for a hunter."""
        await self._execute_sync(
            "UPDATE hunters SET last_read_discussion_timestamp = ? WHERE id = ?",
            (timestamp.isoformat(), hunter_id),
        )
