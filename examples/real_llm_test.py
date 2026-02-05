"""
Real LLM API Test - 真实 LLM API 测试

使用 .env 中的配置进行实际的 LLM 调用测试。
"""

import sys
import os
sys.path.insert(0, '/root/write-agent')

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from src.story.llm import (
    LLMConfig, create_llm_provider, Message, MessageRole
)
from src.story.setting_extractor.models import (
    ExtractedSettings,
    CharacterProfile,
    WorldSetting,
    PlotElement,
    StylePreference
)
from src.story.generation.content_generator import (
    GenerationRequest,
    GenerationMode,
    create_content_generator,
    create_story_generator
)
from src.story.generation.content_manager import create_content_manager


def print_section(title: str):
    """打印分隔符"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_llm_connection():
    """测试1: LLM 连接测试"""
    print_section("测试1: LLM 连接测试")

    # 从环境变量创建配置
    config = LLMConfig(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model=os.getenv("OPENAI_MODEL", "gpt-4"),
        temperature=0.7,
        timeout=120
    )

    print(f"配置信息:")
    print(f"  Provider: {config.provider}")
    print(f"  Base URL: {config.base_url}")
    print(f"  Model: {config.model}")

    # 创建 provider
    llm = create_llm_provider(config)

    # 测试生成
    from src.story.llm.base import LLMRequest
    request = LLMRequest(
        messages=[
            Message(role=MessageRole.SYSTEM, content="你是一个专业的小说作家。"),
            Message(role=MessageRole.USER, content="请写一段关于勇敢骑士的简短故事，大约100字。")
        ],
        temperature=0.8,
        max_tokens=500
    )

    print(f"\n发送请求...")
    response = llm.generate(request)

    print(f"\n响应状态:")
    print(f"  Model: {response.model}")
    print(f"  Finish Reason: {response.finish_reason}")
    print(f"  Usage: {response.usage}")

    print(f"\n生成内容:")
    print(response.content)


def test_story_generation():
    """测试2: 完整故事生成"""
    print_section("测试2: 完整故事生成")

    # 创建故事设定
    settings = ExtractedSettings(
        characters=[
            CharacterProfile(
                name="林风",
                role="主角",
                personality="冷静、果断、有正义感",
                background="前特种部队成员，现为私人保镖",
                appearance="身材高大，眼神锐利"
            )
        ],
        world=WorldSetting(
            world_type="现代都市悬疑",
            era="21世纪",
            technology_level="现代科技"
        ),
        plot=PlotElement(
            conflict="林风保护的一名证人被神秘组织追杀",
            inciting_incident="证人在准备作证前突然失踪",
            themes=["正义", "保护", "阴谋"]
        ),
        style=StylePreference(
            pov="第三人称有限视角",
            tense="过去时",
            tone="紧张",
            pacing="快节奏"
        )
    )

    # 创建 LLM 配置
    config = LLMConfig(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model=os.getenv("OPENAI_MODEL", "gpt-4"),
        temperature=0.8,
        timeout=120
    )

    llm = create_llm_provider(config)
    story_gen = create_story_generator(llm, auto_outline=True)

    print(f"故事设定:")
    print(f"  类型: {settings.world.world_type}")
    print(f"  主角: {settings.characters[0].name}")
    print(f"  冲突: {settings.plot.conflict}")
    print(f"  风格: {settings.style.tone}、{settings.style.pacing}")

    # 生成第一章
    print(f"\n正在生成第一章...")
    chapter = story_gen.generate_chapter(
        settings=settings,
        chapter_number=1,
        generation_mode=GenerationMode.FULL,
        location="林风的公寓"
    )
    # Note: target_word_count is set via GenerationRequest's default

    print(f"\n生成完成!")
    print(f"  标题: {chapter.title}")
    print(f"  字数: {chapter.word_count}")
    print(f"  大纲: {chapter.outline[:200] if chapter.outline else '无'}...")

    print(f"\n=== 章节内容 ===")
    print(chapter.content)

    # 获取统计
    stats = story_gen.get_story_stats()
    print(f"\n=== 故事统计 ===")
    print(f"总章节数: {stats['total_chapters']}")
    print(f"总字数: {stats['total_words']}")


def test_continue_generation():
    """测试3: 续写测试"""
    print_section("测试3: 续写测试")

    settings = ExtractedSettings(
        characters=[CharacterProfile(name="小明", role="主角", personality="好奇")],
        world=WorldSetting(world_type="奇幻冒险"),
        plot=PlotElement(conflict="小明探索神秘岛屿")
    )

    config = LLMConfig(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model=os.getenv("OPENAI_MODEL", "gpt-4"),
        temperature=0.8
    )

    llm = create_llm_provider(config)
    story_gen = create_story_generator(llm, auto_outline=False)

    # 前文内容
    previous_content = """
    小明站在神秘岛屿的海滩上，海浪拍打着礁石。他看到远处有一座古老的高塔，
    塔顶闪烁着奇异的光芒。正当他犹豫要不要前往时，身后传来了一阵奇怪的声音...
    """

    print(f"前文内容:")
    print(previous_content)

    # 续写
    print(f"\n正在续写...")
    chapter = story_gen.generate_chapter(
        settings=settings,
        chapter_number=1,
        generation_mode=GenerationMode.CONTINUE,
        previous_content=previous_content
    )

    print(f"\n=== 续写内容 ===")
    print(chapter.content)


def test_rewrite_generation():
    """测试4: 重写测试"""
    print_section("测试4: 重写测试")

    settings = ExtractedSettings(
        characters=[CharacterProfile(name="李华", role="主角", personality="勇敢")],
        world=WorldSetting(world_type="武侠")
    )

    config = LLMConfig(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model=os.getenv("OPENAI_MODEL", "gpt-4"),
        temperature=0.8
    )

    llm = create_llm_provider(config)
    story_gen = create_story_generator(llm)

    original_content = """
    李华走进客栈，找个位置坐下。他点了酒菜，慢慢地吃着。
    突然，几个大汉走了进来，大声喧哗。
    """

    print(f"原文:")
    print(original_content)

    print(f"\n修改指令: 让场景更紧张，增加武侠氛围")

    # 重写
    rewritten = story_gen.expand_section(
        chapter_number=1,
        settings=settings,
        section_text=original_content,
        target_words=600
    )

    print(f"\n=== 重写后内容 ===")
    print(rewritten)


def main():
    """运行所有测试"""
    print("""
╔════════════════════════════════════════════════════════════╗
║   真实 LLM API 测试 - 使用 .env 配置                       ║
╚════════════════════════════════════════════════════════════╝
    """)

    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("错误: 未找到 OPENAI_API_KEY 环境变量")
        print("请确保 .env 文件配置正确")
        return

    tests = [
        ("LLM 连接测试", test_llm_connection),
        ("完整故事生成", test_story_generation),
        ("续写测试", test_continue_generation),
        ("重写测试", test_rewrite_generation),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"\n✅ {name} 通过")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} 失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("="*60)


if __name__ == "__main__":
    main()
