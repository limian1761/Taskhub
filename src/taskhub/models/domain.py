"""
领域模型定义
"""
from pydantic import BaseModel, Field
from datetime import datetime

class Domain(BaseModel):
    """领域模型"""
    id: str = Field(..., description="领域唯一标识")
    name: str = Field(..., description="领域名称")
    description: str = Field(..., description="领域描述")
    created_at: datetime = Field(default_factory=datetime.utcnow)
