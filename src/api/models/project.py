"""
项目管理API模型
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ProjectInfo(BaseModel):
    """项目信息"""
    id: str
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    status: str = "draft"  # draft, in_progress, completed
    created_at: datetime
    updated_at: datetime
    word_count: int = 0
    chapter_count: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProjectCreate(BaseModel):
    """创建项目请求"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    genre: Optional[str] = None


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    genre: Optional[str] = None
    status: Optional[str] = None


class ChapterInfo(BaseModel):
    """章节信息"""
    id: str
    project_id: str
    title: str
    order: int
    word_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChapterContent(BaseModel):
    """章节内容"""
    id: str
    project_id: str
    title: str
    content: str
    order: int
    word_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
