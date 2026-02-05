"""
内容生成API模型
"""

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class GenerationMode(str, Enum):
    """生成模式"""
    FULL = "full"           # 完整生成
    CONTINUE = "continue"   # 续写
    EXPAND = "expand"       # 扩写
    REWRITE = "rewrite"     # 重写
    OUTLINE = "outline"     # 生成大纲


class GenerationRequest(BaseModel):
    """生成请求"""
    project_id: str
    mode: GenerationMode = GenerationMode.CONTINUE
    chapter_id: Optional[str] = None
    prompt: Optional[str] = Field(None, max_length=5000)
    chapter_number: Optional[int] = None


class GenerationResponse(BaseModel):
    """生成响应"""
    chapter_id: str
    content: str
    word_count: int
    generation_mode: GenerationMode
    metadata: Optional[dict] = None
