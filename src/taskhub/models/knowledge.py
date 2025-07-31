"""
知识库模型定义
"""
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class KnowledgeItem(BaseModel):
    """知识点模型"""
    id: str = Field(..., description="知识点唯一标识")
    title: str = Field(..., description="知识点标题")
    content: str = Field(..., description="知识点内容 (Markdown格式)")
    source: str = Field(..., description="知识来源 (例如: URL)")
    domain_tags: List[str] = Field(..., description="领域标签ID列表")
    created_by: str = Field(..., description="创建者Agent ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
