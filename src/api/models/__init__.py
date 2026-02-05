"""
API数据模型

定义所有API请求和响应的Pydantic模型
"""

from .chat import (
    ChatRequest,
    ChatResponse,
    Message as ChatMessage,
    MessageRole,
)
from .project import (
    ProjectInfo,
    ProjectCreate,
    ProjectUpdate,
    ChapterInfo,
    ChapterContent,
)
from .generation import (
    GenerationRequest,
    GenerationResponse,
    GenerationMode,
)

__all__ = [
    # Chat models
    "ChatRequest",
    "ChatResponse",
    "ChatMessage",
    "MessageRole",
    # Project models
    "ProjectInfo",
    "ProjectCreate",
    "ProjectUpdate",
    "ChapterInfo",
    "ChapterContent",
    # Generation models
    "GenerationRequest",
    "GenerationResponse",
    "GenerationMode",
]
