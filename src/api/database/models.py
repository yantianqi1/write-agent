"""
数据库ORM模型

定义所有数据表的SQLAlchemy模型
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    Boolean,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import VARCHAR
from enum import Enum

from .base import Base, TimestampMixin


# ============================================================================
# 枚举定义
# ============================================================================


class SessionStatus(str, Enum):
    """会话状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ProjectStatus(str, Enum):
    """项目状态"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class GenerationMode(str, Enum):
    """生成模式"""
    FULL = "full"           # 完整生成
    CONTINUE = "continue"   # 续写
    EXPAND = "expand"       # 扩写
    REWRITE = "rewrite"     # 重写
    OUTLINE = "outline"     # 生成大纲


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# 聊天会话相关模型
# ============================================================================


class SessionModel(Base, TimestampMixin):
    """聊天会话模型"""
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        VARCHAR(36), unique=True, index=True, nullable=False
    )
    project_id: Mapped[Optional[str]] = mapped_column(
        VARCHAR(36), ForeignKey("projects.project_id"), nullable=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        SQLEnum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False
    )
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # 关系
    messages: Mapped[List["MessageModel"]] = relationship(
        "MessageModel", back_populates="session", cascade="all, delete-orphan"
    )
    project: Mapped[Optional["Project"]] = relationship(
        "Project", back_populates="chat_sessions"
    )

    def __repr__(self) -> str:
        return f"<SessionModel(id={self.id}, session_id={self.session_id}, title={self.title})>"


class MessageModel(Base, TimestampMixin):
    """聊天消息模型"""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        SQLEnum(MessageRole), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # 关系
    session: Mapped["SessionModel"] = relationship(
        "SessionModel", back_populates="messages"
    )

    __table_args__ = (
        Index("ix_messages_session_created", "session_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<MessageModel(id={self.id}, role={self.role}, content_len={len(self.content)})>"


# ============================================================================
# 项目相关模型
# ============================================================================


class Project(Base, TimestampMixin):
    """创作项目模型"""
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        VARCHAR(36), unique=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    genre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False
    )
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chapter_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 关系
    chapters: Mapped[List["Chapter"]] = relationship(
        "Chapter", back_populates="project", cascade="all, delete-orphan"
    )
    generation_tasks: Mapped[List["GenerationTask"]] = relationship(
        "GenerationTask", back_populates="project", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[List["SessionModel"]] = relationship(
        "SessionModel", back_populates="project"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, project_id={self.project_id}, title={self.title})>"


class Chapter(Base, TimestampMixin):
    """章节内容模型"""
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chapter_id: Mapped[str] = mapped_column(
        VARCHAR(36), unique=True, index=True, nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 关系
    project: Mapped["Project"] = relationship("Project", back_populates="chapters")
    versions: Mapped[List["ChapterVersion"]] = relationship(
        "ChapterVersion", back_populates="chapter", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_chapters_project_order", "project_id", "order_index"),
    )

    def __repr__(self) -> str:
        return f"<Chapter(id={self.id}, chapter_id={self.chapter_id}, title={self.title})>"


class ChapterVersion(Base, TimestampMixin):
    """章节版本历史模型"""
    __tablename__ = "chapter_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chapters.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    change_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # 关系
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="versions")

    __table_args__ = (
        Index("ix_chapter_versions_chapter_version", "chapter_id", "version_number"),
    )

    def __repr__(self) -> str:
        return f"<ChapterVersion(id={self.id}, chapter_id={self.chapter_id}, version={self.version_number})>"


# ============================================================================
# 生成任务相关模型
# ============================================================================


class GenerationTask(Base, TimestampMixin):
    """生成任务模型"""
    __tablename__ = "generation_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        VARCHAR(36), unique=True, index=True, nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False
    )
    mode: Mapped[str] = mapped_column(SQLEnum(GenerationMode), nullable=False)
    chapter_id: Mapped[Optional[str]] = mapped_column(VARCHAR(36), nullable=True)
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 关系
    project: Mapped["Project"] = relationship("Project", back_populates="generation_tasks")

    def __repr__(self) -> str:
        return f"<GenerationTask(id={self.id}, task_id={self.task_id}, status={self.status})>"


# ============================================================================
# 导出所有模型
# ============================================================================

__all__ = [
    # Enums
    "SessionStatus",
    "MessageRole",
    "ProjectStatus",
    "GenerationMode",
    "TaskStatus",
    # Models
    "SessionModel",
    "MessageModel",
    "Project",
    "Chapter",
    "ChapterVersion",
    "GenerationTask",
]
