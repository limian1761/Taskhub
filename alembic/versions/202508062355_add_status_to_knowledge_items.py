"""Add status to knowledge_items

Revision ID: 202508062355
Revises: 202508062348
Create Date: 2025-08-06 23:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '202508062355'
down_revision: Union[str, None] = '202508062348'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column to knowledge_items table with default value 'draft'
    op.execute("ALTER TABLE knowledge_items ADD COLUMN status TEXT DEFAULT 'draft'")
    
    # Update existing records to have 'published' status to maintain backward compatibility
    op.execute("UPDATE knowledge_items SET status = 'published'")


def downgrade() -> None:
    # Remove status column from knowledge_items table
    op.execute("ALTER TABLE knowledge_items DROP COLUMN status")