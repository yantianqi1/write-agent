"""
Anthropic Claude API provider.

This module integrates with Anthropic's Claude API for content generation.
"""

import os
import time
from typing import AsyncIterator, Optional
from .base import (
    LLMProvider, LLMRequest, LLMResponse, LLMStreamChunk,
    Message, MessageRole, with_retry
)


class ClaudeLLMProvider(LLMProvider):
    """
    LLM provider for Anthropic's Claude API.

    Supports Claude 3.5 Sonnet and other Claude models.
    """

    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    BASE_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = DEFAULT_MODEL,
                 timeout: int = 120,
                 max_retries: int = 3):
        """
        Initialize the Claude provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None

    def _get_client(self):
        """Lazy initialization of the HTTP client."""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(
                    timeout=self.timeout,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    }
                )
            except ImportError:
                raise ImportError(
                    "httpx is required for Claude provider. "
                    "Install it with: pip install httpx"
                )
        return self._client

    @with_retry(max_retries=3, delay=1.0)
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response using Claude API."""
        client = self._get_client()

        # Prepare request payload
        messages = [m.to_dict() for m in request.messages]
        system_message = None

        # Extract system message if present
        if messages and messages[0]["role"] == "system":
            system_message = messages.pop(0)["content"]

        payload = {
            "model": request.model or self.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        if system_message:
            payload["system"] = system_message

        if request.top_p != 0.9:
            payload["top_p"] = request.top_p

        if request.stop_sequences:
            payload["stop_sequences"] = request.stop_sequences

        # Make request
        response = client.post(
            self.BASE_URL,
            json=payload
        )

        # Handle errors
        if response.status_code != 200:
            error_msg = f"Claude API error: {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
            except:
                error_msg += f" - {response.text}"
            raise Exception(error_msg)

        data = response.json()

        # Parse response
        content = data.get("content", [])
        if content and len(content) > 0:
            text = "".join(block.get("text", "") for block in content if block.get("type") == "text")
        else:
            text = ""

        return LLMResponse(
            content=text,
            model=data.get("model", self.model),
            finish_reason=data.get("stop_reason", "stop"),
            usage={
                "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
            }
        )

    async def generate_async(self, request: LLMRequest) -> LLMResponse:
        """Generate a response asynchronously."""
        client = self._get_client()

        # For async, we'd use httpx.AsyncClient
        # For now, use sync version in thread pool
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, request)

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Stream a response from Claude API."""
        client = self._get_client()

        # Prepare request payload
        messages = [m.to_dict() for m in request.messages]
        system_message = None

        if messages and messages[0]["role"] == "system":
            system_message = messages.pop(0)["content"]

        payload = {
            "model": request.model or self.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": True,
        }

        if system_message:
            payload["system"] = system_message

        # Use httpx for streaming
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx is required for streaming")

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        ) as async_client:
            async with async_client.stream("POST", self.BASE_URL, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"Claude API error: {response.status_code} - {error_text}")

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            yield LLMStreamChunk(content="", is_final=True)
                            break

                        try:
                            import json
                            data = json.loads(data_str)
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                text = delta.get("text", "")
                                if text:
                                    yield LLMStreamChunk(content=text, is_final=False)
                        except json.JSONDecodeError:
                            continue

    def count_tokens(self, text: str) -> int:
        """Count tokens using Claude's tokenization."""
        # Rough approximation: ~4 chars per token for English
        # For Chinese, ~1.5-2 chars per token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)


class ClaudeLLMProviderAsync(ClaudeLLMProvider):
    """
    Async version of Claude LLM provider.

    Uses httpx.AsyncClient for better async performance.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the async Claude provider."""
        super().__init__(*args, **kwargs)
        self._async_client = None

    def _get_async_client(self):
        """Get or create the async HTTP client."""
        if self._async_client is None:
            try:
                import httpx
                self._async_client = httpx.AsyncClient(
                    timeout=self.timeout,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    }
                )
            except ImportError:
                raise ImportError("httpx is required for Claude provider")
        return self._async_client

    @with_retry(max_retries=3, delay=1.0)
    async def generate_async(self, request: LLMRequest) -> LLMResponse:
        """Generate a response asynchronously."""
        client = await self._get_async_client()

        messages = [m.to_dict() for m in request.messages]
        system_message = None

        if messages and messages[0]["role"] == "system":
            system_message = messages.pop(0)["content"]

        payload = {
            "model": request.model or self.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        if system_message:
            payload["system"] = system_message

        response = await client.post(self.BASE_URL, json=payload)

        if response.status_code != 200:
            error_msg = f"Claude API error: {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
            except:
                error_msg += f" - {response.text}"
            raise Exception(error_msg)

        data = response.json()

        content = data.get("content", [])
        if content and len(content) > 0:
            text = "".join(block.get("text", "") for block in content if block.get("type") == "text")
        else:
            text = ""

        return LLMResponse(
            content=text,
            model=data.get("model", self.model),
            finish_reason=data.get("stop_reason", "stop"),
            usage={
                "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
            }
        )

    async def close(self):
        """Close the async client."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None
