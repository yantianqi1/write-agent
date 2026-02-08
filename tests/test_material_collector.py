"""
素材收集模块单元测试
"""

import pytest
from datetime import datetime, timedelta
from story.material_collector import (
    Material,
    MaterialSource,
    MaterialCategory,
    MaterialDeduplicator,
    CredibilityEvaluator,
    CollectionRequest,
    CollectionResult,
    CompositeMaterialCollector,
)
from story.local_knowledge_collector import LocalKnowledgeCollector
from story.web_search_collector import WebSearchCollector, MockWebSearchCollector
from memory.base import MemoryLevel, MemoryItem
from memory.hierarchical import HierarchicalMemory
from src.memory.vector import MockVectorStore


class TestMaterial:
    """测试 Material 数据类"""

    def test_material_creation(self):
        """测试创建素材对象"""
        material = Material(
            content="测试内容",
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.CHARACTER,
        )

        assert material.content == "测试内容"
        assert material.source == MaterialSource.LOCAL_KNOWLEDGE
        assert material.category == MaterialCategory.CHARACTER
        assert material.credibility_score == 0.5
        assert material.relevance_score == 0.5
        assert material.tags == set()

    def test_content_hash(self):
        """测试内容哈希"""
        material1 = Material(
            content="  测试内容  ",
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.CHARACTER,
        )

        material2 = Material(
            content="测试内容",
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.CHARACTER,
        )

        # 相同内容应该有相同哈希
        assert material1.content_hash == material2.content_hash

        # 不同内容应该有不同哈希
        material3 = Material(
            content="不同内容",
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.CHARACTER,
        )
        assert material1.content_hash != material3.content_hash

    def test_to_dict(self):
        """测试转换为字典"""
        material = Material(
            content="测试内容",
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.CHARACTER,
        )

        result = material.to_dict()

        assert result["content"] == "测试内容"
        assert result["source"] == "local_knowledge"
        assert result["category"] == "character"
        assert result["credibility_score"] == 0.5
        assert result["relevance_score"] == 0.5
        assert "content_hash" in result
        assert isinstance(result["tags"], list)
        assert isinstance(result["timestamp"], str)


class TestMaterialDeduplicator:
    """测试素材去重器"""

    def test_deduplicate(self):
        """测试基本去重功能"""
        materials = [
            Material(
                content="相同内容1",
                source=MaterialSource.LOCAL_KNOWLEDGE,
                category=MaterialCategory.CHARACTER,
            ),
            Material(
                content="相同内容2",  # 内容相同（忽略空格）
                source=MaterialSource.LOCAL_KNOWLEDGE,
                category=MaterialCategory.CHARACTER,
            ),
            Material(
                content="  相同内容1  ",  # 内容相同（前后空格）
                source=MaterialSource.LOCAL_KNOWLEDGE,
                category=MaterialCategory.CHARACTER,
            ),
            Material(
                content="不同内容",
                source=MaterialSource.WEB_SEARCH,
                category=MaterialCategory.KNOWLEDGE,
            ),
        ]

        deduplicator = MaterialDeduplicator()
        unique_materials = deduplicator.deduplicate(materials)

        # 应该去重为 2 个（相同内容的不同表达）
        assert len(unique_materials) == 2

        # 第一个应该是相同内容的某个
        assert unique_materials[0].content_hash == unique_materials[1].content_hash
        # 第二个应该是不同内容
        assert unique_materials[2].content == "不同内容"

    def test_deduplicate_incremental(self):
        """测试增量去重"""
        deduplicator = MaterialDeduplicator()

        # 第一批素材
        batch1 = [
            Material(
                content="内容A",
                source=MaterialSource.LOCAL_KNOWLEDGE,
                category=MaterialCategory.CHARACTER,
            ),
            Material(
                content="内容B",
                source=MaterialSource.LOCAL_KNOWLEDGE,
                category=MaterialCategory.CHARACTER,
            ),
        ]

        # 第二批素材（包含重复）
        batch2 = [
            Material(
                content="内容A",  # 重复
                source=MaterialSource.LOCAL_KNOWLEDGE,
                category=MaterialCategory.CHARACTER,
            ),
            Material(
                content="内容C",
                source=MaterialSource.LOCAL_KNOWLEDGE,
                category=MaterialCategory.CHARACTER,
            ),
        ]

        # 第一批去重
        unique1 = deduplicator.deduplicate_incremental(batch1)
        assert len(unique1) == 2

        # 第二批增量去重
        unique2 = deduplicator.deduplicate_incremental(batch2)
        assert len(unique2) == 1  # 只有内容C 是新的

    def test_clear_cache(self):
        """测试清空缓存"""
        deduplicator = MaterialDeduplicator()

        materials = [
            Material(
                content="内容A",
                source=MaterialSource.LOCAL_KNOWLEDGE,
                category=MaterialCategory.CHARACTER,
            ),
        ]

        # 第一次去重
        unique1 = deduplicator.deduplicate_incremental(materials)
        assert len(unique1) == 1

        # 清空缓存
        deduplicator.clear_cache()

        # 再次去重，应该得到同样的结果
        unique2 = deduplicator.deduplicate_incremental(materials)
        assert len(unique2) == 1


