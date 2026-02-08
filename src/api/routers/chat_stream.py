"""
聊天API路由 - 流式响应版本

处理与AI创作助手的对话交互，使用Server-Sent Events (SSE)实现流式响应
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Optional
import uuid
import json
import asyncio

from ..models.chat import ChatRequest, Message, MessageRole
from ...story.llm import create_llm_provider, LLMRequest, Message as LLMMessage, MessageRole as LLMMessageRole
from ..database import get_db
from ..database.crud import (
    create_session,
    get_session_by_id,
    create_message,
    get_session_messages,
)
from ..cache.session_history import get_session_history_manager
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/chat/stream", tags=["chat-stream"])

# 全局 LLM provider 缓存
_llm_provider = None

# 共享的会话历史管理器
_history_manager = get_session_history_manager()


def get_llm_provider():
    """获取或创建 LLM provider"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = create_llm_provider()
    return _llm_provider


def get_session_history(session_id: str) -> list[LLMMessage]:
    """获取会话历史"""
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


async def _stream_chat_response(
    messages: list[LLMMessage],
    session_id: str
) -> AsyncGenerator[str, None]:
    """
    流式生成聊天响应

    Yields SSE formatted data chunks
    """
    llm = get_llm_provider()
    llm_request = LLMRequest(
        messages=messages,
        temperature=0.8,
        max_tokens=2000,
    )

    full_response = ""
    chunk_id = 0

    try:
        # 使用 LLM 的 stream 方法
        async for stream_chunk in llm.stream(llm_request):
            if stream_chunk.is_final:
                # 发送完成标记
                data = {
                    "type": "done",
                    "session_id": session_id,
                    "full_content": full_response
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                break

            full_response += stream_chunk.content
            chunk_id += 1

            # 发送内容块
            data = {
                "type": "content",
                "chunk_id": chunk_id,
                "content": stream_chunk.content,
                "session_id": session_id
            }
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            # 小延迟以防止过快发送
            await asyncio.sleep(0.01)

    except Exception as e:
        # 发送错误信息
        error_data = {
            "type": "error",
            "error": str(e),
            "session_id": session_id
        }
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"


@router.post("/")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    处理聊天消息 - 流式响应

    使用Server-Sent Events (SSE)实时推送AI回复内容。
    客户端会持续收到内容块，直到收到type="done"的消息。
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

        # 收集完整响应用于后续处理
        response_buffer = []

        async def stream_generator():
            """生成流式响应的内部生成器"""
            async for chunk in _stream_chat_response(messages, session_id):
                response_buffer.append(chunk)
                yield chunk

            # 流结束后，保存助手消息到数据库
            if db_session:
                # 从缓冲区提取完整内容
                full_content = ""
                for chunk in response_buffer:
                    if chunk.startswith("data: "):
                        try:
                            data = json.loads(chunk[6:])
                            if data.get("type") == "content":
                                full_content += data.get("content", "")
                            elif data.get("type") == "done":
                                full_content = data.get("full_content", full_content)
                        except json.JSONDecodeError:
                            pass

                if full_content:
                    await create_message(db, db_session.id, MessageRole.ASSISTANT, full_content)
                    await db.commit()

                # 添加到历史
                add_to_history(session_id, LLMMessageRole.USER, request.message)
                add_to_history(session_id, LLMMessageRole.ASSISTANT, full_content)

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
            }
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Chat streaming failed: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """删除对话会话"""
    from ..routers.chat import delete_session as delete_session_db
    success = await delete_session_db(db, session_id)
    if success:
        # 从缓存中移除
        clear_session_history(session_id)
        await db.commit()
        return {"message": "Session deleted"}

    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/admin/cache-stats")
async def get_cache_stats():
    """获取流式聊天缓存统计信息（管理员接口）"""
    stats = _history_manager.get_stats()
    return {
        "cached_sessions": stats["session_ids"],
        "cache_size": stats["total_sessions"],
        "total_messages": stats["total_messages"],
    }


@router.post("/admin/cleanup-cache")
async def cleanup_cache():
    """清理所有缓存（管理员接口）"""
    global _llm_provider
    _history_manager.clear_all()
    _llm_provider = None
    return {"message": "Cache cleared"}
