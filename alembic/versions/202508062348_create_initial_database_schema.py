"""Create initial database schema from existing tables

Revision ID: 202508062348
Revises: 
Create Date: 2025-08-06 23:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '202508062348'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all tables
    op.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
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
            published_by_hunter_id TEXT,
            created_at TEXT,
            updated_at TEXT,
            evaluation TEXT,
            is_archived INTEGER
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS hunters (
            id TEXT PRIMARY KEY,
            skills TEXT,
            status TEXT,
            current_tasks TEXT,
            completed_tasks INTEGER,
            failed_tasks INTEGER,
            created_at TEXT,
            updated_at TEXT,
            last_read_discussion_timestamp TEXT
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            task_id TEXT,
            hunter_id TEXT,
            status TEXT,
            details TEXT,
            result TEXT,
            evaluation TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_items (
            id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            source TEXT,
            skill_tags TEXT,
            created_by TEXT,
            created_at TEXT
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS domains (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            description TEXT,
            created_at TEXT
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS discussion_messages (
            id TEXT PRIMARY KEY,
            hunter_id TEXT,
            content TEXT,
            created_at TEXT
        )
    """)
    
    op.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_items_fts USING fts5(
            id UNINDEXED,
            title,
            content
        )
    """)
    
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_items_ai AFTER INSERT ON knowledge_items
        BEGIN
            INSERT INTO knowledge_items_fts(id, title, content) 
            VALUES (new.id, new.title, new.content);
        END
    """)
    
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_items_ad AFTER DELETE ON knowledge_items
        BEGIN
            DELETE FROM knowledge_items_fts WHERE id = old.id;
        END
    """)
    
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_items_au AFTER UPDATE ON knowledge_items
        BEGIN
            UPDATE knowledge_items_fts 
            SET title = new.title, content = new.content 
            WHERE id = new.id;
        END
    """)


def downgrade() -> None:
    # Drop all tables in reverse order
    op.execute("DROP TRIGGER IF EXISTS knowledge_items_au")
    op.execute("DROP TRIGGER IF EXISTS knowledge_items_ad")
    op.execute("DROP TRIGGER IF EXISTS knowledge_items_ai")
    op.execute("DROP TABLE IF EXISTS knowledge_items_fts")
    op.execute("DROP TABLE IF EXISTS discussion_messages")
    op.execute("DROP TABLE IF EXISTS domains")
    op.execute("DROP TABLE IF EXISTS knowledge_items")
    op.execute("DROP TABLE IF EXISTS reports")
    op.execute("DROP TABLE IF EXISTS hunters")
    op.execute("DROP TABLE IF EXISTS tasks")