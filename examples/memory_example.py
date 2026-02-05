#!/usr/bin/env python3
"""
记忆系统使用示例
Memory System Usage Example
"""

import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory.base import MemoryLevel, MemoryItem
from memory.hierarchical import HierarchicalMemory
from memory.vector import MockVectorStore, ChromaVectorStore


def example_basic_usage():
    """基础使用示例"""
    print("=" * 50)
    print("基础使用示例")
    print("=" * 50)

    # 创建记忆系统
    memory = HierarchicalMemory(storage_path="./data/memory")

    # 添加全局记忆（世界观）
    memory.add(MemoryItem(
        level=MemoryLevel.GLOBAL,
        content="世界背景：这是一个充满魔法和冒险的奇幻世界，存在多种魔法元素和神秘的古老种族。",
        metadata={"type": "world_setting"}
    ))

    # 添加角色记忆
    memory.add(MemoryItem(
        level=MemoryLevel.CHARACTER,
        content="主角林风：18岁，天生拥有罕见的元素亲和力，性格坚韧不拔，对未知充满好奇。",
        metadata={"name": "林风", "role": "主角", "age": 18}
    ))

    memory.add(MemoryItem(
        level=MemoryLevel.CHARACTER,
        content="配角张明：林风的挚友，擅长防御魔法，忠诚可靠。",
        metadata={"name": "张明", "role": "配角"}
    ))

    # 添加情节记忆
    memory.add(MemoryItem(
        level=MemoryLevel.PLOT,
        content="林风在一次意外中觉醒了自己的魔法天赋，被当地魔法学院录取。",
        metadata={"chapter": 1, "event": "awakening"}
    ))

    memory.add(MemoryItem(
        level=MemoryLevel.PLOT,
        content="伏笔：林风的觉醒似乎与一个古老的预言有关，预言中提到的元素使者将会改变世界。",
        metadata={"type": "foreshadowing", "resolved": False}
    ))

    # 添加风格记忆
    memory.add(MemoryItem(
        level=MemoryLevel.STYLE,
        content="叙事风格：第三人称全知视角，注重心理描写和环境渲染，语言生动形象。",
        metadata={"style": "narrative"}
    ))

    # 搜索记忆
    print("\n🔍 搜索 '林风'：")
    results = memory.search("林风", limit=5)
    for item in results:
        print(f"  - [{item.level.value}] {item.content[:60]}...")

    print("\n🔍 搜索 '魔法'：")
    results = memory.search("魔法", limit=5)
    for item in results:
        print(f"  - [{item.level.value}] {item.content[:60]}...")

    # 按层级获取
    print("\n📚 获取角色层级的记忆：")
    character_memories = memory.get_by_level(MemoryLevel.CHARACTER)
    for item in character_memories:
        print(f"  - {item.content[:60]}...")


def example_with_vector_store():
    """使用向量存储的示例"""
    print("\n" + "=" * 50)
    print("使用向量存储的示例")
    print("=" * 50)

    # 创建向量存储（使用 Mock 模式，因为没有安装依赖）
    vector_store = MockVectorStore()

    # 创建记忆系统并启用向量存储
    memory = HierarchicalMemory(
        storage_path="./data/memory_vector",
        use_vector_db=True,
        vector_store=vector_store
    )

    # 添加记忆
    memory.add(MemoryItem(
        level=MemoryLevel.CHARACTER,
        content="李华是一个勇敢的战士"
    ))

    memory.add(MemoryItem(
        level=MemoryLevel.CHARACTER,
        content="王芳是一个智慧的女法师"
    ))

    memory.add(MemoryItem(
        level=MemoryLevel.PLOT,
        content="李华和王芳组成了冒险小队"
    ))

    # 使用语义搜索
    print("\n🔍 语义搜索 '战士'：")
    results = memory.search("战士", limit=10)
    for item in results:
        score = item.metadata.get("_search_score", 0)
        print(f"  - [{score:.2f}] {item.content}")


def example_rag_workflow():
    """RAG 工作流示例"""
    print("\n" + "=" * 50)
    print("RAG 工作流示例")
    print("=" * 50)

    memory = HierarchicalMemory(storage_path="./data/memory_rag")

    # 1. 添加背景知识
    print("\n📝 添加背景知识...")
    memory.add(MemoryItem(
        level=MemoryLevel.GLOBAL,
        content="元素魔法分为火、水、风、土四种基础元素，还有稀有的光和暗元素。",
        metadata={"type": "magic_system"}
    ))

    memory.add(MemoryItem(
        level=MemoryLevel.CHARACTER,
        content="林风拥有风元素亲和力，可以使用风刃、风之翼等技能。",
        metadata={"name": "林风", "element": "wind"}
    ))

    # 2. 用户提问/创作需求
    query = "林风可以使用什么魔法技能？"
    print(f"\n❓ 创作需求：{query}")

    # 3. 检索相关记忆
    print("\n🔍 检索相关记忆...")
    relevant_memories = memory.search(query, limit=3)
    for i, item in enumerate(relevant_memories, 1):
        print(f"  {i}. [{item.level.value}] {item.content}")

    # 4. 基于检索结果生成（这里模拟）
    print("\n✨ 基于记忆生成内容...")
    context = "\n".join([item.content for item in relevant_memories])
    print(f"上下文：\n{context}\n")


def main():
    """主函数"""
    # 清理旧数据目录
    import shutil
    for path in ["./data/memory", "./data/memory_vector", "./data/memory_rag"]:
        if os.path.exists(path):
            shutil.rmtree(path)

    # 运行示例
    try:
        example_basic_usage()
        example_with_vector_store()
        example_rag_workflow()

        print("\n" + "=" * 50)
        print("✅ 所有示例运行完成！")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
