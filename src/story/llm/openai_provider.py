"""
OpenAI API provider.

This module integrates with OpenAI's API for content generation.
Supports GPT-4 and other OpenAI models.
"""

import os
from typing import AsyncIterator, Optional
from .base import (
    LLMProvider, LLMRequest, LLMResponse, LLMStreamChunk,
    Message, MessageRole, with_retry
)


class OpenAILLMProvider(LLMProvider):
    """
    LLM provider for OpenAI API.

    Supports GPT-4, GPT-4-turbo, and GPT-3.5-turbo.
    """

    DEFAULT_MODEL = "gpt-4-turbo-preview"
    BASE_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = DEFAULT_MODEL,
                 timeout: int = 120,
                 max_retries: int = 3,
                 base_url: Optional[str] = None):
        """
        Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            base_url: Optional custom base URL
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")

        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        # Process base_url
        if base_url:
            # If base_url doesn't end with /chat/completions, add it
            if not base_url.endswith("/chat/completions"):
                # Check if it ends with /v1
                if base_url.endswith("/v1"):
                    base_url = base_url + "/chat/completions"
                elif base_url.endswith("/"):
                    base_url = base_url + "v1/chat/completions"
                else:
                    base_url = base_url + "/v1/chat/completions"
            self.base_url = base_url
        else:
            self.base_url = self.BASE_URL
        self._client = None

    def _get_client(self):
        """Lazy initialization of the HTTP client."""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(
                    timeout=self.timeout,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "content-type": "application/json"
                    }
                )
            except ImportError:
                raise ImportError(
                    "httpx is required for OpenAI provider. "
                    "Install it with: pip install httpx"
                )
        return self._client

    @with_retry(max_retries=3, delay=1.0)
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response using OpenAI API."""
        client = self._get_client()

        # Prepare request payload
        messages = [{"role": m.role.value, "content": m.content} for m in request.messages]

        payload = {
            "model": request.model or self.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        if request.top_p != 0.9:
            payload["top_p"] = request.top_p

        if request.stop_sequences:
            payload["stop"] = request.stop_sequences

        # Make request
        response = client.post(self.base_url, json=payload)

        # Handle errors
        if response.status_code != 200:
            error_msg = f"OpenAI API error: {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
            except:
                error_msg += f" - {response.text}"
            raise Exception(error_msg)

        data = response.json()

        # Parse response
        choice = data.get("choices", [{}])[0]
        text = choice.get("message", {}).get("content", "")

        return LLMResponse(
            content=text,
            model=data.get("model", self.model),
            finish_reason=choice.get("finish_reason", "stop"),
            usage={
                "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": data.get("usage", {}).get("total_tokens", 0),
            }
        )

    async def generate_async(self, request: LLMRequest) -> LLMResponse:
        """Generate a response asynchronously."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, request)

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Stream a response from OpenAI API."""
        messages = [{"role": m.role.value, "content": m.content} for m in request.messages]

        payload = {
            "model": request.model or self.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True,
        }

        try:
            import httpx
        except ImportError:
            raise ImportError("httpx is required for streaming")

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "content-type": "application/json"
            }
        ) as async_client:
            async with async_client.stream("POST", self.base_url, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"OpenAI API error: {response.status_code} - {error_text}")

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            yield LLMStreamChunk(content="", is_final=True)
                            break

                        try:
                            import json
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            text = delta.get("content", "")
                            if text:
                                yield LLMStreamChunk(content=text, is_final=False)
                        except json.JSONDecodeError:
                            continue

    def count_tokens(self, text: str) -> int:
        """Count tokens (rough approximation)."""
        # Use tiktoken if available
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except ImportError:
            # Fallback to rough estimate
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            other_chars = len(text) - chinese_chars
            return int(chinese_chars / 1.5 + other_chars / 4)
