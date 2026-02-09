"""
Google Gemini API provider.

This module integrates with Google's Gemini API for content generation.
Supports Gemini Pro and other Gemini models.
"""

import os
from typing import AsyncIterator, Optional
from .base import (
    LLMProvider, LLMRequest, LLMResponse, LLMStreamChunk,
    Message, MessageRole, with_retry
)


class GeminiLLMProvider(LLMProvider):
    """
    LLM provider for Google Gemini API.

    Supports Gemini Pro, Gemini Flash, and other Gemini models.
    """

    DEFAULT_MODEL = "gemini-2.0-flash-exp"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = DEFAULT_MODEL,
                 timeout: int = 120,
                 max_retries: int = 3):
        """
        Initialize the Gemini provider.

        Args:
            api_key: Google API key (defaults to GEMINI_API_KEY env var)
            model: Model to use (e.g., gemini-2.0-flash-exp, gemini-1.5-pro)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None

        # Build API URL
        self.api_url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        self.stream_url = f"{self.BASE_URL}/{self.model}:streamGenerateContent?key={self.api_key}"

    def _get_client(self):
        """Lazy initialization of the HTTP client."""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(
                    timeout=self.timeout,
                    headers={"content-type": "application/json"}
                )
            except ImportError:
                raise ImportError(
                    "httpx is required for Gemini provider. "
                    "Install it with: pip install httpx"
                )
        return self._client

    def _convert_messages_to_gemini_format(self, messages: list) -> dict:
        """
        Convert messages to Gemini API format.

        Gemini uses a different format with 'contents' array.
        System message should be in the top-level 'system_instruction'.
        """
        contents = []
        system_instruction = None

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_instruction = msg.content
            else:
                role = "user" if msg.role == MessageRole.USER else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })

        result = {"contents": contents}
        if system_instruction:
            result["system_instruction"] = {
                "parts": [{"text": system_instruction}]
            }

        return result

    @with_retry(max_retries=3, delay=1.0)
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response using Gemini API."""
        client = self._get_client()

        # Prepare request payload
        gemini_content = self._convert_messages_to_gemini_format(request.messages)

        payload = {
            **gemini_content,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
                "topP": request.top_p,
            }
        }

        # Add stop sequences if provided
        if request.stop_sequences:
            payload["generationConfig"]["stopSequences"] = request.stop_sequences

        # Make request
        response = client.post(self.api_url, json=payload)

        # Handle errors
        if response.status_code != 200:
            error_msg = f"Gemini API error: {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
            except:
                error_msg += f" - {response.text}"
            raise Exception(error_msg)

        data = response.json()

        # Parse response
        try:
            text = ""
            candidates = data.get("candidates", [])
            if candidates and len(candidates) > 0:
                content_parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(part.get("text", "") for part in content_parts)

            finish_reason = candidates[0].get("finishReason", "STOP") if candidates else "STOP"

            usage_metadata = data.get("usageMetadata", {})

            return LLMResponse(
                content=text,
                model=data.get("modelVersion", self.model),
                finish_reason=finish_reason.lower(),
                usage={
                    "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                    "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                    "total_tokens": usage_metadata.get("totalTokenCount", 0),
                }
            )
        except (KeyError, IndexError) as e:
            raise Exception(f"Failed to parse Gemini response: {e}")

    async def generate_async(self, request: LLMRequest) -> LLMResponse:
        """Generate a response asynchronously."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, request)

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Stream a response from Gemini API."""
        gemini_content = self._convert_messages_to_gemini_format(request.messages)

        payload = {
            **gemini_content,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
                "topP": request.top_p,
            }
        }

        if request.stop_sequences:
            payload["generationConfig"]["stopSequences"] = request.stop_sequences

        try:
            import httpx
        except ImportError:
            raise ImportError("httpx is required for streaming")

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={"content-type": "application/json"}
        ) as async_client:
            async with async_client.stream("POST", self.stream_url, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"Gemini API error: {response.status_code} - {error_text}")

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        import json
                        data = json.loads(line)

                        candidates = data.get("candidates", [])
                        if candidates and len(candidates) > 0:
                            content_parts = candidates[0].get("content", {}).get("parts", [])
                            for part in content_parts:
                                text = part.get("text", "")
                                if text:
                                    # Check if this is the final chunk
                                    finish_reason = candidates[0].get("finishReason", "")
                                    is_final = finish_reason in ("STOP", "MAX_TOKENS", "SAFETY", "RECITATION")

                                    yield LLMStreamChunk(content=text, is_final=is_final)
                                    if is_final:
                                        return
                    except json.JSONDecodeError:
                        continue

    def count_tokens(self, text: str) -> int:
        """
        Count tokens for Gemini.

        Gemini uses a similar tokenization to other models.
        Rough approximation: ~4 chars per token for English,
        ~1.5-2 chars per token for Chinese.
        """
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)


__all__ = ["GeminiLLMProvider"]
