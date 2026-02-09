"""
LLM integration base module.

This module provides the abstract interface for LLM integration,
supporting multiple providers (OpenAI, Anthropic Claude, etc.) and
mock implementations for testing.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
import json


class MessageRole(Enum):
    """Role of a message in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """A message in the conversation."""
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        """Convert to API format."""
        return {"role": self.role.value, "content": self.content}

    def to_claude_format(self) -> Dict[str, str]:
        """Convert to Claude API format."""
        return {"role": self.role.value, "content": self.content}


@dataclass
class LLMRequest:
    """Request to LLM."""
    messages: List[Message]
    model: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    top_k: int = -1
    stream: bool = False
    stop_sequences: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to API request format."""
        return {
            "model": self.model,
            "messages": [m.to_dict() for m in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stream": self.stream,
        }


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    finish_reason: str = "stop"
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.content


@dataclass
class LLMStreamChunk:
    """A chunk of streaming response."""
    content: str
    is_final: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            request: The LLM request

        Returns:
            LLMResponse with generated content
        """
        pass

    @abstractmethod
    async def generate_async(self, request: LLMRequest) -> LLMResponse:
        """Generate a response asynchronously."""
        pass

    @abstractmethod
    def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Stream a response from the LLM."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider for testing and development.

    This provider returns predefined responses without making
    actual API calls. Useful for testing and offline development.
    """

    def __init__(self, response_templates: Optional[Dict[str, str]] = None):
        """
        Initialize the mock provider.

        Args:
            response_templates: Optional mapping of context to responses
        """
        self.response_templates = response_templates or {}
        self.call_count = 0
        self.last_request: Optional[LLMRequest] = None

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a mock response."""
        self.call_count += 1
        self.last_request = request

        # Check for template match
        user_content = request.messages[-1].content if request.messages else ""
        for key, template in self.response_templates.items():
            if key in user_content:
                return LLMResponse(
                    content=template,
                    model=request.model,
                    finish_reason="stop",
                    usage={"prompt_tokens": 100, "completion_tokens": 200}
                )

        # Generate contextual mock response
        content = self._generate_mock_content(user_content)

        return LLMResponse(
            content=content,
            model=request.model,
            finish_reason="stop",
            usage={"prompt_tokens": 100, "completion_tokens": 200}
        )

    async def generate_async(self, request: LLMRequest) -> LLMResponse:
        """Generate a mock response asynchronously."""
        return self.generate(request)

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Stream a mock response."""
        response = self.generate(request)
        words = response.content.split()

        for i, word in enumerate(words):
            chunk = word + " "
            yield LLMStreamChunk(
                content=chunk,
                is_final=(i == len(words) - 1)
            )

    def count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        return len(text.split()) * 1.3  # Rough estimate

    def _generate_mock_content(self, user_input: str) -> str:
        """Generate mock content based on input."""
        if "第一章" in user_input or "开始" in user_input or "chapter 1" in user_input.lower():
            return """# 第一章

天空阴沉沉的，乌云密布，仿佛要压下来一般。

李明站在窗前，望着远处渐渐聚集的人群，心中涌起一股不安。他不知道，今天将是他命运转折的开始。

门外传来了急促的敲门声。

"谁？"李明问道，声音有些颤抖。

"快递，"一个低沉的声音回答道，但李明记得自己并没有订购任何东西。

他犹豫了一下，还是走向门口。当他的手触碰到门把手的那一刻，他感觉到了一阵奇怪的寒意...

门缓缓打开了，门外站着一个穿着黑色风衣的男人，脸上戴着一副墨镜，让人看不清他的面容。

"你是李明吗？"男人问道。

"我是，你是？"

"我是来帮你的，"男人说，"或者说，我们是来帮你的。"

李明皱起眉头，完全不明白对方在说什么。但当他看到男人身后又走出两个人影时，他意识到，这一切恐怕不是什么简单的误会。

"""
        elif "续" in user_input or "continue" in user_input.lower() or "next" in user_input.lower():
            return """李明退后一步，试图与这些人保持距离。

"我不明白你们在说什么，"他说，"如果这是一个玩笑，那一点也不好笑。"

