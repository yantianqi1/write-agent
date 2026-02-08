"""
CRUD操作封装

提供所有模型的CRUD操作函数
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from .models import (
    SessionModel,
    MessageModel,
    Project,
    Chapter,
    ChapterVersion,
    GenerationTask,
    ProjectStatus,
    TaskStatus,
    MessageRole,
    SessionStatus,
    GenerationMode,
)


# ============================================================================
# Session CRUD
# ============================================================================


async def create_session(
    db: AsyncSession,
    session_id: str,
    project_id: Optional[str] = None,
    title: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> SessionModel:
    """创建新的聊天会话"""
    session = SessionModel(
        session_id=session_id,
        project_id=project_id,
        title=title,
        status=SessionStatus.ACTIVE,
        meta=metadata or {},
    )
    db.add(session)
    await db.flush()
    return session


async def get_session_by_id(
    db: AsyncSession,
    session_id: str,
) -> Optional[SessionModel]:
    """根据session_id获取会话"""
    stmt = select(SessionModel).where(
        SessionModel.session_id == session_id,
        SessionModel.status != SessionStatus.DELETED
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession,
    project_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[SessionModel]:
    """列出会话"""
    stmt = select(SessionModel).where(
        SessionModel.status != SessionStatus.DELETED
    )
    if project_id:
        stmt = stmt.where(SessionModel.project_id == project_id)
    stmt = stmt.order_by(desc(SessionModel.updated_at))
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_sessions_with_message_counts(
    db: AsyncSession,
    project_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    获取会话列表及消息数量（单次查询）

    返回格式:
    [
        {
            "session_id": "...",
            "title": "...",
            "updated_at": "...",
            "message_count": 5,
            "last_message_at": "..."
        },
        ...
    ]
    """
    # 使用join和group_by一次性获取会话和消息计数
    stmt = select(
        SessionModel.session_id,
        SessionModel.title,
        SessionModel.updated_at,
        SessionModel.project_id,
        func.coalesce(func.count(MessageModel.id), 0).label("message_count"),
        func.max(MessageModel.created_at).label("last_message_at"),
    ).outerjoin(
        MessageModel, SessionModel.id == MessageModel.session_id
    ).where(
        SessionModel.status != SessionStatus.DELETED
    ).group_by(
        SessionModel.id
    ).order_by(
        desc(SessionModel.updated_at)
    ).limit(limit)

    if project_id:
        stmt = stmt.where(SessionModel.project_id == project_id)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "session_id": row.session_id,
            "title": row.title,
            "updated_at": row.updated_at,
            "project_id": row.project_id,
            "message_count": row.message_count,
            "last_message_at": row.last_message_at,
        }
        for row in rows
    ]


async def delete_session(
    db: AsyncSession,
    session_id: str,
) -> bool:
    """删除会话（软删除）"""
    session = await get_session_by_id(db, session_id)
    if session:
        session.status = SessionStatus.DELETED
        await db.flush()
        return True
    return False