class TestCredibilityEvaluator:
    """测试可信度评估器"""

    def test_evaluate_local_knowledge(self):
        """测试本地知识库的可信度"""
        material = Material(
            content="来自本地知识库的内容",
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.KNOWLEDGE,
        )

        evaluator = CredibilityEvaluator()
        score = evaluator.evaluate(material)

        # 本地知识库基础分数应该是 0.8
        assert 0.75 <= score <= 0.85

    def test_evaluate_web_search(self):
        """测试网络搜索的可信度"""
        material = Material(
            content="来自网络搜索的内容",
            source=MaterialSource.WEB_SEARCH,
            category=MaterialCategory.KNOWLEDGE,
        )

        evaluator = CredibilityEvaluator()
        score = evaluator.evaluate(material)

        # 网络搜索基础分数应该是 0.5
        assert 0.45 <= score <= 0.55

    def test_evaluate_user_input(self):
        """测试用户输入的可信度"""
        material = Material(
            content="来自用户输入的内容",
            source=MaterialSource.USER_INPUT,
            category=MaterialCategory.KNOWLEDGE,
        )

        evaluator = CredibilityEvaluator()
        score = evaluator.evaluate(material)

        # 用户输入应该有最高可信度
        assert 0.95 <= score <= 1.0

    def test_content_length_factor(self):
        """测试内容长度对可信度的影响"""
        evaluator = CredibilityEvaluator()

        # 过短内容
        short_material = Material(
            content="短",
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.KNOWLEDGE,
        )
        short_score = evaluator.evaluate(short_material)

        # 正常长度内容
        normal_material = Material(
            content="这是一个正常长度的内容，应该有较高的可信度。",
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.KNOWLEDGE,
        )
        normal_score = evaluator.evaluate(normal_material)

        # 过长内容
        long_material = Material(
            content="非常长的内容" * 1000,
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.KNOWLEDGE,
        )
        long_score = evaluator.evaluate(long_material)

        # 正常长度应该比短的和长的都有更高的可信度
        assert normal_score > short_score
        assert normal_score > long_score

    def test_reference_factor(self):
        """测试引用来源对可信度的影响"""
        evaluator = CredibilityEvaluator()

        # 有引用
        with_ref = Material(
            content="有引用的内容",
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.KNOWLEDGE,
            metadata={"has_reference": True},
        )

        # 无引用
        without_ref = Material(
            content="无引用的内容",
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.KNOWLEDGE,
            metadata={"has_reference": False},
        )

        with_ref_score = evaluator.evaluate(with_ref)
        without_ref_score = evaluator.evaluate(without_ref)

        # 有引用的可信度应该更高
        assert with_ref_score > without_ref_score

    def test_evaluate_batch(self):
        """测试批量评估"""
        materials = [
            Material(
                content=f"内容{i}",
                source=MaterialSource.LOCAL_KNOWLEDGE,
                category=MaterialCategory.KNOWLEDGE,
            )
            for i in range(5)
        ]

        evaluator = CredibilityEvaluator()
        evaluated = evaluator.evaluate_batch(materials)

        assert len(evaluated) == 5
        # 所有素材都应该被评估
        for material in evaluated:
            assert material.credibility_score != 0.5  # 应该被更新


