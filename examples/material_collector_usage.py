"""
素材收集模块使用示例
Material Collector Usage Examples

演示如何使用素材收集模块从本地知识库和联网搜索收集创作素材
"""

from src.story.material_collector import (
    Material,
    MaterialSource,
    MaterialCategory,
    MaterialDeduplicator,
    CredibilityEvaluator,
    CollectionRequest,
    CollectionResult,
    CompositeMaterialCollector,
)
from src.story.local_knowledge_collector import LocalKnowledgeCollector
from src.story.web_search_collector import WebSearchCollector, MockWebSearchCollector
from src.memory.base import MemoryLevel, MemoryItem
from src.memory.hierarchical import HierarchicalMemory
from src.memory.vector import MockVectorStore


def example_1_basic_collection():
    """示例 1：基本的素材收集"""
    print("=" * 60)
    print("示例 1：基本的素材收集")
    print("=" * 60)

    # 1. 创建记忆系统（模拟）
    vector_store = MockVectorStore()
    memory_store = HierarchicalMemory(
        storage_path="/tmp/example_collection",
        use_vector_db=True,
        vector_store=vector_store,
    )

    # 添加一些记忆
    memory_store.add(
        MemoryItem(
            level=MemoryLevel.CHARACTER,
            content="张三是一个勇敢的侠客，擅长使用剑法",
            metadata={"tags": ["角色", "主角"], "characters": ["张三"]},
        )
    )

    memory_store.add(
        MemoryItem(
            level=MemoryLevel.PLOT,
            content="故事开始于张三踏入江湖，寻找失散多年的妹妹",
            metadata={"tags": ["情节", "开端"], "characters": ["张三", "妹妹"]},
        )
    )

    memory_store.add(
        MemoryItem(
            level=MemoryLevel.GLOBAL,
            content="这是一个武侠世界，各大门派纷争不断",
            metadata={"tags": ["世界", "武侠"]},
        )
    )

    # 2. 创建本地知识库收集器
    local_collector = LocalKnowledgeCollector(memory_store)

    # 3. 创建收集请求
    request = CollectionRequest(
        query="张三",
        category=None,  # 不过滤分类
        max_results=10,
        min_credibility=0.3,
        use_local=True,
        use_web=False,
    )

    # 4. 执行收集
    result = local_collector.collect(request)

    # 5. 显示结果
    print(f"\n收集到 {result.total_count} 条素材，耗时 {result.collection_time:.3f} 秒")
    print(f"来源分布：{result.source_breakdown}")

    for i, material in enumerate(result.materials, 1):
        print(f"\n{i}. [{material.category.value}] {material.content[:50]}...")
        print(f"   可信度: {material.credibility_score:.2f}, 相关性: {material.relevance_score:.2f}")
        print(f"   标签: {', '.join(material.tags) if material.tags else '无'}")

    return result


def example_2_web_search():
    """示例 2：网络搜索收集"""
    print("\n" + "=" * 60)
    print("示例 2：网络搜索收集（Mock）")
    print("=" * 60)

    # 1. 创建 Mock 网络搜索收集器
    web_collector = MockWebSearchCollector()

    # 2. 创建收集请求
    request = CollectionRequest(
        query="剑法",
        category=MaterialCategory.KNOWLEDGE,
        max_results=5,
        min_credibility=0.3,
        use_local=False,
        use_web=True,
    )

    # 3. 执行收集
    result = web_collector.collect(request)

    # 4. 显示结果
    print(f"\n收集到 {result.total_count} 条素材，耗时 {result.collection_time:.3f} 秒")

    for i, material in enumerate(result.materials, 1):
        print(f"\n{i}. [{material.category.value}] {material.content}")
        print(f"   来源: {material.source.value}")
        print(f"   URL: {material.metadata.get('url', 'N/A')}")
        print(f"   可信度: {material.credibility_score:.2f}, 相关性: {material.relevance_score:.2f}")

    return result


