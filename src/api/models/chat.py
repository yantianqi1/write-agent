"""
聊天API模型
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """聊天消息"""
    id: str = Field(default_factory=lambda: f"msg_{datetime.now().timestamp()}")
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatRequest(BaseModel):
    """聊天请求"""
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=10000)
    project_id: Optional[str] = None
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    message: Message
    session_id: str
    should_create: bool = False
    metadata: Optional[dict] = None
