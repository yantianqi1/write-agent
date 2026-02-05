"""
本地知识库收集器
Local Knowledge Collector

从记忆系统检索相关素材
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from .material_collector import (
    MaterialCollector,
    MaterialSource,
    MaterialCategory,
    Material,
    CollectionRequest,
    CollectionResult,
)
from ..memory.base import MemoryLevel
from ..memory.hierarchical import HierarchicalMemory


class LocalKnowledgeCollector(MaterialCollector):
    """本地知识库收集器

    从分层记忆系统中检索相关素材
    """

    def __init__(self, memory_store: HierarchicalMemory):
        self.memory_store = memory_store

        # 记忆层级到素材分类的映射
        self.level_to_category = {
            MemoryLevel.GLOBAL: MaterialCategory.SETTING,
            MemoryLevel.CHARACTER: MaterialCategory.CHARACTER,
            MemoryLevel.PLOT: MaterialCategory.PLOT,
            MemoryLevel.CONTEXT: MaterialCategory.DIALOGUE,
            MemoryLevel.STYLE: MaterialCategory.REFERENCE,
        }

    def get_source_type(self) -> MaterialSource:
        return MaterialSource.LOCAL_KNOWLEDGE

    def collect(self, request: CollectionRequest) -> CollectionResult:
        """从记忆系统收集素材"""
        import time
        start_time = time.time()

        materials = []

        # 确定要搜索的记忆层级
        levels = self._determine_levels(request.category)

        # 从各个层级搜索相关记忆
        for level in levels:
            try:
                memory_items = self.memory_store.search(
                    query=request.query,
                    level=level,
                    limit=request.max_results,
                )

                # 转换为素材对象
                for memory_item in memory_items:
                    material = self._memory_to_material(
                        memory_item,
                        request.category or self.level_to_category.get(level),
                    )
                    materials.append(material)

            except Exception as e:
                print(f"Warning: Search in level {level} failed: {e}")
                continue

        # 计算相关性分数（使用记忆系统的搜索分数）
        for material in materials:
            if "_search_score" in material.metadata:
                material.relevance_score = material.metadata["_search_score"]

        collection_time = time.time() - start_time

        return CollectionResult(
            materials=materials,
            total_count=len(materials),
            source_breakdown={MaterialSource.LOCAL_KNOWLEDGE.value: len(materials)},
            collection_time=collection_time,
        )

    def _determine_levels(self, category: Optional[MaterialCategory]) -> List[MemoryLevel]:
        """根据素材分类确定要搜索的记忆层级"""
        if category is None:
            # 如果未指定分类，搜索所有层级
            return list(MemoryLevel)

        # 根据分类映射到层级
        category_to_levels = {
            MaterialCategory.CHARACTER: [MemoryLevel.CHARACTER],
            MaterialCategory.SETTING: [MemoryLevel.GLOBAL],
            MaterialCategory.PLOT: [MemoryLevel.PLOT],
            MaterialCategory.DIALOGUE: [MemoryLevel.CONTEXT],
            MaterialCategory.DESCRIPTION: [MemoryLevel.CONTEXT, MemoryLevel.STYLE],
            MaterialCategory.REFERENCE: [MemoryLevel.STYLE],
            MaterialCategory.KNOWLEDGE: [MemoryLevel.GLOBAL],
        }

        return category_to_levels.get(category, list(MemoryLevel))

    def _memory_to_material(
        self,
        memory_item,
        category: Optional[MaterialCategory] = None,
    ) -> Material:
        """将记忆项转换为素材对象"""
        # 如果没有指定分类，使用层级映射
        if category is None:
            category = self.level_to_category.get(
                memory_item.level,
                MaterialCategory.KNOWLEDGE,
            )

        # 提取标签
        tags = set()
        if "tags" in memory_item.metadata:
            tags = set(memory_item.metadata["tags"])
        if "characters" in memory_item.metadata:
            tags.update(memory_item.metadata["characters"])
        if "locations" in memory_item.metadata:
            tags.update(memory_item.metadata["locations"])

        # 创建素材对象
        material = Material(
            content=memory_item.content,
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=category,
            timestamp=memory_item.timestamp,
            metadata={
                "memory_id": memory_item.id,
                "memory_level": memory_item.level.value,
                **memory_item.metadata,
            },
            tags=tags,
        )

        return material

    def get_by_character(self, character_name: str, limit: int = 10) -> List[Material]:
        """获取特定角色的相关素材"""
        request = CollectionRequest(
            query=character_name,
            category=MaterialCategory.CHARACTER,
            max_results=limit,
            use_local=True,
            use_web=False,
        )
        result = self.collect(request)
        return result.materials

    def get_by_plot(self, plot_keyword: str, limit: int = 10) -> List[Material]:
        """获取特定情节的相关素材"""
        request = CollectionRequest(
            query=plot_keyword,
            category=MaterialCategory.PLOT,
            max_results=limit,
            use_local=True,
            use_web=False,
        )
        result = self.collect(request)
        return result.materials

    def get_recent_context(self, limit: int = 5) -> List[Material]:
        """获取最近的上下文素材"""
        try:
            memory_items = self.memory_store.get_by_level(
                MemoryLevel.CONTEXT,
                limit=limit,
            )

            materials = []
            for memory_item in memory_items:
                material = self._memory_to_material(memory_item)
                materials.append(material)

            return materials

        except Exception as e:
            print(f"Warning: Failed to get recent context: {e}")
            return []

    def get_global_settings(self) -> List[Material]:
        """获取全局设定素材"""
        try:
            memory_items = self.memory_store.get_by_level(
                MemoryLevel.GLOBAL,
                limit=100,
            )

            materials = []
            for memory_item in memory_items:
                material = self._memory_to_material(memory_item)
                materials.append(material)

            return materials

        except Exception as e:
            print(f"Warning: Failed to get global settings: {e}")
            return []