def example_3_composite_collection():
    """示例 3：复合素材收集（本地 + 网络）"""
    print("\n" + "=" * 60)
    print("示例 3：复合素材收集（本地 + 网络）")
    print("=" * 60)

    # 1. 创建记忆系统
    vector_store = MockVectorStore()
    memory_store = HierarchicalMemory(
        storage_path="/tmp/composite_example",
        use_vector_db=True,
        vector_store=vector_store,
    )

    # 添加一些本地记忆
    memory_store.add(
        MemoryItem(
            level=MemoryLevel.GLOBAL,
            content="本地的武功知识：九阳神功、九阴真经等",
            metadata={"tags": ["武功", "内功"]},
        )
    )

    # 2. 创建多个收集器
    local_collector = LocalKnowledgeCollector(memory_store)
    web_collector = MockWebSearchCollector()

    # 3. 创建复合收集器
    composite = CompositeMaterialCollector(
        collectors=[local_collector, web_collector]
    )

    # 4. 创建收集请求
    request = CollectionRequest(
        query="武功",
        category=MaterialCategory.KNOWLEDGE,
        max_results=10,
        min_credibility=0.3,
        use_local=True,
        use_web=True,
    )

    # 5. 执行收集
    result = composite.collect(request)

    # 6. 显示结果
    print(f"\n总共收集到 {result.total_count} 条素材，耗时 {result.collection_time:.3f} 秒")
    print(f"来源分布：")
    for source, count in result.source_breakdown.items():
        print(f"  - {source}: {count} 条")

    print("\n按来源分类显示：")
    local_materials = [m for m in result.materials if m.source == MaterialSource.LOCAL_KNOWLEDGE]
    web_materials = [m for m in result.materials if m.source == MaterialSource.WEB_SEARCH]

    print(f"\n本地知识库 ({len(local_materials)} 条):")
    for material in local_materials:
        print(f"  - {material.content[:40]}... (可信度: {material.credibility_score:.2f})")

    print(f"\n网络搜索 ({len(web_materials)} 条):")
    for material in web_materials:
        print(f"  - {material.content[:40]}... (可信度: {material.credibility_score:.2f})")

    return result


def example_4_deduplication():
    """示例 4：素材去重"""
    print("\n" + "=" * 60)
    print("示例 4：素材去重")
    print("=" * 60)

    # 1. 创建重复的素材
    materials = [
        Material(
            content="  九阳神功  ",  # 前后有空格
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.KNOWLEDGE,
        ),
        Material(
            content="九阳神功",  # 无空格
            source=MaterialSource.WEB_SEARCH,
            category=MaterialCategory.KNOWLEDGE,
        ),
        Material(
            content="九阴真经",  # 不同内容
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.KNOWLEDGE,
        ),
        Material(
            content="九阳神功",  # 重复
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.KNOWLEDGE,
        ),
    ]

    print(f"\n原始素材数量: {len(materials)}")

    # 2. 创建去重器
    deduplicator = MaterialDeduplicator()

    # 3. 执行去重
    unique_materials = deduplicator.deduplicate(materials)

    print(f"去重后素材数量: {len(unique_materials)}")

    for i, material in enumerate(unique_materials, 1):
        print(f"{i}. {material.content}")

    return unique_materials


def example_5_credibility_evaluation():
    """示例 5：可信度评估"""
    print("\n" + "=" * 60)
    print("示例 5：可信度评估")
    print("=" * 60)

    # 1. 创建不同来源的素材
    materials = [
        Material(
            content="来自用户输入的设定",
            source=MaterialSource.USER_INPUT,
            category=MaterialCategory.CHARACTER,
        ),
        Material(
            content="来自本地知识库的内容",
            source=MaterialSource.LOCAL_KNOWLEDGE,
            category=MaterialCategory.SETTING,
        ),
        Material(
            content="来自网络搜索的信息",
            source=MaterialSource.WEB_SEARCH,
            category=MaterialCategory.KNOWLEDGE,
        ),
    ]

    # 2. 创建评估器
    evaluator = CredibilityEvaluator()

    # 3. 评估素材
    print("\n素材可信度评估：")
    for material in materials:
        score = evaluator.evaluate(material)
        print(f"- {material.source.value:20s} {score:.2f}")

    # 4. 批量评估
    print("\n批量评估：")
    evaluated_materials = evaluator.evaluate_batch(materials)

    for material in evaluated_materials:
        print(f"- [{material.source.value}] {material.content[:30]}...")
        print(f"  可信度: {material.credibility_score:.2f}")

    return evaluated_materials


