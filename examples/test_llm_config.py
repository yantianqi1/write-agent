"""
测试 LLM 配置

验证 API 配置是否正确工作。
"""

import sys
import os
sys.path.insert(0, '/root/write-agent')

# 加载 .env 文件
from pathlib import Path
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

from src.story.llm import create_llm_provider, Message, MessageRole, LLMRequest

def test_llm_connection():
    """测试 LLM 连接"""
    print("="*60)
    print("  LLM 配置测试")
    print("="*60)

    # 显示当前配置
    print(f"\n当前环境变量:")
    print(f"  OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', '未设置')[:20]}...")
    print(f"  OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL', '未设置')}")
    print(f"  OPENAI_MODEL: {os.getenv('OPENAI_MODEL', '未设置')}")

    try:
        # 创建 provider
        print(f"\n正在创建 LLM Provider...")
        llm = create_llm_provider()
        print(f"✅ Provider 创建成功")

        # 测试生成
        print(f"\n正在测试内容生成...")

        request = LLMRequest(
            messages=[
                Message(role=MessageRole.SYSTEM, content="你是一个简洁的助手。"),
                Message(role=MessageRole.USER, content="用一句话介绍你自己。")
            ],
            temperature=0.7,
            max_tokens=100,
        )

        response = llm.generate(request)

        print(f"\n✅ 生成成功!")
        print(f"\n响应内容:")
        print(f"  {response.content[:200]}")

        if response.usage:
            print(f"\nToken 使用:")
            print(f"  输入: {response.usage.get('prompt_tokens', 'N/A')}")
            print(f"  输出: {response.usage.get('completion_tokens', 'N/A')}")

        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_story_generation():
    """测试故事内容生成"""
    print("\n" + "="*60)
    print("  故事内容生成测试")
    print("="*60)

    from src.story.llm import create_llm_provider, Message, MessageRole, LLMRequest
    from src.story.setting_extractor.models import ExtractedSettings, CharacterProfile, WorldSetting

    try:
        # 创建 provider
        llm = create_llm_provider()

        # 创建简单设定
        settings = ExtractedSettings(
            characters=[CharacterProfile(name="李明", role="主角")],
            world=WorldSetting(world_type="科幻", era="未来"),
        )

        # 构建提示词
        system_prompt = "你是一位小说作家。根据设定创作一段简短的开头。"
        user_prompt = f"""设定：
- 世界类型：{settings.world.world_type}
- 时代：{settings.world.era}
- 主角：{settings.characters[0].name}

请写一个100字左右的故事开头。"""

        request = LLMRequest(
            messages=[
                Message(role=MessageRole.SYSTEM, content=system_prompt),
                Message(role=MessageRole.USER, content=user_prompt)
            ],
            temperature=0.8,
            max_tokens=500,
        )

        response = llm.generate(request)

        print(f"\n✅ 故事生成成功!")
        print(f"\n生成的内容:")
        print(f"  {response.content}")

        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


if __name__ == "__main__":
    print("开始测试 LLM 配置...\n")

    success = test_llm_connection()

    if success:
        print("\n" + "="*60)
        test_story_generation()

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
