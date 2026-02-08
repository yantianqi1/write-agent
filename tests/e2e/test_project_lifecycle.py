"""
项目生命周期端到端测试

测试项目的完整生命周期：
1. 创建项目
2. 更新项目
3. 创建章节
4. 更新章节
5. 删除章节
6. 删除项目
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.database import init_db, get_db


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


class TestProjectLifecycle:
    """项目生命周期测试组"""

    @pytest.mark.asyncio
    async def test_create_project(self, client: AsyncClient):
        """测试创建项目"""
        response = await client.post(
            "/api/v1/projects/",
            json={
                "title": "测试小说",
                "description": "这是一部测试小说",
                "genre": "科幻"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "测试小说"
        assert data["description"] == "这是一部测试小说"
        assert data["genre"] == "科幻"
        assert data["status"] == "draft"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_list_projects(self, client: AsyncClient):
        """测试列出项目"""
        # 创建几个项目
        for i in range(3):
            await client.post(
                "/api/v1/projects/",
                json={"title": f"测试项目 {i+1}", "genre": "奇幻"}
            )

        # 列出项目
        response = await client.get("/api/v1/projects/")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_get_project(self, client: AsyncClient):
        """测试获取单个项目"""
        # 创建项目
        create_response = await client.post(
            "/api/v1/projects/",
            json={"title": "获取测试项目", "genre": "武侠"}
        )
        project_id = create_response.json()["id"]

        # 获取项目
        response = await client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == project_id
        assert data["title"] == "获取测试项目"

    @pytest.mark.asyncio
    async def test_update_project(self, client: AsyncClient):
        """测试更新项目"""
        # 创建项目
        create_response = await client.post(
            "/api/v1/projects/",
            json={"title": "更新前", "genre": "科幻"}
        )
        project_id = create_response.json()["id"]

        # 更新项目
        update_response = await client.put(
            f"/api/v1/projects/{project_id}",
            json={"title": "更新后", "status": "in_progress"}
        )
        assert update_response.status_code == 200
        data = update_response.json()

        assert data["title"] == "更新后"
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_delete_project(self, client: AsyncClient):
        """测试删除项目"""
        # 创建项目
        create_response = await client.post(
            "/api/v1/projects/",
            json={"title": "待删除项目", "genre": "历史"}
        )
        project_id = create_response.json()["id"]

        # 删除项目
        delete_response = await client.delete(f"/api/v1/projects/{project_id}")
        assert delete_response.status_code == 200

        # 验证已删除
        get_response = await client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_chapter(self, client: AsyncClient):
        """测试创建章节"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects/",
            json={"title": "章节测试项目", "genre": "科幻"}
        )
        project_id = project_response.json()["id"]

        # 创建章节
        chapter_response = await client.post(
            f"/api/v1/projects/{project_id}/chapters",
            json={
                "title": "第一章：开始",
                "content": "这是第一章的内容...",
                "order": 1
            }
        )
        assert chapter_response.status_code == 200
        data = chapter_response.json()

        assert data["title"] == "第一章：开始"
        assert data["content"] == "这是第一章的内容..."
        assert data["order"] == 1

    @pytest.mark.asyncio
    async def test_list_chapters(self, client: AsyncClient):
        """测试列出章节"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects/",
            json={"title": "多章节项目", "genre": "科幻"}
        )
        project_id = project_response.json()["id"]

        # 创建多个章节
        for i in range(3):
            await client.post(
                f"/api/v1/projects/{project_id}/chapters",
                json={"title": f"第{i+1}章", "content": f"内容{i+1}"}
            )

        # 列出章节
        response = await client.get(f"/api/v1/projects/{project_id}/chapters")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_get_chapter(self, client: AsyncClient):
        """测试获取章节内容"""
        # 创建项目和章节
        project_response = await client.post(
            "/api/v1/projects/",
            json={"title": "获取章节项目", "genre": "科幻"}
        )
        project_id = project_response.json()["id"]

        chapter_response = await client.post(
            f"/api/v1/projects/{project_id}/chapters",
            json={"title": "测试章节", "content": "章节内容"}
        )
        chapter_id = chapter_response.json()["id"]

        # 获取章节
        response = await client.get(
            f"/api/v1/projects/{project_id}/chapters/{chapter_id}"
        )
        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "测试章节"
        assert data["content"] == "章节内容"

    @pytest.mark.asyncio
    async def test_update_chapter(self, client: AsyncClient):
        """测试更新章节"""
        # 创建项目和章节
        project_response = await client.post(
            "/api/v1/projects/",
            json={"title": "更新章节项目", "genre": "科幻"}
        )
        project_id = project_response.json()["id"]

        chapter_response = await client.post(
            f"/api/v1/projects/{project_id}/chapters",
            json={"title": "原标题", "content": "原内容"}
        )
        chapter_id = chapter_response.json()["id"]

        # 更新章节
        update_response = await client.put(
            f"/api/v1/projects/{project_id}/chapters/{chapter_id}",
            json={"title": "新标题", "content": "新内容"}
        )
        assert update_response.status_code == 200
        data = update_response.json()

        assert data["title"] == "新标题"
        assert data["content"] == "新内容"

    @pytest.mark.asyncio
    async def test_delete_chapter(self, client: AsyncClient):
        """测试删除章节"""
        # 创建项目和章节
        project_response = await client.post(
            "/api/v1/projects/",
            json={"title": "删除章节项目", "genre": "科幻"}
        )
        project_id = project_response.json()["id"]

        chapter_response = await client.post(
            f"/api/v1/projects/{project_id}/chapters",
            json={"title": "待删除章节", "content": "内容"}
        )
        chapter_id = chapter_response.json()["id"]

        # 删除章节
        delete_response = await client.delete(
            f"/api/v1/projects/{project_id}/chapters/{chapter_id}"
        )
        assert delete_response.status_code == 200

        # 验证已删除
        get_response = await client.get(
            f"/api/v1/projects/{project_id}/chapters/{chapter_id}"
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_word_count_updates(self, client: AsyncClient):
        """测试字数统计更新"""
        # 创建项目
        project_response = await client.post(
            "/api/v1/projects/",
            json={"title": "字数统计项目", "genre": "科幻"}
        )
        project_id = project_response.json()["id"]

        # 创建章节
        content = "这是一段测试内容，用于验证字数统计功能。"
        await client.post(
            f"/api/v1/projects/{project_id}/chapters",
            json={"title": "第一章", "content": content}
        )

        # 检查项目字数
        response = await client.get(f"/api/v1/projects/{project_id}")
        data = response.json()

        assert data["word_count"] > 0
        assert data["chapter_count"] == 1


@pytest.mark.asyncio
async def test_cache_invalidation(client: AsyncClient):
    """测试缓存失效"""
    # 创建项目
    create_response = await client.post(
        "/api/v1/projects/",
        json={"title": "缓存测试", "genre": "科幻"}
    )
    project_id = create_response.json()["id"]

    # 获取项目（应该被缓存）
    await client.get(f"/api/v1/projects/{project_id}")

    # 更新项目（应该清除缓存）
    await client.put(
        f"/api/v1/projects/{project_id}",
        json={"title": "已更新"}
    )

    # 再次获取应该返回更新后的数据
    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.json()["title"] == "已更新"