def example_6_filter_and_sort():
    """示例 6：过滤和排序素材"""
    print("\n" + "=" * 60)
    print("示例 6：过滤和排序素材")
    print("=" * 60)

    # 1. 使用示例 3 的结果
    result = example_3_composite_collection()

    # 2. 过滤高可信度素材
    print("\n过滤可信度 >= 0.6 的素材:")
    high_cred_materials = result.filter_by_credibility(0.6)
    print(f"找到 {len(high_cred_materials)} 条高可信度素材")

    for material in high_cred_materials:
        print(f"- {material.content[:40]}... (可信度: {material.credibility_score:.2f})")

    # 3. 获取最相关的素材
    print("\n最相关的 3 条素材:")
    top_materials = result.get_top_by_relevance(3)

    for i, material in enumerate(top_materials, 1):
        print(f"{i}. [{material.source.value}] {material.content}")
        print(f"   相关性: {material.relevance_score:.2f}")

    return result


def example_7_specific_queries():
    """示例 7：特定查询方法"""
    print("\n" + "=" * 60)
    print("示例 7：特定查询方法")
    print("=" * 60)

    # 1. 创建记忆系统
    vector_store = MockVectorStore()
    memory_store = HierarchicalMemory(
        storage_path="/tmp/specific_queries",
        use_vector_db=True,
        vector_store=vector_store,
    )

    # 添加测试记忆
    memory_store.add(
        MemoryItem(
            level=MemoryLevel.CHARACTER,
            content="张三是一个勇敢的侠客，擅长使用剑法",
            metadata={"tags": ["角色", "主角"], "characters": ["张三"]},
        )
    )

    memory_store.add(
        MemoryItem(
            level=MemoryLevel.PLOT,
            content="张三在江湖中遇到了各种挑战和机缘",
            metadata={"tags": ["情节", "江湖"]},
        )
    )

    memory_store.add(
        MemoryItem(
            level=MemoryLevel.CONTEXT,
            content="最近的上下文：张三刚刚到达京城",
            metadata={"tags": ["上下文", "京城"]},
        )
    )

    # 2. 创建本地知识库收集器
    local_collector = LocalKnowledgeCollector(memory_store)

    # 3. 按角色查询
    print("\n按角色查询 '张三':")
    character_materials = local_collector.get_by_character("张三", limit=5)
    for i, material in enumerate(character_materials, 1):
        print(f"{i}. {material.content}")

    # 4. 按情节查询
    print("\n按情节查询 '江湖':")
    plot_materials = local_collector.get_by_plot("江湖", limit=5)
    for i, material in enumerate(plot_materials, 1):
        print(f"{i}. {material.content}")

    # 5. 获取最近的上下文
    print("\n获取最近的上下文:")
    context_materials = local_collector.get_recent_context(limit=3)
    for i, material in enumerate(context_materials, 1):
        print(f"{i}. {material.content}")

    # 6. 获取全局设定
    print("\n获取全局设定:")
    global_settings = local_collector.get_global_settings()
    for i, material in enumerate(global_settings, 1):
        print(f"{i}. {material.content}")


def main():
    """运行所有示例"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + " " * 15 + "素材收集模块使用示例" + " " * 22 + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")

    # 运行所有示例
    example_1_basic_collection()
    example_2_web_search()
    example_3_composite_collection()
    example_4_deduplication()
    example_5_credibility_evaluation()
    example_6_filter_and_sort()
    example_7_specific_queries()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