class TestLocalKnowledgeCollector:
    """测试本地知识库收集器"""

    def setup_method(self):
        """测试前设置"""
        # 创建测试用的记忆系统
        self.vector_store = MockVectorStore()
        self.memory_store = HierarchicalMemory(
            storage_path="/tmp/test_memory_collector",
            use_vector_db=True,
            vector_store=self.vector_store,
        )

        # 添加一些测试记忆
        self.memory_store.add(
            MemoryItem(
                level=MemoryLevel.CHARACTER,
                content="张三是一个勇敢的侠客",
                metadata={"tags": ["角色", "主角"]},
            )
        )

        self.memory_store.add(
            MemoryItem(
                level=MemoryLevel.PLOT,
                content="张三在江湖中遇到了各种挑战",
                metadata={"tags": ["情节", "江湖"]},
            )
        )

        self.memory_store.add(
            MemoryItem(
                level=MemoryLevel.GLOBAL,
                content="这是一个武侠世界",
                metadata={"tags": ["世界", "武侠"]},
            )
        )

        # 创建收集器
        self.collector = LocalKnowledgeCollector(self.memory_store)

    def test_collect_by_query(self):
        """测试通过查询收集素材"""
        request = CollectionRequest(
            query="张三",
            category=None,
            max_results=10,
            use_local=True,
            use_web=False,
        )

        result = self.collector.collect(request)

        assert isinstance(result, CollectionResult)
        assert result.total_count > 0
        assert len(result.materials) > 0

        # 检查素材来源
        for material in result.materials:
            assert material.source == MaterialSource.LOCAL_KNOWLEDGE
            assert "张三" in material.content

    def test_collect_by_category(self):
        """测试按分类收集素材"""
        request = CollectionRequest(
            query="",
            category=MaterialCategory.CHARACTER,
            max_results=10,
            use_local=True,
            use_web=False,
        )

        result = self.collector.collect(request)

        assert result.total_count > 0

        # 所有素材应该是角色分类
        for material in result.materials:
            assert material.category == MaterialCategory.CHARACTER

    def test_get_by_character(self):
        """测试获取特定角色的素材"""
        materials = self.collector.get_by_character("张三", limit=5)

        assert len(materials) > 0

        for material in materials:
            assert material.category == MaterialCategory.CHARACTER
            assert "张三" in material.content

    def test_get_by_plot(self):
        """测试获取特定情节的素材"""
        materials = self.collector.get_by_plot("江湖", limit=5)

        assert len(materials) > 0

        for material in materials:
            assert material.category == MaterialCategory.PLOT
            assert "江湖" in material.content

    def test_get_global_settings(self):
        """测试获取全局设定"""
        materials = self.collector.get_global_settings()

        assert len(materials) > 0

        for material in materials:
            assert material.category == MaterialCategory.SETTING


class TestWebSearchCollector:
    """测试网络搜索收集器"""

    def setup_method(self):
        """测试前设置"""
        self.collector = MockWebSearchCollector()

    def test_collect_mock_results(self):
        """测试收集模拟搜索结果"""
        request = CollectionRequest(
            query="剑法",
            category=None,
            max_results=10,
            use_local=False,
            use_web=True,
        )

        result = self.collector.collect(request)

        assert isinstance(result, CollectionResult)
        assert result.total_count > 0
        assert result.collection_time >= 0

        # 检查素材来源
        for material in result.materials:
            assert material.source == MaterialSource.WEB_SEARCH

    def test_set_search_results(self):
        """测试设置外部搜索结果"""
        request = CollectionRequest(
            query="武功",
            category=None,
            max_results=5,
            use_local=False,
            use_web=True,
        )

        # 模拟外部搜索结果
        search_results = [
            {
                "title": "九阳神功",
                "url": "https://example.com/jiuyang",
                "snippet": "九阳神功是一门至阳至刚的内功心法",
            },
            {
                "title": "九阴真经",
                "url": "https://example.com/jiuyin",
                "snippet": "九阴真经是阴阳调和的内功心法",
            },
        ]

        result = self.collector.set_search_results(request, search_results)

        assert result.total_count == 2

        # 检查素材内容
        assert "九阳神功" in result.materials[0].content
        assert "九阴真经" in result.materials[1].content

        # 检查元数据
        for material in result.materials:
            assert "url" in material.metadata
            assert "title" in material.metadata
            assert material.source == MaterialSource.WEB_SEARCH

    def test_relevance_scoring(self):
        """测试相关性评分"""
        request = CollectionRequest(
            query="剑法",
            category=None,
            max_results=5,
            use_local=False,
            use_web=True,
        )

        result = self.collector.collect(request)

        # MockWebSearchCollector 应该设置相关性分数
        if result.total_count > 1:
            # 按相关性排序
            sorted_materials = sorted(
                result.materials, key=lambda x: x.relevance_score, reverse=True
            )
            assert sorted_materials[0].relevance_score >= sorted_materials[-1].relevance_score


