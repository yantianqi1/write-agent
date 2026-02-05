"""
向量存储模块
Vector Storage Module

使用 Chroma 实现向量存储和语义检索
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .base import MemoryLevel, MemoryItem


class VectorStore(ABC):
    """向量存储抽象接口"""

    @abstractmethod
    def add(self, item: MemoryItem, embedding: Optional[List[float]] = None):
        """添加记忆项到向量存储"""
        pass

    @abstractmethod
    def search(self, query: str, level: Optional[MemoryLevel] = None, limit: int = 10) -> List[tuple[str, float]]:
        """语义搜索，返回 (memory_id, score) 列表"""
        pass

    @abstractmethod
    def delete(self, memory_id: str):
        """删除记忆项"""
        pass

    @abstractmethod
    def update(self, memory_id: str, content: str):
        """更新记忆项内容"""
        pass


class ChromaVectorStore(VectorStore):
    """Chroma 向量存储实现"""

    def __init__(
        self,
        collection_name: str = "novel_memory",
        persist_path: str = "./data/vector_db",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.collection_name = collection_name
        self.persist_path = persist_path
        self.embedding_model_name = embedding_model
        self._client = None
        self._collection = None
        self._embedding_model = None

        if not CHROMA_AVAILABLE:
            raise ImportError(
                "ChromaDB is not installed. Please install it with: "
                "pip install chromadb sentence-transformers"
            )

        self._init()

    def _init(self):
        """初始化 Chroma 客户端和嵌入模型"""
        # 初始化 Chroma 客户端
        self._client = chromadb.PersistentClient(path=self.persist_path)

        # 初始化嵌入模型
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        else:
            raise ImportError(
                "sentence-transformers is not installed. Please install it with: "
                "pip install sentence-transformers"
            )

        # 获取或创建集合
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """生成文本嵌入"""
        embeddings = self._embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def add(self, item: MemoryItem, embedding: Optional[List[float]] = None):
        """添加记忆项到向量存储"""
        if embedding is None:
            embedding = self._embed([item.content])[0]

        self._collection.add(
            ids=[item.id],
            embeddings=[embedding],
            documents=[item.content],
            metadatas=[
                {
                    "level": item.level.value,
                    "timestamp": item.timestamp.isoformat(),
                    **item.metadata
                }
            ]
        )

    def search(
        self,
        query: str,
        level: Optional[MemoryLevel] = None,
        limit: int = 10
    ) -> List[tuple[str, float]]:
        """语义搜索"""
        # 生成查询嵌入
        query_embedding = self._embed([query])[0]

        # 构建过滤条件
        where = {"level": level.value} if level else None

        # 执行搜索
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where,
        )

        # 提取结果
        memory_ids = results["ids"][0] if results["ids"] else []
        distances = results["distances"][0] if results["distances"] else []

        # 转换为分数（余弦距离越小越相似）
        scores = [1.0 - d for d in distances] if distances else []

        return list(zip(memory_ids, scores))

    def delete(self, memory_id: str):
        """删除记忆项"""
        self._collection.delete(ids=[memory_id])

    def update(self, memory_id: str, content: str):
        """更新记忆项内容"""
        # 先删除旧的
        self.delete(memory_id)

        # 获取旧的记忆项（需要从外部传递）
        # 这里简化处理，实际应该先查询再更新
        # TODO: 优化更新逻辑

    def get_ids_by_level(self, level: MemoryLevel, limit: int = 100) -> List[str]:
        """根据层级获取记忆 ID"""
        results = self._collection.get(
            where={"level": level.value},
            limit=limit,
        )
        return results["ids"] if results else []


class MockVectorStore(VectorStore):
    """Mock 向量存储（用于测试和开发）"""

    def __init__(self):
        self.items: Dict[str, tuple[str, Dict[str, Any]]] = {}  # id -> (content, metadata)

    def add(self, item: MemoryItem, embedding: Optional[List[float]] = None):
        """添加记忆项"""
        self.items[item.id] = (
            item.content,
            {
                "level": item.level.value,
                "timestamp": item.timestamp.isoformat(),
                **item.metadata
            }
        )

    def search(
        self,
        query: str,
        level: Optional[MemoryLevel] = None,
        limit: int = 10
    ) -> List[tuple[str, float]]:
        """简单的关键词搜索（Mock 实现）"""
        query_lower = query.lower()
        results = []

        for memory_id, (content, metadata) in self.items.items():
            # 检查层级
            if level and metadata["level"] != level.value:
                continue

            # 简单的关键词匹配分数
            score = content.lower().count(query_lower) / max(len(content), 1)
            if score > 0:
                results.append((memory_id, min(score * 10, 1.0)))

        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def delete(self, memory_id: str):
        """删除记忆项"""
        if memory_id in self.items:
            del self.items[memory_id]

    def update(self, memory_id: str, content: str):
        """更新记忆项"""
        if memory_id in self.items:
            old_metadata = self.items[memory_id][1]
            self.items[memory_id] = (content, old_metadata)
