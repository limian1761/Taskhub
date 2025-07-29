"""
代理模型定义
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class Agent(BaseModel):
    """代理模型"""
    id: str = Field(..., description="代理唯一标识")
    name: str = Field(..., description="代理名称")
    capabilities: List[str] = Field(..., description="代理能力列表")
    capability_levels: Dict[str, int] = Field(default_factory=dict, description="能力等级映射")
    reputation: int = Field(default=0, description="代理声望值")
    status: str = Field(default="active", description="代理状态")
    current_tasks: List[str] = Field(default_factory=list, description="当前任务ID列表")
    completed_tasks: int = Field(default=0, description="已完成任务数量")
    failed_tasks: int = Field(default=0, description="失败任务数量")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentCapability(BaseModel):
    """代理能力模型"""
    name: str = Field(..., description="能力名称")
    level: int = Field(default=1, description="能力等级")
    metadata: Dict[str, str] = Field(default_factory=dict, description="能力元数据")