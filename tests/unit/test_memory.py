"""
记忆系统单元测试
"""

import pytest
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory.base import MemoryLevel, MemoryItem
from memory.hierarchical import HierarchicalMemory
from memory.vector import MockVectorStore


class TestMemoryItem:
    """测试 MemoryItem"""

    def test_memory_item_creation(self):
        """测试创建记忆项"""
        item = MemoryItem(
            level=MemoryLevel.GLOBAL,
            content="这是一个测试记忆",
            metadata={"test": True}
        )
        assert item.level == MemoryLevel.GLOBAL
        assert item.content == "这是一个测试记忆"
        assert item.metadata["test"] is True
        assert item.id is not None

    def test_memory_item_to_dict(self):
        """测试 MemoryItem 转字典"""
        item = MemoryItem(
            level=MemoryLevel.CHARACTER,
            content="角色记忆",
            metadata={"name": "张三"}
        )
        data = item.to_dict()
        assert data["level"] == "character"
        assert data["content"] == "角色记忆"
        assert data["metadata"]["name"] == "张三"


class TestHierarchicalMemory:
    """测试分层记忆系统"""

    def test_memory_creation(self):
        """测试创建记忆系统"""
        memory = HierarchicalMemory(storage_path="/tmp/test_memory")
        assert memory is not None

    def test_add_memory_item(self):
        """测试添加记忆项"""
        memory = HierarchicalMemory(storage_path="/tmp/test_memory_add")
        item = MemoryItem(
            level=MemoryLevel.GLOBAL,
            content="世界背景：这是一个魔法世界"
        )
        memory_id = memory.add(item)
        assert memory_id is not None
        assert memory_id in memory.memories

    def test_get_memory_item(self):
        """测试获取记忆项"""
        memory = HierarchicalMemory(storage_path="/tmp/test_memory_get")
        item = MemoryItem(
            level=MemoryLevel.CHARACTER,
            content="主角：林风",
            metadata={"name": "林风", "role": "主角"}
        )
        memory_id = memory.add(item)
        retrieved = memory.get(memory_id)
        assert retrieved is not None
        assert retrieved.content == "主角：林风"
        assert retrieved.metadata["name"] == "林风"

    def test_update_memory_item(self):
        """测试更新记忆项"""
        memory = HierarchicalMemory(storage_path="/tmp/test_memory_update")
        item = MemoryItem(
            level=MemoryLevel.PLOT,
            content="第一章开始"
        )
        memory_id = memory.add(item)
        memory.update(memory_id, "第一章：林风觉醒", metadata={"chapter": 1})
        updated = memory.get(memory_id)
        assert updated.content == "第一章：林风觉醒"
        assert updated.metadata["chapter"] == 1

    def test_delete_memory_item(self):
        """测试删除记忆项"""
        memory = HierarchicalMemory(storage_path="/tmp/test_memory_delete")
        item = MemoryItem(
            level=MemoryLevel.CONTEXT,
            content="近期的上下文内容"
        )
        memory_id = memory.add(item)
        assert memory.get(memory_id) is not None
        memory.delete(memory_id)
        assert memory.get(memory_id) is None

    def test_search_memory_items(self):
        """测试搜索记忆项"""
        memory = HierarchicalMemory(storage_path="/tmp/test_memory_search")

        # 添加多个记忆项
        memory.add(MemoryItem(MemoryLevel.GLOBAL, "世界是一个魔法世界"))
        memory.add(MemoryItem(MemoryLevel.CHARACTER, "主角林风是个天才"))
        memory.add(MemoryItem(MemoryLevel.PLOT, "林风发现了自己的天赋"))
        memory.add(MemoryItem(MemoryLevel.CONTEXT, "林风刚刚进入学院"))

        # 搜索
        results = memory.search("林风", limit=10)
        assert len(results) >= 3  # 应该找到3个包含"林风"的记忆

    def test_get_by_level(self):
        """测试按层级获取记忆项"""
        memory = HierarchicalMemory(storage_path="/tmp/test_memory_level")

        # 添加不同层级的记忆
        memory.add(MemoryItem(MemoryLevel.GLOBAL, "世界设定"))
        memory.add(MemoryItem(MemoryLevel.CHARACTER, "角色A"))
        memory.add(MemoryItem(MemoryLevel.CHARACTER, "角色B"))
        memory.add(MemoryItem(MemoryLevel.PLOT, "情节1"))

        # 获取角色层级的记忆
        character_memories = memory.get_by_level(MemoryLevel.CHARACTER)
        assert len(character_memories) == 2

    def test_with_vector_store(self):
        """测试使用向量存储"""
        vector_store = MockVectorStore()
        memory = HierarchicalMemory(
            storage_path="/tmp/test_memory_vector",
            use_vector_db=True,
            vector_store=vector_store
        )

        # 添加记忆
        item = MemoryItem(
            level=MemoryLevel.CHARACTER,
            content="张三是主角的朋友"
        )
        memory.add(item)

        # 搜索
        results = memory.search("张三")
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
