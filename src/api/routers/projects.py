"""
项目管理API路由

处理小说项目的CRUD操作
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
import uuid
from datetime import datetime

from ..models.project import (
    ProjectInfo,
    ProjectCreate,
    ProjectUpdate,
    ChapterInfo,
)
from ..database import get_db
from ..database.crud import (
    create_project,
    get_project_by_id,
    list_projects as list_projects_db,
    update_project as update_project_db,
    delete_project as delete_project_db,
    create_chapter,
    get_chapter_by_id,
    list_chapters,
    update_chapter,
    delete_chapter,
)
from ..cache.decorators import cached_result
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@cached_result("all_projects", ttl=60)
@router.get("/", response_model=List[ProjectInfo])
async def list_projects(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """获取所有项目列表"""
    projects = await list_projects_db(db, limit=limit, offset=offset)

    result = []
    for project in projects:
        result.append(ProjectInfo(
            id=project.project_id,
            title=project.title,
            description=project.description,
            genre=project.genre,
            status=project.status.value,
            created_at=project.created_at,
            updated_at=project.updated_at,
            word_count=project.word_count,
            chapter_count=project.chapter_count,
        ))
    return result


@router.get("/{project_id}", response_model=ProjectInfo)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个项目详情"""
    from ..cache import get_cache

    # 先尝试从缓存获取
    cache_key = f"project:{project_id}"
    cache = get_cache()
    cached = cache.get(cache_key)
    if cached:
        return cached

    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = ProjectInfo(
        id=project.project_id,
        title=project.title,
        description=project.description,
        genre=project.genre,
        status=project.status.value,
        created_at=project.created_at,
        updated_at=project.updated_at,
        word_count=project.word_count,
        chapter_count=project.chapter_count,
    )

    # 存入缓存
    cache.set(cache_key, result)
    return result


@router.post("/", response_model=ProjectInfo)
async def create_new_project(request: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """创建新项目"""
    from ..cache import get_cache

    project_id = str(uuid.uuid4())

    project = await create_project(
        db=db,
        project_id=project_id,
        title=request.title,
        description=request.description,
        genre=request.genre,
    )
    await db.commit()

    # 清除项目列表缓存
    get_cache().delete("all_projects")

    return ProjectInfo(
        id=project.project_id,
        title=project.title,
        description=project.description,
        genre=project.genre,
        status=project.status.value,
        created_at=project.created_at,
        updated_at=project.updated_at,
        word_count=project.word_count,
        chapter_count=project.chapter_count,
    )


@router.put("/{project_id}", response_model=ProjectInfo)
async def update_project(
    project_id: str,
    request: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新项目信息"""
    from ..database.models import ProjectStatus
    from ..cache import get_cache

    # 转换状态字符串为枚举
    status = None
    if request.status is not None:
        try:
            status = ProjectStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")

    project = await update_project_db(
        db=db,
        project_id=project_id,
        title=request.title,
        description=request.description,
        genre=request.genre,
        status=status,
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.commit()

    # 刷新以确保所有属性已加载
    await db.refresh(project)

    # 清除项目缓存
    get_cache().delete(f"project:{project_id}")
    get_cache().delete("all_projects")

    return ProjectInfo(
        id=project.project_id,
        title=project.title,
        description=project.description,
        genre=project.genre,
        status=project.status.value,
        created_at=project.created_at,
        updated_at=project.updated_at,
        word_count=project.word_count,
        chapter_count=project.chapter_count,
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """删除项目"""
    from ..cache import get_cache

    success = await delete_project_db(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.commit()

    # 清除项目缓存
    get_cache().delete(f"project:{project_id}")

    return {"message": "Project deleted"}


@router.get("/{project_id}/chapters", response_model=List[ChapterInfo])
async def get_chapters(
    project_id: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """获取项目的所有章节"""
    # 验证项目存在
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chapters = await list_chapters(db, project_id, limit=limit, offset=offset)

    return [
        ChapterInfo(
            id=ch.chapter_id,
            project_id=project_id,
            title=ch.title,
            order=ch.order_index,
            word_count=ch.word_count,
            created_at=ch.created_at,
            updated_at=ch.updated_at,
        )
        for ch in chapters
    ]


@router.get("/{project_id}/chapters/{chapter_id}")
async def get_chapter_content(project_id: str, chapter_id: str, db: AsyncSession = Depends(get_db)):
    """获取章节内容"""
    # 验证项目存在
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chapter = await get_chapter_by_id(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    return {
        "id": chapter.chapter_id,
        "project_id": project_id,
        "title": chapter.title,
        "content": chapter.content,
        "order": chapter.order_index,
        "word_count": chapter.word_count,
        "summary": chapter.summary,
        "notes": chapter.notes,
        "created_at": chapter.created_at,
        "updated_at": chapter.updated_at,
    }


@router.post("/{project_id}/chapters")
async def create_new_chapter(
    project_id: str,
    title: str = Body(..., embed=True),
    content: str = Body("", embed=True),
    order: Optional[int] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db)
):
    """创建新章节"""
    # 验证项目存在
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 如果没有指定顺序，自动设置为下一章
    if order is None:
        chapters = await list_chapters(db, project_id)
        order = len(chapters) + 1

    chapter_id = str(uuid.uuid4())

    chapter = await create_chapter(
        db=db,
        chapter_id=chapter_id,
        project_id=project_id,
        title=title,
        content=content,
        order_index=order,
    )
    await db.commit()

    return {
        "id": chapter.chapter_id,
        "project_id": project_id,
        "title": chapter.title,
        "content": chapter.content,
        "order": chapter.order_index,
        "word_count": chapter.word_count,
        "created_at": chapter.created_at,
        "updated_at": chapter.updated_at,
    }


@router.put("/{project_id}/chapters/{chapter_id}")
async def update_chapter_content(
    project_id: str,
    chapter_id: str,
    title: Optional[str] = Body(None, embed=True),
    content: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db)
):
    """更新章节内容"""
    # 验证项目存在
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chapter = await update_chapter(
        db=db,
        chapter_id=chapter_id,
        title=title,
        content=content,
        create_version=True,  # 自动创建版本历史
        change_description="Manual update via API",
    )

    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    await db.commit()

    # 刷新以确保所有属性已加载
    await db.refresh(chapter)

    return {
        "id": chapter.chapter_id,
        "project_id": project_id,
        "title": chapter.title,
        "content": chapter.content,
        "order": chapter.order_index,
        "word_count": chapter.word_count,
        "created_at": chapter.created_at,
        "updated_at": chapter.updated_at,
    }


@router.delete("/{project_id}/chapters/{chapter_id}")
async def delete_chapter_endpoint(project_id: str, chapter_id: str, db: AsyncSession = Depends(get_db)):
    """删除章节"""
    # 验证项目存在
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    success = await delete_chapter(db, chapter_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chapter not found")

    await db.commit()
    return {"message": "Chapter deleted"}
