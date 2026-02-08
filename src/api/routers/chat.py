"""
聊天API路由

处理与AI创作助手的对话交互
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
import uuid
import time

from ..models.chat import ChatRequest, ChatResponse, Message, MessageRole
from ...story.llm import create_llm_provider, LLMRequest, Message as LLMMessage, MessageRole as LLMMessageRole
from ..database import get_db
from ..database.crud import (
    create_session,
    get_session_by_id,
    delete_session as delete_session_db,
    update_session,
    create_message,
    get_session_messages,
    list_sessions,
)
from ..cache.lru_session_cache import get_session_cache
from ..cache.session_history import get_session_history_manager
from ..middleware import get_metrics
from sqlalchemy.ext.asyncio import AsyncSession
from ...story.llm import Message as LLMMessage, MessageRole as LLMMessageRole

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# 全局 LLM provider 缓存
_llm_provider = None

# LRU 会话缓存实例
_session_cache = get_session_cache()

# 共享的会话历史管理器
_history_manager = get_session_history_manager()


def get_llm_provider():
    """获取或创建 LLM provider"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = create_llm_provider()
    return _llm_provider


def get_session_history(session_id: str) -> list[LLMMessage]:
    """获取会话历史（使用共享历史管理器）"""
    return _history_manager.get_history(session_id)


def add_to_history(session_id: str, role: LLMMessageRole, content: str) -> None:
    """添加消息到历史"""
    _history_manager.add_message(session_id, role, content)


def clear_session_history(session_id: str) -> None:
    """清除会话历史"""
    _history_manager.clear_session(session_id)


# 系统提示模板
SYSTEM_PROMPT = """你是一位专业的小说创作助手，擅长通过对话帮助用户创作小说。

你的核心能力：
1. 通过自然对话了解用户想要创作的故事类型、风格和情节
2. 帮助用户构思角色设定、世界观和故事大纲
3. 根据用户要求生成小说章节内容
4. 协助修改和润色已写的内容

对话风格：
- 友好、专业、富有启发性
- 主动提问了解用户需求
- 给出建设性的创作建议
- 适当的时候可以主动开始创作

注意事项：
- 不要让用户觉得在"填写设定表单"，而是自然聊天
- 当信息足够时，可以主动提议开始创作
- 保持创作热情和正能量"""


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    处理聊天消息

    通过自然对话与AI创作助手交互，AI会帮助用户进行小说创作。
    """
    try:
        # 获取或创建会话ID
        session_id = request.session_id or str(uuid.uuid4())

        # 获取数据库会话对象
        db_session = await get_session_by_id(db, session_id)
        if not db_session:
            # 创建新的数据库会话记录
            db_session = await create_session(db, session_id, project_id=request.project_id)

        # 保存用户消息到数据库
        if db_session:
            await create_message(db, db_session.id, MessageRole.USER, request.message)

        # 获取对话历史
        history = get_session_history(session_id)

        # 构建 LLM 请求
        messages = [
            LLMMessage(role=LLMMessageRole.SYSTEM, content=SYSTEM_PROMPT)
        ]

        # 添加历史消息
        messages.extend(history[-10:])  # 只取最近10条历史

        # 添加当前用户消息
        messages.append(LLMMessage(role=LLMMessageRole.USER, content=request.message))

        # 调用 LLM - 使用异步方法避免阻塞事件循环
        llm = get_llm_provider()
        llm_request = LLMRequest(
            messages=messages,
            temperature=0.8,
            max_tokens=2000,
        )

        # 使用异步调用，避免阻塞
        llm_response = await llm.generate_async(llm_request)
        response_text = llm_response.content.strip()

        # 添加到历史
        add_to_history(session_id, LLMMessageRole.USER, request.message)
        add_to_history(session_id, LLMMessageRole.ASSISTANT, response_text)

        # 保存助手消息到数据库
        if db_session:
            await create_message(db, db_session.id, MessageRole.ASSISTANT, response_text)

        await db.commit()

        # 创建响应消息
        chat_message = Message(
            role=MessageRole.ASSISTANT,
            content=response_text
        )

        # 分析是否应该开始创作（简单判断）
        should_create = any(keyword in response_text for keyword in
                           ["让我写", "开始创作", "生成章节", "来写一段"])

        return ChatResponse(
            message=chat_message,
            session_id=session_id,
            should_create=should_create,
            metadata={
                "model": llm_response.model,
                "tokens_used": llm_response.usage.get("total_tokens", 0),
                "confidence": 0.9,
            }
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.get("/sessions/{session_id}/summary")
async def get_session_summary(session_id: str, db: AsyncSession = Depends(get_db)):
    """获取对话会话摘要"""
    db_session = await get_session_by_id(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 获取消息历史
    messages = await get_session_messages(db, db_session.id)

    # 统计信息
    user_messages = [m for m in messages if m.role == MessageRole.USER]
    assistant_messages = [m for m in messages if m.role == MessageRole.ASSISTANT]

    return {
        "session_id": session_id,
        "title": db_session.title,
        "project_id": db_session.project_id,
        "message_count": len(messages),
        "user_message_count": len(user_messages),
        "assistant_message_count": len(assistant_messages),
        "created_at": db_session.created_at,
        "updated_at": db_session.updated_at,
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """删除对话会话"""
    success = await delete_session_db(db, session_id)
    if success:
        # 从 LRU 缓存中移除
        _session_cache.delete(session_id)
        # 从会话历史中移除
        _history_manager.clear_session(session_id)
        await db.commit()
        return {"message": "Session deleted"}

    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/sessions")
async def list_sessions_endpoint(
    project_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """列出所有会话"""
    sessions = await list_sessions(
        db=db,
        project_id=project_id,
        limit=limit
    )
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "title": s.title,
                "project_id": s.project_id,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in sessions
        ]
    }


@router.get("/admin/cache-stats")
async def get_cache_stats():
    """获取会话缓存统计信息（管理员接口）"""
    return _session_cache.get_stats()


@router.get("/admin/cache/{session_id}")
async def get_session_cache_info(session_id: str):
    """获取特定会话的缓存信息（管理员接口）"""
    info = _session_cache.get_session_info(session_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Session not in cache")
    return info


@router.post("/admin/cleanup-cache")
async def cleanup_cache():
    """清理所有缓存（管理员接口）"""
    global _llm_provider
    _session_cache.clear()
    _history_manager.clear_all()
    _llm_provider = None
    return {"message": "Cache cleared"}


@router.get("/admin/metrics")
async def get_admin_metrics():
    """获取系统性能指标（管理员接口）"""
    metrics = get_metrics()
    return metrics.get_metrics()
