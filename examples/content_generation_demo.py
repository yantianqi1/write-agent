"""
Content Generation Demo - LLM 内容生成完整示例

本示例展示如何使用内容生成引擎进行小说创作。

核心功能：
1. LLM 集成（支持 Mock、Claude、OpenAI）
2. 提示词模板生成
3. 章节内容生成
4. 内容管理
5. 一致性检查
"""

import sys
sys.path.insert(0, '/root/write-agent')

from src.story.llm import (
    MockLLMProvider, LLMConfig, create_llm_provider, Message, MessageRole
)
from src.story.setting_extractor.models import (
    ExtractedSettings, CharacterProfile, WorldSetting, PlotElement, StylePreference
)
from src.story.generation.prompt_templates import (
    GenerationContext, GenerationMode, create_template_engine
)
from src.story.generation.content_generator import (
    GenerationRequest, ContentGenerator, LLMContentGenerator, StoryGenerator,
    create_content_generator, create_story_generator
)
from src.story.generation.content_manager import (
    ContentManager, create_content_manager, create_file_manager, ChapterContent
)
from src.story.generation.consistency import (
    ConsistencyChecker, ConsistencyReport, create_consistency_checker
)


def print_section(title: str):
    """打印分隔符"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_llm_integration():
    """演示1: LLM 集成基础"""
    print_section("演示1: LLM 集成基础")

    # 创建 Mock LLM Provider
    llm = MockLLMProvider()

    # 测试生成
    from src.story.llm.base import LLMRequest
    request = LLMRequest(
        messages=[
            Message(role=MessageRole.SYSTEM, content="你是一个作家。"),
            Message(role=MessageRole.USER, content="写一段关于勇敢骑士的故事。")
        ],
        max_tokens=500
    )

    response = llm.generate(request)

    print("Mock LLM 响应:")
    print(response.content[:500] + "...")


def demo_prompt_templates():
    """演示2: 提示词模板系统"""
    print_section("演示2: 提示词模板系统")

    # 创建示例设定
    settings = ExtractedSettings(
        characters=[
            CharacterProfile(
                name="李明",
                role="主角",
                personality="勇敢、善良、有正义感",
                background="一个普通的程序员，意外获得了超能力",
                appearance="身材中等，戴眼镜"
            )
        ],
        world=WorldSetting(
            world_type="都市异能",
            era="现代",
            magic_system="通过代码操控现实的能力",
            technology_level="现代科技与超能力共存"
        ),
        plot=PlotElement(
            conflict="李明需要对抗企图掌控这种能力的神秘组织",
            inciting_incident="李明在一次编程中意外发现可以改写现实"
        ),
        style=StylePreference(
            pov="第三人称有限视角",
            tense="过去时",
            tone="紧张刺激",
            pacing="快节奏"
        )
    )

    # 创建模板引擎
    template_engine = create_template_engine("default")

    # 创建生成上下文
    from src.story.generation.prompt_templates import GenerationContext
    context = GenerationContext(
        settings=settings,
        chapter_number=1,
        generation_mode=GenerationMode.FULL,
        target_word_count=2000
    )

    # 生成提示词
    system_prompt, user_prompt = template_engine.generate_prompt(context)

    print("=== System Prompt ===")
    print(system_prompt[:500] + "...")
    print("\n=== User Prompt ===")
    print(user_prompt[:800] + "...")


def demo_content_generation():
    """演示3: 内容生成"""
    print_section("演示3: 内容生成")

    # 创建设定
    settings = ExtractedSettings(
        characters=[
            CharacterProfile(
                name="云飞",
                role="主角",
                personality="勇敢、机智、重情义",
                background="江湖侠客，为寻找失散的妹妹而踏上旅途",
                appearance="身材修长，剑眉星目"
            )
        ],
        world=WorldSetting(
            world_type="武侠世界",
            era="古代",
            magic_system="内功、轻功、剑术"
        ),
        plot=PlotElement(
            conflict="云飞需要对抗杀害父母的仇人",
            inciting_incident="云飞发现仇人线索"
        )
    )

    # 创建内容生成器
    llm = MockLLMProvider()
    generator = create_content_generator(llm)

    # 生成第一章
    request = GenerationRequest(
        settings=settings,
        chapter_number=1,
        generation_mode=GenerationMode.FULL,
        target_word_count=1500
    )

    result = generator.generate(request)

    print(f"生成了第 {result.chapter_number} 章")
    print(f"字数: {result.word_count}")
    print(f"使用模型: {result.metadata.get('model', 'unknown')}")
    print(f"\n=== 内容预览 ===")
    print(result.content[:600] + "...")


def demo_story_generation():
    """演示4: 完整故事生成流程"""
    print_section("演示4: 完整故事生成流程")

    # 创建设定
    settings = ExtractedSettings(
        characters=[
            CharacterProfile(
                name="林月",
                role="主角",
                personality="聪明、勇敢、好奇",
                background="女侦探，擅长推理"
            )
        ],
        world=WorldSetting(
            world_type="现代都市",
            era="21世纪"
        ),
        plot=PlotElement(
            conflict="林月需要侦破一系列神秘失踪案"
        )
    )

    # 创建故事生成器
    llm = MockLLMProvider()
    story_gen = create_story_generator(llm, auto_outline=True)

    # 生成前两章
    for i in range(1, 3):
        print(f"\n--- 生成第 {i} 章 ---")
        chapter = story_gen.generate_chapter(
            settings=settings,
            chapter_number=i,
            location="案发现场" if i == 1 else "侦探办公室"
        )

        print(f"标题: {chapter.title}")
        print(f"字数: {chapter.word_count}")
        print(f"大纲: {chapter.outline[:100] if chapter.outline else '无'}...")

    # 获取统计
    stats = story_gen.get_story_stats()
    print(f"\n=== 故事统计 ===")
    print(f"总章节数: {stats['total_chapters']}")
    print(f"总字数: {stats['total_words']}")
    print(f"平均每章字数: {stats['avg_words_per_chapter']}")


def demo_content_manager():
    """演示5: 内容管理"""
    print_section("演示5: 内容管理")

    # 创建内容管理器
    manager = create_content_manager(auto_save=True)

    # 创建项目
    project = manager.create_project(
        name="示例故事",
        description="这是一个示例故事项目"
    )

    # 添加示例章节
    from datetime import datetime

    chapter1 = ChapterContent(
        chapter_number=1,
        title="第一章：开始",
        content="这是第一章的内容...",
        word_count=100,
        created_at=datetime.now().isoformat()
    )

    manager.add_chapter(chapter1)
    print(f"已添加: {chapter1.title}")

    # 查询章节
    retrieved = manager.get_chapter(1)
    print(f"查询第1章: {retrieved.title if retrieved else '未找到'}")

    # 获取统计
    stats = manager.get_stats()
    print(f"\n=== 项目统计 ===")
    print(f"总章节数: {stats['total_chapters']}")
    print(f"总字数: {stats['total_words']}")

    # 导出
    markdown = manager.export_to_markdown()
    print(f"\n=== Markdown 导出预览 ===")
    print(markdown[:300] + "...")


def demo_consistency_checking():
    """演示6: 一致性检查"""
    print_section("演示6: 一致性检查")

    # 创建设定
    settings = ExtractedSettings(
        characters=[
            CharacterProfile(
                name="张三",
                role="主角",
                personality="勇敢、果断"
            ),
            CharacterProfile(
                name="李四",
                role="配角",
                personality="胆小、谨慎"
            )
        ],
        world=WorldSetting(
            world_type="古代",
            technology_level="冷兵器时代"
        )
    )

    # 创建一致性检查器
    checker = create_consistency_checker(settings)

    # 测试内容 - 包含一致性问题
    test_content = """
    张三握着剑，心中充满了恐惧。他不敢上前，只能眼睁睁地看着敌人逼近。

    李四突然变得异常勇敢，冲上前去与敌人搏斗。

    张三掏出了手枪，向敌人射击。
    """

    print("=== 测试内容 ===")
    print(test_content)

    # 检查一致性
    report = checker.check_content(test_content, chapter_number=1)

    print(f"\n=== 一致性检查结果 ===")
    print(f"通过: {report.passed}")
    print(f"得分: {report.score:.2f}")
    print(f"发现问题数: {len(report.issues)}")

    if report.issues:
        print("\n=== 发现的问题 ===")
        for issue in report.issues:
            print(f"[{issue.level.value.upper()}] {issue.description}")
            if issue.suggestion:
                print(f"  建议: {issue.suggestion}")


def demo_full_workflow():
    """演示7: 完整工作流"""
    print_section("演示7: 完整创作工作流")

    # 1. 创建设定
    settings = ExtractedSettings(
        characters=[
            CharacterProfile(
                name="陈宇",
                role="主角",
                personality="冷静、理性、分析能力强",
                background="前刑警，现为私家侦探"
            )
        ],
        world=WorldSetting(
            world_type="现代悬疑",
            era="21世纪"
        ),
        plot=PlotElement(
            conflict="陈宇需要侦破一起连环失踪案"
        ),
        style=StylePreference(
            pov="第一人称",
            tense="过去时",
            tone="悬疑",
            pacing="中等"
        )
    )

    print("=== 故事设定 ===")
    print(f"类型: {settings.world.world_type}")
    print(f"主角: {settings.characters[0].name}")
    print(f"冲突: {settings.plot.conflict}")

    # 2. 创建组件
    llm = MockLLMProvider()
    story_gen = create_story_generator(llm)
    manager = create_content_manager()
    checker = create_consistency_checker(settings)

    # 3. 创建项目
    manager.create_project("悬疑故事", "一个侦探破案的故事")

    # 4. 生成第一章
    print(f"\n--- 生成第一章 ---")
    chapter = story_gen.generate_chapter(
        settings=settings,
        chapter_number=1,
        location="案发现场"
    )

    # 5. 添加到管理器
    manager.add_chapter(chapter)

    # 6. 检查一致性
    report = checker.check_content(chapter.content, 1)
    print(f"一致性检查: {report.score:.2f} 分")

    # 7. 显示统计
    stats = manager.get_stats()
    print(f"\n=== 项目统计 ===")
    print(f"总字数: {stats['total_words']}")
    print(f"章节数: {stats['total_chapters']}")

    print(f"\n=== 内容预览 ===")
    print(chapter.content[:400] + "...")


def demo_streaming_generation():
    """演示8: 流式生成"""
    print_section("演示8: 流式生成")

    import asyncio

    async def stream_demo():
        settings = ExtractedSettings(
            characters=[CharacterProfile(name="主角", role="主角")],
            world=WorldSetting(world_type="奇幻")
        )

        llm = MockLLMProvider()
        generator = create_content_generator(llm)

        request = GenerationRequest(
            settings=settings,
            chapter_number=1,
            target_word_count=500
        )

        print("=== 流式输出 ===")
        collected = []
        async for chunk in generator.generate_stream(request):
            collected.append(chunk)
            print(chunk, end='', flush=True)

        print(f"\n\n共收到 {len(collected)} 个块")

    asyncio.run(stream_demo())


def main():
    """运行所有演示"""
    print("""
╔════════════════════════════════════════════════════════════╗
║   内容生成引擎演示 - LLM 集成与小说创作                  ║
╚════════════════════════════════════════════════════════════╝
    """)

    demos = [
        ("LLM 集成基础", demo_llm_integration),
        ("提示词模板系统", demo_prompt_templates),
        ("内容生成", demo_content_generation),
        ("完整故事生成", demo_story_generation),
        ("内容管理", demo_content_manager),
        ("一致性检查", demo_consistency_checking),
        ("完整创作工作流", demo_full_workflow),
        ("流式生成", demo_streaming_generation),
    ]

    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n演示出错: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("所有演示完成！")
    print("="*60)


if __name__ == "__main__":
    main()
