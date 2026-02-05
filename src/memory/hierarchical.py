"""
分层记忆系统实现
Hierarchical Memory System

实现分层记忆存储和管理
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import json

from .base import MemoryStore, MemoryLevel, MemoryItem
from .vector import VectorStore, ChromaVectorStore, MockVectorStore


class HierarchicalMemory(MemoryStore):
    """分层记忆系统

    使用多层缓存和向量检索实现记忆管理
    """

    def __init__(
        self,
        storage_path: str = "./data/memory",
        use_vector_db: bool = False,
        vector_store: Optional[VectorStore] = None,
    ):
        self.storage_path = storage_path
        self.memories: Dict[str, MemoryItem] = {}
        self.level_index: Dict[MemoryLevel, List[str]] = defaultdict(list)

        # 初始化向量存储
        if use_vector_db and vector_store is None:
            try:
                self.vector_db = ChromaVectorStore()
            except ImportError:
                print("ChromaDB not available, falling back to MockVectorStore")
                self.vector_db = MockVectorStore()
        elif vector_store is not None:
            self.vector_db = vector_store
        else:
            self.vector_db = None

    def add(self, item: MemoryItem) -> str:
        """添加记忆项"""
        # 存储记忆项
        self.memories[item.id] = item
        # 更新层级索引
        self.level_index[item.level].append(item.id)

        # 添加到向量数据库
        if self.vector_db:
            self.vector_db.add(item)

        self._save()
        return item.id

    def get(self, memory_id: str) -> Optional[MemoryItem]:
        """根据 ID 获取记忆项"""
        return self.memories.get(memory_id)

    def update(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """更新记忆项"""
        if memory_id not in self.memories:
            raise ValueError(f"Memory item not found: {memory_id}")

        item = self.memories[memory_id]
        item.content = content
        if metadata:
            item.metadata.update(metadata)

        # 更新向量数据库
        if self.vector_db:
            self.vector_db.update(memory_id, content)

        self._save()

    def delete(self, memory_id: str):
        """删除记忆项"""
        if memory_id not in self.memories:
            return

        item = self.memories[memory_id]
        # 从层级索引中移除
        if memory_id in self.level_index[item.level]:
            self.level_index[item.level].remove(memory_id)

        # 从存储中移除
        del self.memories[memory_id]

        # 从向量数据库删除
        if self.vector_db:
            self.vector_db.delete(memory_id)

        self._save()

    def search(
        self,
        query: str,
        level: Optional[MemoryLevel] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """根据查询搜索记忆项"""
        # 如果有向量数据库，使用语义检索
        if self.vector_db:
            results = self.vector_db.search(query, level=level, limit=limit)
            items = []
            for memory_id, score in results:
                if memory_id in self.memories:
                    item = self.memories[memory_id]
                    # 将分数存储到 metadata 中
                    item.metadata["_search_score"] = score
                    items.append(item)
            return items

        # 否则使用简单的关键词匹配
        candidates = []

        if level:
            # 只搜索指定层级
            memory_ids = self.level_index.get(level, [])
        else:
            # 搜索所有层级
            memory_ids = list(self.memories.keys())

        # 简单的关键词匹配
        query_lower = query.lower()
        for memory_id in memory_ids[:limit * 2]:  # 多取一些候选
            item = self.memories[memory_id]
            if query_lower in item.content.lower():
                candidates.append((item, self._match_score(item, query_lower)))

        # 按匹配度排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in candidates[:limit]]

    def get_by_level(self, level: MemoryLevel, limit: int = 100) -> List[MemoryItem]:
        """根据层级获取记忆项"""
        memory_ids = self.level_index.get(level, [])
        items = [self.memories[mid] for mid in memory_ids[:limit] if mid in self.memories]
        # 按时间倒序排列
        items.sort(key=lambda x: x.timestamp, reverse=True)
        return items

    def _match_score(self, item: MemoryItem, query: str) -> float:
        """计算匹配分数（简单的关键词计数）"""
        return item.content.lower().count(query)

    def _save(self):
        """持久化存储"""
        # TODO: 使用更高效的存储方式
        import os
        os.makedirs(self.storage_path, exist_ok=True)

        # 保存记忆项
        memories_data = {mid: item.to_dict() for mid, item in self.memories.items()}
        with open(f"{self.storage_path}/memories.json", "w", encoding="utf-8") as f:
            json.dump(memories_data, f, ensure_ascii=False, indent=2)

        # 保存索引
        index_data = {
            level.value: ids
            for level, ids in self.level_index.items()
        }
        with open(f"{self.storage_path}/index.json", "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

    def _load(self):
        """从持久化存储加载"""
        import os

        memories_file = f"{self.storage_path}/memories.json"
        index_file = f"{self.storage_path}/index.json"

        if os.path.exists(memories_file) and os.path.exists(index_file):
            # 加载记忆项
            with open(memories_file, "r", encoding="utf-8") as f:
                memories_data = json.load(f)
                for memory_id, data in memories_data.items():
                    self.memories[memory_id] = MemoryItem(
                        level=MemoryLevel(data["level"]),
                        content=data["content"],
                        metadata=data["metadata"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                    )
                    self.memories[memory_id].id = data["id"]

            # 加载索引
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
                for level_str, ids in index_data.items():
                    self.level_index[MemoryLevel(level_str)] = ids
