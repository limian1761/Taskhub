"""
任务模型定义
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class TaskType(str, Enum):
    """任务类型枚举"""

    NORMAL = "NORMAL"
    EVALUATION = "EVALUATION"
    RESEARCH = "RESEARCH"  # 研究任务类型，用于知识发现和收集


class TaskEvaluation(BaseModel):
    """任务评价信息"""

    score: int = Field(..., description="任务评分 1-100")
    feedback: str = Field(..., description="评价反馈")
    evaluator_id: str = Field(..., description="评价者ID")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    skill_updates: dict[str, int] = Field(default_factory=dict, description="技能分数更新")


class Task(BaseModel):
    """任务模型"""

    id: str = Field(..., description="任务唯一标识")
    name: str = Field(..., description="任务名称")
    details: str = Field(..., description="任务详情")
    required_skill: str = Field(..., description="完成任务所需的核心技能")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    priority: int = Field(default=0, description="任务优先级，由发布者声望决定")
    hunter_id: str | None = Field(None, description="认领任务的猎人ID")
    lease_id: str | None = None
    lease_expires_at: datetime | None = None
    depends_on: list[str] = Field(default_factory=list)
    parent_task_id: str | None = None
    published_by_hunter_id: str | None = Field(None, description="任务发布者ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evaluation: TaskEvaluation | None = Field(None, description="任务评价信息")
    is_archived: bool = Field(default=False, description="是否已归档")
    task_type: TaskType = Field(default=TaskType.NORMAL, description="任务类型")
    report_id: str | None = Field(None, description="关联的报告ID")


class TaskCreateRequest(BaseModel):
    """任务创建请求"""

    name: str = Field(..., description="任务名称")
    details: str = Field(..., description="任务详情")
    required_skill: str = Field(..., description="所需技能")
    depends_on: list[str] = Field(default_factory=list)
    parent_task_id: str | None = None


class TaskUpdateRequest(BaseModel):
    """任务更新请求"""

    name: str | None = None
    details: str | None = None
    status: str | None = None
    assignee: str | None = None


class TaskListParams(BaseModel):
    """任务列表查询参数"""

    status: str | None = None
    required_skill: str | None = None
    hunter_id: str | None = None


class TaskDeleteParams(BaseModel):
    """任务删除参数"""

    task_id: str = Field(..., description="任务ID")
    force: bool = Field(default=False, description="是否强制删除")