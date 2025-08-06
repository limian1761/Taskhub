"""
猎人模型定义
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class Hunter(BaseModel):
    """猎人模型"""

    id: str = Field(..., description="猎人唯一标识")
    skills: dict[str, int] = Field(default_factory=dict, description="技能字典")
    reputation: int = Field(default=0, description="声望值")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_read_discussion_timestamp: Optional[datetime] = Field(default=None, description="最后阅读讨论的时间戳")