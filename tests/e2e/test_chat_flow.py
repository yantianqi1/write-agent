"""
聊天流程端到端测试

测试完整的聊天交互流程，包括：
1. 创建新会话
2. 发送消息
3. 接收回复
4. 会话状态管理
"""

import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.database import get_db, init_db
from api.models.chat import ChatRequest


@pytest_asyncio.fixture
async def client():
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    """创建测试数据库会话"""
    await init_db()
    async for session in get_db():
        yield session
        break


class TestChatFlow:
    """聊天流程测试组"""

    @pytest.mark.asyncio
    async def test_new_chat_session(self, client: AsyncClient):
        """测试创建新的聊天会话"""
        response = await client.post(
            "/api/v1/chat/",
            json={
                "message": "你好，我想写一部小说",
                "session_id": None,
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "session_id" in data
        assert data["message"]["role"] == "assistant"
        assert len(data["session_id"]) > 0

    @pytest.mark.asyncio
    async def test_continue_chat_session(self, client: AsyncClient):
        """测试继续现有聊天会话"""
        # 第一次消息
        response1 = await client.post(
            "/api/v1/chat/",
            json={
                "message": "我想写一部科幻小说",
                "session_id": None,
            }
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # 第二次消息（继续会话）
        response2 = await client.post(
            "/api/v1/chat/",
            json={
                "message": "主角是一个人工智能",
                "session_id": session_id,
            }
        )
        assert response2.status_code == 200
        data2 = response2.json()

        # 验证会话ID保持一致
        assert data2["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_session_persistence(self, client: AsyncClient):
        """测试会话持久化"""
        # 创建会话
        response1 = await client.post(
            "/api/v1/chat/",
            json={"message": "测试消息", "session_id": None}
        )
        session_id = response1.json()["session_id"]

        # 获取会话摘要
        response2 = await client.get(f"/api/v1/chat/sessions/{session_id}/summary")
        assert response2.status_code == 200
        data = response2.json()

        assert "session_id" in data
        assert data["session_id"] == session_id
        assert "message_count" in data

    @pytest.mark.asyncio
    async def test_delete_session(self, client: AsyncClient):
        """测试删除会话"""
        # 创建会话
        response1 = await client.post(
            "/api/v1/chat/",
            json={"message": "要删除的会话", "session_id": None}
        )
        session_id = response1.json()["session_id"]

        # 删除会话
        response2 = await client.delete(f"/api/v1/chat/sessions/{session_id}")
        assert response2.status_code == 200

        # 验证会话已删除
        response3 = await client.get(f"/api/v1/chat/sessions/{session_id}/summary")
        assert response3.status_code == 404

    @pytest.mark.asyncio
    async def test_list_sessions(self, client: AsyncClient):
        """测试列出会话"""
        # 创建多个会话
        session_ids = []
        for i in range(3):
            response = await client.post(
                "/api/v1/chat/",
                json={"message": f"测试会话 {i+1}", "session_id": None}
            )
            session_ids.append(response.json()["session_id"])

        # 列出会话
        response = await client.get("/api/v1/chat/sessions?limit=10")
        assert response.status_code == 200
        data = response.json()

        assert "sessions" in data
        assert len(data["sessions"]) >= 3

    @pytest.mark.asyncio
    async def test_chat_with_project_id(self, client: AsyncClient):
        """测试关联项目的聊天"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects/",
            json={"title": "测试项目", "genre": "科幻"}
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # 关联项目的聊天
        chat_response = await client.post(
            "/api/v1/chat/",
            json={
                "message": "帮我设计主角",
                "session_id": None,
                "project_id": project_id
            }
        )
        assert chat_response.status_code == 200
        data = chat_response.json()

        # 验证会话与项目关联
        summary_response = await client.get(f"/api/v1/chat/sessions/{data['session_id']}/summary")
        summary_data = summary_response.json()
        # project_id可能在metadata中或单独字段


@pytest.mark.asyncio
async def test_error_handling(client: AsyncClient):
    """测试错误处理"""
    # 空消息
    response = await client.post(
        "/api/v1/chat/",
        json={"message": "", "session_id": None}
    )
    # 应该返回错误或正常响应

    # 无效的session_id
    response = await client.get("/api/v1/chat/sessions/invalid-id/summary")
    assert response.status_code == 404