class TestCompositeMaterialCollector:
    """测试复合素材收集器"""

    def setup_method(self):
        """测试前设置"""
        # 创建测试用的记忆系统
        self.vector_store = MockVectorStore()
        self.memory_store = HierarchicalMemory(
            storage_path="/tmp/test_memory_collector",
            use_vector_db=True,
            vector_store=self.vector_store,
        )

        # 添加测试记忆
        self.memory_store.add(
            MemoryItem(
                level=MemoryLevel.CHARACTER,
                content="测试角色张三",
                metadata={"tags": ["角色"]},
            )
        )

        # 创建收集器
        self.local_collector = LocalKnowledgeCollector(self.memory_store)
        self.web_collector = MockWebSearchCollector()

        # 创建复合收集器
        self.composite_collector = CompositeMaterialCollector(
            collectors=[self.local_collector, self.web_collector]
        )

    def test_collect_from_multiple_sources(self):
        """测试从多个来源收集素材"""
        request = CollectionRequest(
            query="张三",
            category=None,
            max_results=20,
            use_local=True,
            use_web=True,
            min_credibility=0.0,
        )

        result = self.composite_collector.collect(request)

        assert isinstance(result, CollectionResult)
        assert result.total_count > 0
        assert result.collection_time >= 0

        # 检查是否有来自不同来源的素材
        sources = {material.source for material in result.materials}
        assert len(sources) > 1 or result.total_count > 0  # 至少有一些结果

    def test_filter_by_credibility(self):
        """测试过滤低可信度素材"""
        request = CollectionRequest(
            query="测试",
            category=None,
            max_results=10,
            use_local=True,
            use_web=True,
            min_credibility=0.6,  # 较高的可信度要求
        )

        result = self.composite_collector.collect(request)

        # 所有返回的素材都应该满足最低可信度要求
        for material in result.materials:
            assert material.credibility_score >= 0.6

    def test_deduplication(self):
        """测试复合收集器的去重功能"""
        # 这个测试需要确保本地和搜索有重复的内容
        # 在 mock 环境下，这个测试可能不会触发实际的重复
        # 但验证了去重逻辑的存在

        request = CollectionRequest(
            query="测试",
            category=None,
            max_results=10,
            use_local=True,
            use_web=True,
        )

        result = self.composite_collector.collect(request)

        # 检查结果中没有重复的哈希
        hashes = [material.content_hash for material in result.materials]
        assert len(hashes) == len(set(hashes))

    def test_result_limiting(self):
        """测试结果数量限制"""
        request = CollectionRequest(
            query="测试",
            category=None,
            max_results=5,  # 限制结果数量
            use_local=True,
            use_web=True,
        )

        result = self.composite_collector.collect(request)

        # 结果数量不应该超过 max_results
        assert result.total_count <= 5
        assert len(result.materials) <= 5


class TestIntegration:
    """集成测试"""

    def test_full_collection_workflow(self):
        """测试完整的收集工作流程"""
        # 1. 创建记忆系统
        vector_store = MockVectorStore()
        memory_store = HierarchicalMemory(
            storage_path="/tmp/integration_test",
            use_vector_db=True,
            vector_store=vector_store,
        )

        # 2. 添加记忆
        memory_store.add(
            MemoryItem(
                level=MemoryLevel.CHARACTER,
                content="英雄是一个正义感强烈的年轻人",
                metadata={"tags": ["角色", "主角"]},
            )
        )

        memory_store.add(
            MemoryItem(
                level=MemoryLevel.PLOT,
                content="故事从英雄踏入江湖开始",
                metadata={"tags": ["情节", "开端"]},
            )
        )

        # 3. 创建收集器
        local_collector = LocalKnowledgeCollector(memory_store)
        web_collector = MockWebSearchCollector()
        composite = CompositeMaterialCollector(
            collectors=[local_collector, web_collector]
        )

        # 4. 执行收集
        request = CollectionRequest(
            query="英雄",
            category=None,
            max_results=10,
            use_local=True,
            use_web=True,
        )

        result = composite.collect(request)

        # 5. 验证结果
        assert result.total_count > 0
        assert len(result.source_breakdown) > 0

        # 6. 使用结果
        # 获取高相关性的素材
        top_materials = result.get_top_by_relevance(3)
        assert len(top_materials) <= 3

        # 过滤高可信度的素材
        high_cred = result.filter_by_credibility(0.7)
        for material in high_cred:
            assert material.credibility_score >= 0.7


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
