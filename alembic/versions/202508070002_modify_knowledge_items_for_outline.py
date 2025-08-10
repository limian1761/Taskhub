"""Modify knowledge_items table for Outline integration

Revision ID: 202508070002
Revises: 202508070001
Create Date: 2025-08-07 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlite3

# revision identifiers, used by Alembic.
revision = '202508070002'
down_revision = '202508070001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 删除旧的全文索引表
    op.execute("DROP TABLE IF EXISTS knowledge_items_fts")
    
    with op.batch_alter_table('knowledge_items', schema=None) as batch_op:
        # 删除content列
        batch_op.drop_column('content')
        # 添加Outline相关字段
        batch_op.add_column(sa.Column('outline_id', sa.String(), nullable=False))
        batch_op.add_column(sa.Column('url', sa.String(), nullable=False))


def downgrade() -> None:
    # 删除Outline相关字段
    with op.batch_alter_table('knowledge_items', schema=None) as batch_op:
        batch_op.drop_column('url')
        batch_op.drop_column('outline_id')
        # 恢复content列
        batch_op.add_column(sa.Column('content', sa.String(), nullable=False))
    
    # 重新创建全文索引表
    conn = op.get_bind()
    conn.execute(sa.text("""
        CREATE VIRTUAL TABLE knowledge_items_fts USING fts5(
            id,
            title,
            content,
            source,
            skill_tags,
            tokenize='porter'
        )
    """))
    
    # 填充全文索引表
    conn.execute(sa.text("""
        INSERT INTO knowledge_items_fts 
        SELECT id, title, content, source, skill_tags 
        FROM knowledge_items
    """))