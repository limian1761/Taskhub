"""
报告模型定义
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ReportEvaluation(BaseModel):
    """报告评价模型"""

    score: int = Field(..., ge=0, le=100, description="评价分数 0-100")
    feedback: str = Field(..., description="评价反馈")
    evaluator_id: str = Field(..., description="评价者ID")
    skill_updates: dict[str, int] = Field(default_factory=dict, description="技能分数更新")
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Report(BaseModel):
    """任务报告模型"""

    id: str = Field(..., description="报告唯一标识")
    task_id: str = Field(..., description="关联的任务ID")
    hunter_id: str = Field(..., description="提交报告的猎人ID")
    status: str = Field(..., description="报告状态: pending, submitted, reviewed")
    details: str | None = Field(None, description="报告详情")
    result: str | None = Field(None, description="执行结果")
    evaluation: ReportEvaluation | None = Field(None, description="评价结果")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReportListParams(BaseModel):
    """获取报告列表的参数模型"""

    task_id: str | None = Field(None, description="按任务ID筛选")
    hunter_id: str | None = Field(None, description="按猎人ID筛选")
    status: str | None = Field(None, description="按状态筛选：pending, submitted, reviewed")
    limit: int | None = Field(100, description="返回结果数量限制", ge=1, le=1000)