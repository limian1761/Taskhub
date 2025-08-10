"""remove domains table

Revision ID: 202508070004
Revises: 202508070003
Create Date: 2025-08-07 00:04:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202508070004'
down_revision = '202508070003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Drops the domains table as this is now managed in Outline as Collections.
    """
    op.drop_table('domains')


def downgrade() -> None:
    """
    Recreates the domains table.
    """
    op.create_table('domains',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
