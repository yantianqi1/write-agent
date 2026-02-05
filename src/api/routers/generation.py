"""
内容生成API路由

处理小说内容生成请求
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
import uuid
from datetime import datetime

from ..models.generation import GenerationRequest, GenerationResponse, GenerationMode
from ..models.project import ChapterInfo
from ...story.generation.content_generator import StoryGenerator, create_story_generator
from ...story.llm import create_llm_provider

router = APIRouter(prefix="/api/v1/generate", tags=["generation"])

# Storage for generation status (in production, use Redis)
_generation_status: dict = {}


def get_project_chapters(project_id: str) -> list:
    """Get project chapters (shared with projects router)"""
    # This would be shared storage in production
    import sys
    sys.path.append("/root/write-agent/src/api/routers")
    from .projects import _chapters
    return _chapters.get(project_id, [])


@router.post("/chapter", response_model=GenerationResponse)
async def generate_chapter(request: GenerationRequest, background_tasks: BackgroundTasks):
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
        # Import here to avoid circular imports
        import sys
        sys.path.append("/root/write-agent/src/api/routers")
        from .projects import _chapters, _projects

        if request.project_id not in _projects:
            raise HTTPException(status_code=404, detail="Project not found")

        # Create LLM provider and generator
        llm_provider = create_llm_provider()
        generator = create_story_generator(llm_provider)

        # Get existing chapters to determine order
        chapters = _chapters.get(request.project_id, [])
        next_order = len(chapters) + 1

        # For demo, generate mock content if LLM is not configured
        if request.mode == GenerationMode.CONTINUE or request.mode == GenerationMode.FULL:
            chapter_title = f"第{next_order}章"
            content = _generate_mock_content(request.project_id, next_order)
            word_count = len(content)
        else:
            chapter_title = f"第{next_order}章"
            content = _generate_mock_content(request.project_id, next_order)
            word_count = len(content)

        # Create chapter
        chapter_id = str(uuid.uuid4())
        now = datetime.now()

        new_chapter = {
            "id": chapter_id,
            "project_id": request.project_id,
            "title": chapter_title,
            "content": content,
            "order": next_order,
            "word_count": word_count,
            "created_at": now,
            "updated_at": now,
        }

        # Store chapter
        if request.project_id not in _chapters:
            _chapters[request.project_id] = []
        _chapters[request.project_id].append(new_chapter)

        # Update project word count
        _projects[request.project_id]["word_count"] = sum(
            ch["word_count"] for ch in _chapters[request.project_id]
        )
        _projects[request.project_id]["updated_at"] = now

        return GenerationResponse(
            chapter_id=chapter_id,
            content=content,
            word_count=word_count,
            generation_mode=request.mode,
            metadata={"chapter_title": chapter_title, "order": next_order}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


def _generate_mock_content(project_id: str, chapter_num: int) -> str:
    """生成模拟内容（用于演示）"""
    return f"""# 第{chapter_num}章

这是一个示例章节。在实际部署中，这里会调用真实的LLM来生成内容。

---

飞船的警报声已经停止了，取而代之的是死一般的寂静。

李明从昏迷中醒来，第一感觉是冷。刺骨的寒冷透过宇航服渗入骨髓，他努力睁开眼睛，看到的只有漆黑的太空和闪烁的星光。

"有人吗？"他试图通过通讯系统呼叫，但回应他的只有沙沙的静电噪音。

他费力地解开安全带，飘浮在失重的驾驶舱内。各种指示灯在黑暗中闪烁，大多是红色的警告灯。主引擎已经彻底损坏，备用系统也只剩下最基本的维生功能还在运转。

李明飘向舷窗，向外望去。远处，一颗蓝色的星球静静地悬浮在黑暗中。那是他的目的地，也是他现在唯一的希望。

*（这是第{chapter_num}章的示例内容。完整的实现需要配置LLM API密钥。）*
"""


@router.get("/status/{generation_id}")
async def get_generation_status(generation_id: str):
    """获取生成任务状态"""
    if generation_id not in _generation_status:
        raise HTTPException(status_code=404, detail="Generation not found")

    return _generation_status[generation_id]
