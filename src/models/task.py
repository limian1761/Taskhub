from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class TaskEvaluation(BaseModel):
    """任务评价信息"""
    score: int = Field(..., description="任务评分 1-100")
    reputation_change: int = Field(..., description="声望值变化")
    feedback: str = Field(..., description="评价反馈")
    evaluator_id: str = Field(..., description="评价者ID")
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    capability_updates: Dict[str, int] = Field(default_factory=dict, description="能力等级更新")


class Task(BaseModel):
    id: str = Field(..., description="任务唯一标识")
    name: str = Field(..., description="任务名称")
    details: str = Field(..., description="任务详情")
    capability: str = Field(..., description="所需能力")
    status: str = Field(default="pending", description="任务状态")
    assignee: Optional[str] = None
    lease_id: Optional[str] = None
    lease_expires_at: Optional[datetime] = None
    depends_on: List[str] = Field(default_factory=list)
    parent_task_id: Optional[str] = None
    created_by: Optional[str] = Field(None, description="任务创建者ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluation: Optional[TaskEvaluation] = Field(None, description="任务评价信息")
    is_archived: bool = Field(default=False, description="是否已归档")
    candidates: List[str] = Field(default_factory=list, description="候选代理ID列表")


class TaskCreateRequest(BaseModel):
    name: str = Field(..., description="任务名称")
    details: str = Field(..., description="任务详情")
    capability: str = Field(..., description="所需能力")
    depends_on: List[str] = Field(default_factory=list)
    parent_task_id: Optional[str] = None
    candidates: List[str] = Field(default_factory=list, description="候选代理ID列表")


class TaskUpdateRequest(BaseModel):
    name: Optional[str] = None
    details: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None