"""
Conversational Agent Demo - 隐式设定提取和AI补全示例

本示例展示如何使用对话式 Agent 进行隐式设定提取和自动补全。
用户只需要自然聊天，AI 会自动在后台构建和补全设定。

核心特性：
1. 隐式设定提取 - 从对话中自动推断设定
2. AI 智能补全 - 自动填充缺失信息
3. 创作决策 - 自动判断何时开始创作
4. 无感修改 - 理解自然语言修改指令
"""

import sys
sys.path.insert(0, '/root/write-agent')

from src.story.setting_extractor.conversational_agent import (
    ConversationalAgent, StreamlinedAgent, create_agent
)
from src.story.setting_extractor.modification_engine import (
    ModificationEngine, create_modification_engine
)
from src.story.setting_extractor.completeness_checker import ReadinessAssessment
from src.story.creation.creation_decision import (
    CreationFlowManager, create_flow_manager, CreationContext
)


def print_section(title: str):
    """打印分隔符"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_basic_conversation():
    """演示1: 基础对话流程"""
    print_section("演示1: 基础对话流程")

    # 创建 Agent
    agent = create_agent(agent_type="streamlined", auto_complete=True, min_readiness=0.3)

    # 模拟用户对话
    conversation = [
        "我想写一个科幻小说",
        "主角是个黑客，要反抗大公司",
        "可以开始了"
    ]

    for user_msg in conversation:
        print(f"用户: {user_msg}")

        # 处理用户输入
        response = agent.process(user_msg)

        print(f"Agent: {response.message}")

        # 显示内部状态（用于演示，实际用户不可见）
        if response.metadata:
            print(f"  [内部] 就绪度: {response.metadata.get('readiness_score', 0):.2f}")
            print(f"  [内部] 应该创作: {response.should_create}")

        if response.should_create:
            print("  >>> AI 开始生成内容...")

    # 显示最终设定
    print_section("最终提取的设定（内部状态）")
    settings = agent.get_current_settings()
    print_settings_summary(settings)


def demo_implicit_completion():
    """演示2: 隐式AI补全"""
    print_section("演示2: 隐式AI补全")

    agent = create_agent(auto_complete=True)

    # 用户只提供极少量信息
    minimal_input = "写个关于勇敢骑士的故事"

    print(f"用户输入: {minimal_input}")
    print(f"（仅此一句话，AI 将自动补全所有缺失设定）\n")

    response = agent.process(minimal_input)

    # 显示补全后的设定
    settings = agent.get_current_settings()

    print("\n--- AI 自动补全后的完整设定 ---")
    if settings.characters:
        char = settings.characters[0]
        print(f"主角: {char.name or 'AI生成'}")
        print(f"  - 性格: {char.personality or 'AI补全'}")
        print(f"  - 背景: {char.background or 'AI补全'}")

    if settings.world:
        print(f"\n世界观:")
        print(f"  - 类型: {settings.world.world_type or 'AI推断'}")
        print(f"  - 时代: {settings.world.era or 'AI推断'}")

    if settings.plot:
        print(f"\n情节:")
        print(f"  - 冲突: {settings.plot.conflict or 'AI生成'}")

    readiness = agent.get_readiness_assessment()
    print(f"\n就绪度: {readiness.readiness_score:.2f}")
    print(f"自动补全项: {len(readiness.auto_completable)} 个")


def demo_modification_understanding():
    """演示3: 修改理解引擎"""
    print_section("演示3: 修改理解引擎")

    from src.story.setting_extractor.models import (
        ExtractedSettings, CharacterProfile, WorldSetting
    )

    # 创建初始设定
    settings = ExtractedSettings(
        characters=[
            CharacterProfile(
                name="Neo",
                personality="胆小，犹豫",
                role="主角"
            )
        ]
    )

    print("初始设定:")
    print(f"  主角: Neo - {settings.characters[0].personality}")

    # 创建修改引擎
    mod_engine = create_modification_engine()

    # 处理修改指令
    modification_requests = [
        "让Neo更勇敢一点",
        "让主角更果断",
        "把Neo改得更机智",
    ]

    for request in modification_requests:
        print(f"\n用户说: 「{request}」")

        result = mod_engine.process(request, settings)

        if result.success:
            settings = result.modified_settings
            print(f"  ✓ {result.changes_description[0] if result.changes_description else '已修改'}")

            # 显示更新后的角色
            char = settings.characters[0] if settings.characters else None
            if char:
                print(f"  → 当前性格: {char.personality}")


def demo_readiness_assessment():
    """演示4: 创作就绪度评估"""
    print_section("演示4: 创作就绪度评估")

    from src.story.setting_extractor.completeness_checker import BasicCompletenessChecker
    from src.story.setting_extractor.models import ExtractedSettings, CharacterProfile, WorldSetting

    checker = BasicCompletenessChecker(implicit_mode=True, min_readiness=0.3)

    # 测试不同完整度的设定
    test_cases = [
        ("完全空白", ExtractedSettings()),
        ("仅有角色", ExtractedSettings(
            characters=[CharacterProfile(name="小明")]
        )),
        ("基本设定", ExtractedSettings(
            characters=[CharacterProfile(name="Neo", role="主角", personality="勇敢")],
            world=WorldSetting(world_type="科幻", era="未来"),
        )),
    ]

    for name, settings in test_cases:
        assessment = checker.is_ready_for_creation(settings)

        print(f"\n{name}:")
        print(f"  就绪度: {assessment.readiness_score:.2f}")
        print(f"  可以创作: {'是' if assessment.is_ready else '否'}")
        print(f"  建议操作: {assessment.recommended_action}")

        if assessment.auto_completable:
            print(f"  AI将补全: {len(assessment.auto_completable)} 项")


def demo_creation_flow():
    """演示5: 完整创作流程"""
    print_section("演示5: 完整创作流程")

    # 创建组件
    agent = create_agent(auto_complete=True, min_readiness=0.3)
    flow_manager = create_flow_manager(engine_type="adaptive")
    mod_engine = create_modification_engine()

    # 完整对话流程
    conversation_flow = [
        {
            "user": "我想写个武侠小说",
            "context": "初始表达"
        },
        {
            "user": "主角是个江湖侠客",
            "context": "补充角色"
        },
        {
            "user": "他有一把剑",
            "context": "添加细节"
        },
        {
            "user": "开始写吧",
            "context": "明确要求创作"
        },
        {
            "user": "继续",
            "context": "继续创作"
        },
        {
            "user": "让主角更聪明一点",
            "context": "修改角色"
        },
        {
            "user": "继续写",
            "context": "修改后继续"
        },
    ]

    for turn in conversation_flow:
        user_msg = turn["user"]
        context = turn["context"]

        print(f"\n[{context}]")
        print(f"用户: {user_msg}")

        # 处理对话
        response = agent.process(user_msg)

        # 检查是否是修改意图
        if "更" in user_msg or "改" in user_msg:
            settings = agent.get_current_settings()
            mod_result = mod_engine.process(user_msg, settings)
            if mod_result.success:
                agent.state.current_settings = mod_result.modified_settings
                print(f"Agent: {response.message} ({mod_result.changes_description[0]})")
        else:
            print(f"Agent: {response.message}")

        # 检查创作决策
        creation_context = CreationContext(
            current_settings=agent.get_current_settings(),
            readiness_assessment=agent.get_readiness_assessment(),
            conversation_turn_count=agent.state.turn_count,
            last_user_message=user_msg,
            has_created_before=flow_manager.current_chapter > 0,
            last_chapter_created=flow_manager.current_chapter
        )

        decision = flow_manager.evaluate(creation_context)

        if decision.should_create:
            print(f"  >>> [创作决策] 开始创作第{decision.suggested_chapter}章")
            print(f"      策略: {decision.strategy.value}")
            print(f"      原因: {decision.reason}")

            # 模拟创作
            flow_manager.record_creation(decision, word_count=1000)

    # 显示最终统计
    print_section("创作统计")
    summary = flow_manager.get_creation_summary()
    print(f"当前章节: {summary['current_chapter']}")
    print(f"总字数: {summary['total_words']}")
    print(f"创作次数: {summary['creation_count']}")

    print_section("最终设定")
    settings = agent.get_current_settings()
    print_settings_summary(settings)


def print_settings_summary(settings):
    """打印设定摘要"""
    if settings.characters:
        print("\n【角色】")
        for char in settings.characters:
            print(f"  - {char.name or '未命名'} ({char.role or '未知'})")
            if char.personality:
                print(f"    性格: {char.personality}")
            if char.background:
                print(f"    背景: {char.background}")

    if settings.world:
        print("\n【世界观】")
        print(f"  - 类型: {settings.world.world_type or '未设定'}")
        print(f"  - 时代: {settings.world.era or '未设定'}")
        if settings.world.magic_system:
            print(f"  - 魔法系统: {settings.world.magic_system}")

    if settings.plot:
        print("\n【情节】")
        if settings.plot.conflict:
            print(f"  - 冲突: {settings.plot.conflict}")
        if settings.plot.inciting_incident:
            print(f"  - 起因: {settings.plot.inciting_incident}")

    if settings.style:
        print("\n【风格】")
        print(f"  - 视角: {settings.style.pov or '未设定'}")
        print(f"  - 基调: {settings.style.tone or '未设定'}")
        print(f"  - 节奏: {settings.style.pacing or '未设定'}")


def main():
    """运行所有演示"""
    print("""
╔════════════════════════════════════════════════════════════╗
║   对话式小说创作 Agent - 隐式设定提取演示                 ║
╚════════════════════════════════════════════════════════════╝
    """)

    demos = [
        ("基础对话流程", demo_basic_conversation),
        ("隐式AI补全", demo_implicit_completion),
        ("修改理解引擎", demo_modification_understanding),
        ("创作就绪度评估", demo_readiness_assessment),
        ("完整创作流程", demo_creation_flow),
    ]

    for name, demo_func in demos:
        try:
            demo_func()
            input("\n按回车继续下一个演示...")
        except Exception as e:
            print(f"\n演示出错: {e}")
            import traceback
            traceback.print_exc()

    print("\n所有演示完成！")


if __name__ == "__main__":
    main()
