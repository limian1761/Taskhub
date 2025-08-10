"""Remove knowledge_items and knowledge_items_fts tables

Revision ID: 202508070003
Revises: 202508070002
Create Date: 2025-08-07 00:03:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '202508070003'
down_revision = '202508070002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Drops the knowledge_items and knowledge_items_fts tables as knowledge
    is now fully managed in Outline.
    """
    op.execute("DROP TABLE IF EXISTS knowledge_items_fts")
    op.execute("DROP TABLE IF EXISTS knowledge_items")


def downgrade() -> None:
    """
    Recreates the knowledge_items and knowledge_items_fts tables.
    """
    # Recreate knowledge_items table
    op.create_table('knowledge_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('outline_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('skill_tags', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='draft', nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Recreate knowledge_items_fts table
    op.execute("""
        CREATE VIRTUAL TABLE knowledge_items_fts USING fts5(
            id UNINDEXED,
            title,
            url,
            source,
            skill_tags,
            content='knowledge_items'
        )
    """)
