"""
Discussion message model for the Taskhub system.
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field

from taskhub.utils.id_generator import generate_id


class DiscussionMessage(BaseModel):
    """Discussion message model"""
    
    id: str = Field(default_factory=lambda: generate_id("discussion"), description="消息唯一标识")
    hunter_id: str = Field(..., description="发言的猎人ID")
    content: str = Field(..., description="消息内容")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间")