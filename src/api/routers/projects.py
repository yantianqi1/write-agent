"""
项目管理API路由

处理小说项目的CRUD操作
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict
import uuid
from datetime import datetime

from ..models.project import (
    ProjectInfo,
    ProjectCreate,
    ProjectUpdate,
    ChapterInfo,
)

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

# In-memory storage (in production, use database)
_projects: Dict[str, Dict] = {}
_chapters: Dict[str, List[Dict]] = {}


@router.get("/", response_model=List[ProjectInfo])
async def list_projects():
    """获取所有项目列表"""
    projects = []
    for project_id, project in _projects.items():
        projects.append(ProjectInfo(
            id=project_id,
            title=project["title"],
            description=project.get("description"),
            genre=project.get("genre"),
            status=project.get("status", "draft"),
            created_at=project["created_at"],
            updated_at=project["updated_at"],
            word_count=project.get("word_count", 0),
            chapter_count=len(_chapters.get(project_id, [])),
        ))
    return projects


@router.get("/{project_id}", response_model=ProjectInfo)
async def get_project(project_id: str):
    """获取单个项目详情"""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")

    project = _projects[project_id]
    return ProjectInfo(
        id=project_id,
        title=project["title"],
        description=project.get("description"),
        genre=project.get("genre"),
        status=project.get("status", "draft"),
        created_at=project["created_at"],
        updated_at=project["updated_at"],
        word_count=project.get("word_count", 0),
        chapter_count=len(_chapters.get(project_id, [])),
    )


@router.post("/", response_model=ProjectInfo)
async def create_project(request: ProjectCreate):
    """创建新项目"""
    project_id = str(uuid.uuid4())
    now = datetime.now()

    _projects[project_id] = {
        "title": request.title,
        "description": request.description,
        "genre": request.genre,
        "status": "draft",
        "created_at": now,
        "updated_at": now,
        "word_count": 0,
    }
    _chapters[project_id] = []

    return ProjectInfo(
        id=project_id,
        title=request.title,
        description=request.description,
        genre=request.genre,
        status="draft",
        created_at=now,
        updated_at=now,
        word_count=0,
        chapter_count=0,
    )


@router.put("/{project_id}", response_model=ProjectInfo)
async def update_project(project_id: str, request: ProjectUpdate):
    """更新项目信息"""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")

    project = _projects[project_id]

    if request.title is not None:
        project["title"] = request.title
    if request.description is not None:
        project["description"] = request.description
    if request.genre is not None:
        project["genre"] = request.genre
    if request.status is not None:
        project["status"] = request.status

    project["updated_at"] = datetime.now()

    return ProjectInfo(
        id=project_id,
        title=project["title"],
        description=project.get("description"),
        genre=project.get("genre"),
        status=project.get("status", "draft"),
        created_at=project["created_at"],
        updated_at=project["updated_at"],
        word_count=project.get("word_count", 0),
        chapter_count=len(_chapters.get(project_id, [])),
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")

    del _projects[project_id]
    if project_id in _chapters:
        del _chapters[project_id]

    return {"message": "Project deleted"}


@router.get("/{project_id}/chapters", response_model=List[ChapterInfo])
async def list_chapters(project_id: str):
    """获取项目的所有章节"""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")

    chapters = _chapters.get(project_id, [])
    return [
        ChapterInfo(
            id=ch["id"],
            project_id=project_id,
            title=ch["title"],
            order=ch["order"],
            word_count=ch["word_count"],
            created_at=ch["created_at"],
            updated_at=ch["updated_at"],
        )
        for ch in chapters
    ]


@router.get("/{project_id}/chapters/{chapter_id}")
async def get_chapter(project_id: str, chapter_id: str):
    """获取章节内容"""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")

    chapters = _chapters.get(project_id, [])
    for ch in chapters:
        if ch["id"] == chapter_id:
            return {
                "id": ch["id"],
                "project_id": project_id,
                "title": ch["title"],
                "content": ch["content"],
                "order": ch["order"],
                "word_count": ch["word_count"],
                "created_at": ch["created_at"],
                "updated_at": ch["updated_at"],
            }

    raise HTTPException(status_code=404, detail="Chapter not found")
