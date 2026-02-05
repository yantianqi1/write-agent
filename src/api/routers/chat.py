"""
聊天API路由

处理与AI创作助手的对话交互
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
import uuid

from ..models.chat import ChatRequest, ChatResponse, Message, MessageRole
from ...story.setting_extractor.conversational_agent import create_agent, ConversationalAgent

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Session storage (in production, use Redis or database)
_sessions: Dict[str, ConversationalAgent] = {}


def get_agent(session_id: Optional[str]) -> ConversationalAgent:
    """获取或创建对话agent"""
    if not session_id or session_id not in _sessions:
        agent = create_agent(agent_type="streamlined", auto_complete=True, min_readiness=0.2)
        new_session_id = session_id or str(uuid.uuid4())
        _sessions[new_session_id] = agent
        return agent, new_session_id
    return _sessions[session_id], session_id


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    处理聊天消息

    通过自然对话与AI创作助手交互，AI会隐式提取故事设定并决定何时开始创作。
    """
    try:
        # Get or create agent for this session
        agent, session_id = get_agent(request.session_id)

        # Process the user message
        response = agent.process(request.message)

        # Create chat message for response
        chat_message = Message(
            role=MessageRole.ASSISTANT,
            content=response.message
        )

        return ChatResponse(
            message=chat_message,
            session_id=session_id,
            should_create=response.should_create,
            metadata={
                "confidence": response.confidence,
                "readiness_score": response.metadata.get("readiness_score", 0) if response.metadata else 0,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.get("/sessions/{session_id}/summary")
async def get_session_summary(session_id: str):
    """获取对话会话摘要"""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = _sessions[session_id]
    summary = agent.get_conversation_summary()
    summary["session_id"] = session_id

    return summary


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除对话会话"""
    if session_id in _sessions:
        del _sessions[session_id]
        return {"message": "Session deleted"}
    return {"message": "Session not found"}