黑衣男人摇了摇头，嘴角露出一丝苦笑。"我也希望这是个玩笑，相信我。但时间不多了，我们必须立刻离开这里。"

"离开？去哪里？"

"去一个安全的地方，"男人说，"有人要找你，而他们不是什么好人。"

就在这时，远处传来了一声巨响，像是爆炸的声音。黑衣男人脸色一变，立刻抓住了李明的手臂。

"快！没时间解释了！"他大声说道，拉着李明向楼道跑去。

李明被这突如其来的变故吓懵了，双腿几乎是机械地跟着对方奔跑。当他们冲进楼梯间时，他听到楼下传来了急促的脚步声和喊叫声。

"他们来了，"另一个黑衣人说道，"我们得走楼梯。"

三人开始沿着楼梯向上攀爬。李明的心脏剧烈地跳动着，他不明白发生了什么，但他知道一件事——他的生活，从今天开始，将永远改变。

当他们爬上屋顶时，李明看到了让他终生难忘的一幕：远处的城市中心，一股巨大的烟柱正在升起，而在烟雾之中，有什么东西在闪烁着诡异的光芒。

"那是什么？"李明惊恐地问道。

"那是我们一直在等待的，"黑衣男人说，"也是你一直在等待的，虽然你自己可能并不知道。"

"""
        else:
            return """这是根据您的设定生成的内容。请确保已配置真实的 LLM API 来获得高质量的内容生成。

当前使用的是 Mock LLM Provider，仅用于测试和演示。

要使用真实的 LLM，请配置 API 密钥并切换到实际的 Provider。"""


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    provider: str = "mock"  # mock, openai, anthropic, etc.
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }


def create_llm_provider(config: LLMConfig = None) -> LLMProvider:
    """
    Factory function to create LLM providers.

    Args:
        config: LLM configuration (defaults to env vars)

    Returns:
        Configured LLMProvider instance
    """
    import os

    # Use env vars if config not provided
    if config is None:
        # Auto-detect provider from env vars (priority order)
        if os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
            api_key = os.getenv("ANTHROPIC_API_KEY")
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            base_url = None
        elif os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
            provider = "azure-openai"
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
            base_url = os.getenv("AZURE_OPENAI_ENDPOINT")
        elif os.getenv("GEMINI_API_KEY"):
            provider = "gemini"
            api_key = os.getenv("GEMINI_API_KEY")
            model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
            base_url = None
        elif os.getenv("OLLAMA_BASE_URL") or provider == "ollama":
            provider = "ollama"
            api_key = None
            model = os.getenv("OLLAMA_MODEL", "llama3.2")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        else:
            provider = "openai"
            api_key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("OPENAI_MODEL", "gpt-4")
            base_url = os.getenv("OPENAI_BASE_URL")

        config = LLMConfig(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model
        )

    provider_type = config.provider.lower()

    if provider_type == "mock":
        return MockLLMProvider()
    elif provider_type in ("anthropic", "claude"):
        from .claude_provider import ClaudeLLMProvider
        return ClaudeLLMProvider(
            api_key=config.api_key,
            model=config.model,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
    elif provider_type in ("openai", "gpt"):
        from .openai_provider import OpenAILLMProvider
        return OpenAILLMProvider(
            api_key=config.api_key,
            model=config.model,
            timeout=config.timeout,
            max_retries=config.max_retries,
            base_url=config.base_url
        )
    elif provider_type in ("azure", "azure-openai", "azureopenai"):
        from .azure_openai_provider import AzureOpenAILLMProvider
        return AzureOpenAILLMProvider(
            api_key=config.api_key,
            endpoint=config.base_url or os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", config.model),
            model=config.model,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
    elif provider_type == "gemini":
        from .gemini_provider import GeminiLLMProvider
        return GeminiLLMProvider(
            api_key=config.api_key,
            model=config.model,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
    elif provider_type == "ollama":
        from .ollama_provider import OllamaLLMProvider
        return OllamaLLMProvider(
            model=config.model,
            base_url=config.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            timeout=config.timeout,
            max_retries=config.max_retries
        )
    else:
        raise ValueError(f"Unknown LLM provider: {config.provider}")


# Retry decorator for LLM calls
def with_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator to add retry logic to LLM calls."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            import time
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        raise

        return wrapper
    return decorator
