"""
内容生成API路由

处理小说内容生成请求
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Optional
import uuid

from ..models.generation import GenerationRequest, GenerationResponse, GenerationMode
from ...story.llm import create_llm_provider, LLMRequest, Message, MessageRole
from ..database import get_db
from ..database.crud import (
    get_project_by_id,
    list_chapters,
    create_chapter,
    create_generation_task,
    get_generation_task_by_id,
    update_generation_task_status,
    list_generation_tasks,
)
from ..database.models import TaskStatus
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/generate", tags=["generation"])


# 全局 LLM provider 缓存
_llm_provider = None


def get_llm_provider():
    """获取或创建 LLM provider"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = create_llm_provider()
    return _llm_provider


def _build_generation_prompt(project, chapter_order: int, previous_chapters: list, mode: str, user_prompt: str = "") -> tuple[str, str]:
    """
    构建生成提示词

    Returns:
        (system_prompt, user_prompt)
    """
    # 获取项目信息
    title = project.title
    description = project.description if hasattr(project, 'description') and project.description else ""
    genre = project.genre if hasattr(project, 'genre') and project.genre else "小说"

    # 构建系统提示
    system_prompt = f"""你是一位专业的小说作家，擅长创作引人入胜的故事。

你的任务是：
1. 严格遵循提供的故事设定和世界观
2. 保持角色性格和行为的一致性
3. 创作生动、富有画面感的场景描写
4. 编写自然流畅的对话
5. 保持情节的逻辑连贯性

写作要求：
- 篇幅：1500-2500字
- 风格：{genre}
- 叙述角度：第三人称
- 时态：过去时

请直接输出小说正文，不要包含任何说明或元信息。"""

    # 构建用户提示
    context_parts = [
        f"小说标题：{title}",
        f"类型：{genre}",
    ]

    if description:
        context_parts.append(f"故事简介：{description}")

    context_parts.append(f"章节：第{chapter_order}章")

    # 添加前文摘要
    if previous_chapters:
        prev_summary = previous_chapters[-1].content[-300:] if previous_chapters[-1].content else ""
        if prev_summary:
            context_parts.append(f"前文概要（最后300字）：\n{prev_summary}")

    # 根据模式添加指令
    mode_instructions = {
        "full": "请创作这一章的完整内容",
        "continue": "请续写上一章的内容",
        "expand": f"请扩写以下内容：{user_prompt}",
        "rewrite": f"请重写以下内容：{user_prompt}",
        "outline": "请为这一章生成大纲"
    }

    context_parts.append(mode_instructions.get(mode, "请创作这一章的完整内容"))

    if user_prompt and mode not in ["expand", "rewrite"]:
        context_parts.append(f"额外要求：{user_prompt}")

    user_prompt_text = "\n\n".join(context_parts)

    return system_prompt, user_prompt_text


@router.post("/chapter", response_model=GenerationResponse)
async def generate_chapter(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    生成章节内容

    支持多种生成模式：
    - full: 完整生成新章节
    - continue: 续写上一章
    - expand: 扩写指定内容
    - rewrite: 重写指定章节
    - outline: 生成大纲
    """
    try:
        # 验证项目存在
        project = await get_project_by_id(db, request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 创建生成任务记录
        task_id = str(uuid.uuid4())
        task = await create_generation_task(
            db=db,
            task_id=task_id,
            project_id=request.project_id,
            mode=request.mode,
            chapter_id=request.chapter_id,
            prompt=request.prompt,
        )
        await db.commit()

        # 获取现有章节以确定顺序
        chapters = await list_chapters(db, request.project_id)
        next_order = len(chapters) + 1

        # 如果是续写模式，获取上一章内容
        previous_chapters = []
        if request.mode.value == "continue" and chapters:
            previous_chapters = chapters
            next_order = len(chapters)  # 继续上一章

        # 使用真实 LLM 生成内容
        llm = get_llm_provider()
        system_prompt, user_prompt = _build_generation_prompt(
            project, next_order, previous_chapters, request.mode.value, request.prompt or ""
        )

        # 构建请求
        llm_request = LLMRequest(
            messages=[
                Message(role=MessageRole.SYSTEM, content=system_prompt),
                Message(role=MessageRole.USER, content=user_prompt)
            ],
            temperature=0.8,
            max_tokens=4000,
        )

        # 调用 LLM - 使用异步方法避免阻塞事件循环
        llm_response = await llm.generate_async(llm_request)
        content = llm_response.content.strip()
        word_count = len(content)

        # 生成章节标题
        chapter_title = f"第{next_order}章"
        # 尝试从内容中提取标题
        for line in content.split('\n')[:5]:
            line = line.strip()
            if line.startswith('#') or line.startswith('第') and '章' in line:
                chapter_title = line.lstrip('#').strip()
                break

        # 创建章节
        chapter_id = str(uuid.uuid4())

        chapter = await create_chapter(
            db=db,
            chapter_id=chapter_id,
            project_id=request.project_id,
            title=chapter_title,
            content=content,
            order_index=next_order,
        )

        # 更新任务状态为完成
        await update_generation_task_status(
            db=db,
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            result={
                "chapter_id": chapter_id,
                "chapter_title": chapter_title,
                "word_count": word_count,
                "order": next_order,
                "model": llm_response.model,
                "tokens_used": llm_response.usage.get("total_tokens", 0),
            }
        )
        await db.commit()

        return GenerationResponse(
            chapter_id=chapter_id,
            content=content,
            word_count=word_count,
            generation_mode=request.mode,
            metadata={
                "task_id": task_id,
                "chapter_title": chapter_title,
                "order": next_order,
                "model": llm_response.model,
                "tokens_used": llm_response.usage.get("total_tokens", 0),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        # 更新任务状态为失败
        if 'task_id' in locals():
            try:
                await update_generation_task_status(
                    db=db,
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error_message=str(e),
                )
                await db.commit()
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get("/status/{generation_id}")
async def get_generation_status(generation_id: str, db: AsyncSession = Depends(get_db)):
    """获取生成任务状态"""
    task = await get_generation_task_by_id(db, generation_id)
    if not task:
        raise HTTPException(status_code=404, detail="Generation not found")

    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "mode": task.mode.value,
        "chapter_id": task.chapter_id,
        "result": task.result,
        "error_message": task.error_message,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
    }


@router.get("/tasks")
async def list_generation_tasks(
    project_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """列出生成任务"""
    # 验证项目存在
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 转换状态
    task_status = None
    if status:
        try:
            task_status = TaskStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    tasks = await list_generation_tasks(
        db=db,
        project_id=project_id,
        status=task_status,
        limit=limit
    )

    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "status": t.status.value,
                "mode": t.mode.value,
                "chapter_id": t.chapter_id,
                "created_at": t.created_at,
                "started_at": t.started_at,
                "completed_at": t.completed_at,
            }
            for t in tasks
        ]
    }


@router.post("/reset")
async def reset_generation_cache():
    """重置生成器缓存（管理员）"""
    global _llm_provider
    _llm_provider = None
    return {"message": "Generation cache reset"}
