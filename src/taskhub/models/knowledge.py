"""
知识库模型定义
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class KnowledgeItem(BaseModel):
    """知识库条目模型"""

    id: str = Field(..., description="知识点唯一标识")
    title: str = Field(..., description="知识点标题")
    content: str = Field(..., description="知识点内容")
    source: str = Field(..., description="知识来源")
    skill_tags: list[str] = Field(..., description="关联的技能标签")
    created_by: str = Field(..., description="创建者ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))