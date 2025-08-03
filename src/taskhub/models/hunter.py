"""
Hunter模型定义
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Hunter(BaseModel):
    """赏金猎人模型"""

    id: str = Field(..., description="猎人唯一标识")
    skills: dict[str, int] = Field(default_factory=dict, description="猎人的技能及其熟练度分数")
    status: str = Field(default="active", description="猎人状态")
    current_tasks: list[str] = Field(default_factory=list, description="当前任务ID列表")
    completed_tasks: int = Field(default=0, description="已完成任务数量")
    failed_tasks: int = Field(default=0, description="失败任务数量")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