async def update_session(
    db: AsyncSession,
    session_id: str,
    title: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> Optional[SessionModel]:
    """更新会话"""
    session = await get_session_by_id(db, session_id)
    if session:
        if title is not None:
            session.title = title
        if metadata is not None:
            session.meta.update(metadata)
        await db.flush()
        return session
    return None


# ============================================================================
# Message CRUD
# ============================================================================


async def create_message(
    db: AsyncSession,
    session_internal_id: int,
    role: MessageRole,
    content: str,
    metadata: Optional[Dict] = None,
) -> MessageModel:
    """创建消息"""
    message = MessageModel(
        session_id=session_internal_id,
        role=role,
        content=content,
        meta=metadata or {},
    )
    db.add(message)
    await db.flush()
    return message


async def get_session_messages(
    db: AsyncSession,
    session_internal_id: int,
    limit: int = 100,
) -> List[MessageModel]:
    """获取会话的所有消息"""
    stmt = select(MessageModel).where(
        MessageModel.session_id == session_internal_id
    ).order_by(MessageModel.created_at).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ============================================================================
# Project CRUD
# ============================================================================


async def create_project(
    db: AsyncSession,
    project_id: str,
    title: str,
    description: Optional[str] = None,
    genre: Optional[str] = None,
    settings: Optional[Dict] = None,
) -> Project:
    """创建项目"""
    project = Project(
        project_id=project_id,
        title=title,
        description=description,
        genre=genre,
        status=ProjectStatus.DRAFT,
        settings=settings or {},
        word_count=0,
        chapter_count=0,
    )
    db.add(project)
    await db.flush()
    return project


async def get_project_by_id(
    db: AsyncSession,
    project_id: str,
) -> Optional[Project]:
    """根据project_id获取项目"""
    stmt = select(Project).where(Project.project_id == project_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_project_with_chapters(
    db: AsyncSession,
    project_id: str,
) -> Optional[Project]:
    """
    获取项目及其章节（使用selectinload避免N+1查询）

    当需要访问项目章节时使用此方法
    """
    stmt = select(Project).options(
        selectinload(Project.chapters)
    ).where(Project.project_id == project_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_projects(
    db: AsyncSession,
    status: Optional[ProjectStatus] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Project]:
    """列出项目"""
    stmt = select(Project)
    if status:
        stmt = stmt.where(Project.status == status)
    stmt = stmt.order_by(desc(Project.updated_at))
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_project(
    db: AsyncSession,
    project_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    genre: Optional[str] = None,
    status: Optional[ProjectStatus] = None,
) -> Optional[Project]:
    """更新项目信息"""
    project = await get_project_by_id(db, project_id)
    if project:
        if title is not None:
            project.title = title
        if description is not None:
            project.description = description
        if genre is not None:
            project.genre = genre
        if status is not None:
            project.status = status
        await db.flush()
        return project
    return None


async def delete_project(
    db: AsyncSession,
    project_id: str,
) -> bool:
    """删除项目"""
    project = await get_project_by_id(db, project_id)
    if project:
        await db.delete(project)
        await db.flush()
        return True
    return False


async def update_project_word_count(
    db: AsyncSession,
    project_id: str,
) -> None:
    """
    更新项目的字数统计

    优化版本：使用单次查询获取字数和章节数
    """
    project = await get_project_by_id(db, project_id)
    if project:
        # 使用单次查询同时获取字数和章节数
        stmt = select(
            func.coalesce(func.sum(Chapter.word_count), 0),
            func.coalesce(func.count(Chapter.id), 0)
        ).where(Chapter.project_id == project.id)
        result = await db.execute(stmt)
        total_words, chapter_count = result.one()

        project.word_count = total_words
        project.chapter_count = chapter_count
        await db.flush()


# ============================================================================
# Chapter CRUD
# ============================================================================


async def create_chapter(
    db: AsyncSession,
    chapter_id: str,
    project_id: str,
    title: str,
    content: str,
    order_index: int,
    summary: Optional[str] = None,
    notes: Optional[str] = None,
) -> Chapter:
    """创建章节"""
    # 获取项目的内部ID
    project = await get_project_by_id(db, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    word_count = len(content)

    chapter = Chapter(
        chapter_id=chapter_id,
        project_id=project.id,
        title=title,
        content=content,
        order_index=order_index,
        word_count=word_count,
        summary=summary,
        notes=notes,
    )
    db.add(chapter)
    await db.flush()

    # 更新项目字数
    await update_project_word_count(db, project_id)

    return chapter


async def get_chapter_by_id(
    db: AsyncSession,
    chapter_id: str,
) -> Optional[Chapter]:
    """根据chapter_id获取章节"""
    stmt = select(Chapter).where(Chapter.chapter_id == chapter_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_chapters(
    db: AsyncSession,
    project_id: str,
    limit: int = 100,
    offset: int = 0,
) -> List[Chapter]:
    """列出项目的所有章节"""
    project = await get_project_by_id(db, project_id)
    if not project:
        return []

    stmt = select(Chapter).where(
        Chapter.project_id == project.id
    ).order_by(Chapter.order_index)
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_chapter(
    db: AsyncSession,
    chapter_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    summary: Optional[str] = None,
    notes: Optional[str] = None,
    create_version: bool = False,
    change_description: Optional[str] = None,
) -> Optional[Chapter]:
    """更新章节"""
    chapter = await get_chapter_by_id(db, chapter_id)
    if chapter:
        # 如果需要创建版本历史
        if create_version and content and content != chapter.content:
            await create_chapter_version(
                db,
                chapter.id,
                chapter.content,
                change_description or "Auto-save before update",
            )

        if title is not None:
            chapter.title = title
        if content is not None:
            chapter.content = content
            chapter.word_count = len(content)
        if summary is not None:
            chapter.summary = summary
        if notes is not None:
            chapter.notes = notes

        await db.flush()

        # 更新项目字数
        await update_project_word_count(
            db,
            (await db.execute(select(Project).where(Project.id == chapter.project_id)))
            .scalar_one()
            .project_id
        )

        return chapter
    return None


async def delete_chapter(
    db: AsyncSession,
    chapter_id: str,
) -> bool:
    """删除章节"""
    chapter = await get_chapter_by_id(db, chapter_id)
    if chapter:
        project_id = (await db.execute(
            select(Project).where(Project.id == chapter.project_id)
        )).scalar_one().project_id

        await db.delete(chapter)
        await db.flush()

        # 更新项目字数
        await update_project_word_count(db, project_id)
        return True
    return False


# ============================================================================
# Chapter Version CRUD
# ============================================================================


async def create_chapter_version(
    db: AsyncSession,
    chapter_internal_id: int,
    content: str,
    change_description: Optional[str] = None,
) -> ChapterVersion:
    """创建章节版本"""
    # 获取当前版本号
    stmt = select(func.count(ChapterVersion.id)).where(
        ChapterVersion.chapter_id == chapter_internal_id
    )
    result = await db.execute(stmt)
    version_number = (result.scalar() or 0) + 1

    version = ChapterVersion(
        chapter_id=chapter_internal_id,
        content=content,
        change_description=change_description,
        version_number=version_number,
    )
    db.add(version)
    await db.flush()
    return version


async def list_chapter_versions(
    db: AsyncSession,
    chapter_id: str,
    limit: int = 20,
) -> List[ChapterVersion]:
    """列出章节的版本历史"""
    chapter = await get_chapter_by_id(db, chapter_id)
    if not chapter:
        return []

    stmt = select(ChapterVersion).where(
        ChapterVersion.chapter_id == chapter.id
    ).order_by(desc(ChapterVersion.created_at)).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ============================================================================
# Generation Task CRUD
# ============================================================================


async def create_generation_task(
    db: AsyncSession,
    task_id: str,
    project_id: str,
    mode: GenerationMode,
    chapter_id: Optional[str] = None,
    prompt: Optional[str] = None,
) -> GenerationTask:
    """创建生成任务"""
    # 获取项目的内部ID
    project = await get_project_by_id(db, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    task = GenerationTask(
        task_id=task_id,
        project_id=project.id,
        status=TaskStatus.PENDING,
        mode=mode,
        chapter_id=chapter_id,
        prompt=prompt,
        result={},
    )
    db.add(task)
    await db.flush()
    return task


async def get_generation_task_by_id(
    db: AsyncSession,
    task_id: str,
) -> Optional[GenerationTask]:
    """根据task_id获取生成任务"""
    stmt = select(GenerationTask).where(GenerationTask.task_id == task_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_generation_task_status(
    db: AsyncSession,
    task_id: str,
    status: TaskStatus,
    result: Optional[Dict] = None,
    error_message: Optional[str] = None,
) -> Optional[GenerationTask]:
    """更新生成任务状态"""
    task = await get_generation_task_by_id(db, task_id)
    if task:
        task.status = status
        if result is not None:
            task.result = result
        if error_message is not None:
            task.error_message = error_message

        if status == TaskStatus.RUNNING and not task.started_at:
            task.started_at = datetime.now()
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()

        await db.flush()
        return task
    return None


async def list_generation_tasks(
    db: AsyncSession,
    project_id: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    limit: int = 50,
) -> List[GenerationTask]:
    """列出生成任务"""
    stmt = select(GenerationTask)
    if project_id:
        project = await get_project_by_id(db, project_id)
        if project:
            stmt = stmt.where(GenerationTask.project_id == project.id)
        else:
            return []
    if status:
        stmt = stmt.where(GenerationTask.status == status)
    stmt = stmt.order_by(desc(GenerationTask.created_at)).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ============================================================================
# 导出所有函数
# ============================================================================

__all__ = [
    # Session
    "create_session",
    "get_session_by_id",
    "list_sessions",
    "get_sessions_with_message_counts",  # 新增
    "delete_session",
    "update_session",
    # Message
    "create_message",
    "get_session_messages",
    # Project
    "create_project",
    "get_project_by_id",
    "get_project_with_chapters",  # 新增
    "list_projects",
    "update_project",
    "delete_project",
    "update_project_word_count",
    # Chapter
    "create_chapter",
    "get_chapter_by_id",
    "list_chapters",
    "update_chapter",
    "delete_chapter",
    # Chapter Version
    "create_chapter_version",
    "list_chapter_versions",
    # Generation Task
    "create_generation_task",
    "get_generation_task_by_id",
    "update_generation_task_status",
    "list_generation_tasks",
]
