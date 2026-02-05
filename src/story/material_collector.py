"""
素材收集模块
Material Collector Module

实现从本地知识库和联网搜索收集创作素材
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import re


class MaterialSource(Enum):
    """素材来源类型"""
    LOCAL_KNOWLEDGE = "local_knowledge"  # 本地知识库
    WEB_SEARCH = "web_search"            # 联网搜索
    USER_INPUT = "user_input"            # 用户输入
    PREVIOUS_WORK = "previous_work"      # 历史作品


class MaterialCategory(Enum):
    """素材分类"""
    CHARACTER = "character"      # 人物设定
    SETTING = "setting"          # 场景/世界观设定
    PLOT = "plot"                # 情节/事件
    DIALOGUE = "dialogue"        # 对话素材
    DESCRIPTION = "description"  # 描写素材
    KNOWLEDGE = "knowledge"      # 背景知识
    REFERENCE = "reference"      # 参考作品


@dataclass
class Material:
    """素材项数据结构"""
    content: str                              # 素材内容
    source: MaterialSource                    # 来源
    category: MaterialCategory                # 分类
    credibility_score: float = 0.5            # 可信度分数 (0.0 - 1.0)
    relevance_score: float = 0.5              # 相关性分数 (0.0 - 1.0)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)

    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.tags, list):
            self.tags = set(self.tags)

    @property
    def content_hash(self) -> str:
        """内容的哈希值，用于去重"""
        content_normalized = re.sub(r'\s+', ' ', self.content.strip().lower())
        return hashlib.md5(content_normalized.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "source": self.source.value,
            "category": self.category.value,
            "credibility_score": self.credibility_score,
            "relevance_score": self.relevance_score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "tags": list(self.tags),
            "content_hash": self.content_hash,
        }


@dataclass
class CollectionRequest:
    """素材收集请求"""
    query: str                              # 查询内容/主题
    category: Optional[MaterialCategory] = None  # 指定分类（可选）
    max_results: int = 10                   # 最大结果数
    min_credibility: float = 0.3            # 最低可信度
    use_local: bool = True                  # 是否使用本地知识库
    use_web: bool = False                   # 是否使用联网搜索
    tags: Optional[List[str]] = None        # 标签过滤（可选）

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class CollectionResult:
    """素材收集结果"""
    materials: List[Material]
    total_count: int
    source_breakdown: Dict[str, int] = field(default_factory=dict)
    collection_time: float = 0.0

    def add_materials(self, new_materials: List[Material]):
        """添加新素材"""
        self.materials.extend(new_materials)
        self.total_count = len(self.materials)

    def filter_by_credibility(self, min_score: float) -> List[Material]:
        """过滤出可信度高于指定阈值的素材"""
        return [m for m in self.materials if m.credibility_score >= min_score]

    def filter_by_relevance(self, min_score: float) -> List[Material]:
        """过滤出相关性高于指定阈值的素材"""
        return [m for m in self.materials if m.relevance_score >= min_score]

    def get_top_by_relevance(self, n: int) -> List[Material]:
        """获取相关性最高的 N 个素材"""
        return sorted(self.materials, key=lambda x: x.relevance_score, reverse=True)[:n]


class MaterialCollector(ABC):
    """素材收集器抽象基类"""

    @abstractmethod
    def collect(self, request: CollectionRequest) -> CollectionResult:
        """收集素材的核心方法"""
        pass

    @abstractmethod
    def get_source_type(self) -> MaterialSource:
        """返回收集器类型"""
        pass


class MaterialDeduplicator:
    """素材去重器"""

    def __init__(self, similarity_threshold: float = 0.9):
        self.similarity_threshold = similarity_threshold
        self._seen_hashes: Set[str] = set()

    def deduplicate(self, materials: List[Material]) -> List[Material]:
        """去重素材列表"""
        unique_materials = []
        seen_hashes = set()

        for material in materials:
            content_hash = material.content_hash

            # 简单的哈希去重
            if content_hash not in seen_hashes:
                unique_materials.append(material)
                seen_hashes.add(content_hash)

        return unique_materials

    def deduplicate_incremental(self, materials: List[Material]) -> List[Material]:
        """增量去重（跨批次去重）"""
        unique_materials = []

        for material in materials:
            content_hash = material.content_hash

            if content_hash not in self._seen_hashes:
                unique_materials.append(material)
                self._seen_hashes.add(content_hash)

        return unique_materials

    def clear_cache(self):
        """清空缓存"""
        self._seen_hashes.clear()


class CredibilityEvaluator:
    """素材可信度评估器"""

    def __init__(self):
        # 不同来源的基础可信度
        self.base_scores = {
            MaterialSource.LOCAL_KNOWLEDGE: 0.8,
            MaterialSource.WEB_SEARCH: 0.5,
            MaterialSource.USER_INPUT: 1.0,
            MaterialSource.PREVIOUS_WORK: 0.7,
        }

    def evaluate(self, material: Material) -> float:
        """评估单个素材的可信度"""
        # 基础分数来自来源类型
        base_score = self.base_scores.get(material.source, 0.5)

        # 根据内容长度调整（过短或过长的内容降低可信度）
        content_length = len(material.content)
        length_factor = 1.0

        if content_length < 20:
            length_factor = 0.5
        elif content_length > 10000:
            length_factor = 0.8

        # 根据是否有引用来源调整
        reference_factor = 1.0
        if material.metadata.get("has_reference", False):
            reference_factor = 1.2

        # 综合评分
        final_score = base_score * length_factor * reference_factor
        return min(final_score, 1.0)

    def evaluate_batch(self, materials: List[Material]) -> List[Material]:
        """批量评估素材可信度"""
        for material in materials:
            material.credibility_score = self.evaluate(material)
        return materials


class CompositeMaterialCollector:
    """复合素材收集器

    整合多个收集器，统一调度和去重
    """

    def __init__(
        self,
        collectors: Optional[List[MaterialCollector]] = None,
        deduplicator: Optional[MaterialDeduplicator] = None,
        evaluator: Optional[CredibilityEvaluator] = None,
    ):
        self.collectors = collectors or []
        self.deduplicator = deduplicator or MaterialDeduplicator()
        self.evaluator = evaluator or CredibilityEvaluator()

    def add_collector(self, collector: MaterialCollector):
        """添加收集器"""
        self.collectors.append(collector)

    def collect(self, request: CollectionRequest) -> CollectionResult:
        """使用所有收集器收集素材"""
        import time
        start_time = time.time()

        all_materials = []
        source_breakdown = {}

        # 从所有收集器收集素材
        for collector in self.collectors:
            # 根据请求决定是否使用该收集器
            source_type = collector.get_source_type()

            if source_type == MaterialSource.LOCAL_KNOWLEDGE and not request.use_local:
                continue
            if source_type == MaterialSource.WEB_SEARCH and not request.use_web:
                continue

            try:
                result = collector.collect(request)
                materials = result.materials
                all_materials.extend(materials)
                source_breakdown[source_type.value] = len(materials)
            except Exception as e:
                print(f"Warning: Collector {source_type} failed: {e}")
                continue

        # 去重
        unique_materials = self.deduplicator.deduplicate(all_materials)

        # 评估可信度
        evaluated_materials = self.evaluator.evaluate_batch(unique_materials)

        # 过滤低可信度和低相关性的素材
        filtered_materials = [
            m for m in evaluated_materials
            if m.credibility_score >= request.min_credibility
        ]

        # 限制结果数量
        final_materials = filtered_materials[:request.max_results]

        collection_time = time.time() - start_time

        return CollectionResult(
            materials=final_materials,
            total_count=len(final_materials),
            source_breakdown=source_breakdown,
            collection_time=collection_time,
        )
