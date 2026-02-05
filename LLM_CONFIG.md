# LLM 配置说明

## 配置方式

在项目根目录创建 `.env` 文件：

```bash
# LLM API Configuration
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=http://your-api-endpoint/v1
OPENAI_MODEL=your_model_name
```

## 当前配置

```
OPENAI_API_KEY=20021214Ytq@.
OPENAI_BASE_URL=http://154.64.236.74:8045/v1
OPENAI_MODEL=gemini-2.0-flash-exp
```

## 支持的 API 格式

兼容 OpenAI API 格式的服务都可以使用：

- **OpenAI 官方**：`https://api.openai.com/v1`
- **Azure OpenAI**：`https://your-resource.openai.azure.com/openai/deployments/your-deployment`
- **第三方代理**：任何兼容 OpenAI API 格式的服务
- **本地模型**：如 Ollama (`http://localhost:11434/v1`)

## 使用方式

### 1. 在代码中创建 Provider

```python
from src.story.llm import create_llm_provider, Message, MessageRole, LLMRequest

# 自动从环境变量读取配置
llm = create_llm_provider()

# 生成内容
request = LLMRequest(
    messages=[
        Message(role=MessageRole.SYSTEM, content="你是一个作家"),
        Message(role=MessageRole.USER, content="写一个故事开头")
    ],
    temperature=0.7,
    max_tokens=500
)

response = llm.generate(request)
print(response.content)
```

### 2. 使用故事生成器

```python
from src.story.llm import create_llm_provider
from src.story.generation import create_story_generator
from src.story.setting_extractor.models import ExtractedSettings, CharacterProfile

# 创建生成器（自动使用 .env 配置）
story_gen = create_story_generator(create_llm_provider())

# 创建设定
settings = ExtractedSettings(
    characters=[CharacterProfile(name="主角", role="主角")]
)

# 生成章节
chapter = story_gen.generate_chapter(settings, chapter_number=1)
print(chapter.content)
```

## 测试配置

运行测试脚本验证配置：

```bash
python3 examples/test_llm_config.py
```

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | API 密钥 | 必填 |
| `OPENAI_BASE_URL` | API 端点（不含 `/chat/completions` 会自动添加） | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | 模型名称 | `gpt-4` |
| `ANTHROPIC_API_KEY` | Claude API 密钥（可选） | - |
