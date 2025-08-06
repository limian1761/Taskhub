"""Add status to knowledge_items

Revision ID: 202508070001
Revises: 202508062348
Create Date: 2025-08-07 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '202508070001'
down_revision: Union[str, None] = '202508062348'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column to knowledge_items table with default value 'draft'
    op.execute("ALTER TABLE knowledge_items ADD COLUMN status TEXT DEFAULT 'draft'")
    
    # Update the FTS table to include the status column
    # Since FTS doesn't need to index the status, we don't need to modify the FTS table


def downgrade() -> None:
    # Remove status column from knowledge_items table
    op.execute("CREATE TABLE knowledge_items_backup AS SELECT id, title, content, source, skill_tags, created_by, created_at FROM knowledge_items")
    op.execute("DROP TABLE knowledge_items")
    op.execute("""CREATE TABLE knowledge_items (
        id TEXT PRIMARY KEY,
        title TEXT,
        content TEXT,
        source TEXT,
        skill_tags TEXT,
        created_by TEXT,
        created_at TEXT
    )""")
    op.execute("INSERT INTO knowledge_items SELECT * FROM knowledge_items_backup")
    op.execute("DROP TABLE knowledge_items_backup")