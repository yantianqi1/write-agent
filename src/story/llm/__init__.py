"""
LLM integration module.

Provides unified interface for multiple LLM providers including
Anthropic Claude, OpenAI GPT, and mock implementations for testing.
"""

from .base import (
    # Enums
    MessageRole,
    # Data classes
    Message,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    LLMConfig,
    # Providers
    LLMProvider,
    MockLLMProvider,
    # Factory
    create_llm_provider,
    # Decorator
    with_retry
)

__all__ = [
    "MessageRole",
    "Message",
    "LLMRequest",
    "LLMResponse",
    "LLMStreamChunk",
    "LLMConfig",
    "LLMProvider",
    "MockLLMProvider",
    "create_llm_provider",
    "with_retry",
]

__version__ = "0.1.0"
