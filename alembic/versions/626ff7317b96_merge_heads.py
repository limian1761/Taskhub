"""merge heads

Revision ID: 626ff7317b96
Revises: 202508062355, 202508070004
Create Date: 2025-08-08 21:54:15.032332

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '626ff7317b96'
down_revision: Union[str, None] = ('202508062355', '202508070004')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass