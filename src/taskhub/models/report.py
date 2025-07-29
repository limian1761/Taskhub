"""
报告模型定义
"""
from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class ReportEvaluation(BaseModel):
    """报告评价模型"""
    
    score: int = Field(..., ge=0, le=100, description="评价分数 0-100")
    reputation_change: int = Field(..., description="声望值变化")
    feedback: str = Field(..., description="评价反馈")
    evaluator_id: str = Field(..., description="评价者ID")
    capability_updates: Dict[str, int] = Field(default_factory=dict, description="能力等级更新")
    evaluated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Report(BaseModel):
    """任务报告模型"""
    
    id: str = Field(..., description="报告唯一标识")
    task_id: str = Field(..., description="关联的任务ID")
    agent_id: str = Field(..., description="提交报告的代理ID")
    status: str = Field(..., description="报告状态: pending, submitted, reviewed")
    details: Optional[str] = Field(None, description="报告详情")
    result: Optional[str] = Field(None, description="执行结果")
    evaluation: Optional[ReportEvaluation] = Field(None, description="评价结果")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ReportSubmitParams(BaseModel):
    """提交任务报告的参数模型"""
    
    task_id: str = Field(..., description="任务ID")
    agent_id: str = Field(..., description="代理ID")
    status: str = Field(..., description="任务状态")
    details: Optional[str] = Field(None, description="报告详情")
    result: Optional[str] = Field(None, description="执行结果")


class ReportListParams(BaseModel):
    """获取报告列表的参数模型"""
    
    task_id: Optional[str] = Field(None, description="按任务ID筛选")
    agent_id: Optional[str] = Field(None, description="按代理ID筛选")
    status: Optional[str] = Field(None, description="按状态筛选：pending, submitted, reviewed")
    limit: Optional[int] = Field(100, description="返回结果数量限制", ge=1, le=1000)