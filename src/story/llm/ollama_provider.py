"""
Ollama API provider.

This module integrates with Ollama for local LLM inference.
Supports all models available through Ollama (Llama, Mistral, etc.).
"""

import os
from typing import AsyncIterator, Optional, List
from .base import (
    LLMProvider, LLMRequest, LLMResponse, LLMStreamChunk,
    Message, MessageRole, with_retry
)


class OllamaLLMProvider(LLMProvider):
    """
    LLM provider for Ollama.

    Ollama is a local LLM runner that supports various open-source models.
    """

    DEFAULT_MODEL = "llama3.2"
    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(self,
                 model: str = DEFAULT_MODEL,
                 base_url: Optional[str] = None,
                 timeout: int = 300,
                 max_retries: int = 2):
        """
        Initialize the Ollama provider.

        Args:
            model: Model name (e.g., llama3.2, mistral, codellama)
            base_url: Ollama API base URL (defaults to OLLAMA_BASE_URL env var or localhost:11434)
            timeout: Request timeout in seconds (local models may need more time)
            max_retries: Maximum number of retries
        """
        self.model = model
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", self.DEFAULT_BASE_URL)
        self.base_url = self.base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None

        self.api_url = f"{self.base_url}/api/chat"
        self.generate_url = f"{self.base_url}/api/generate"
        self.tags_url = f"{self.base_url}/api/tags"

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
                    "httpx is required for Ollama provider. "
                    "Install it with: pip install httpx"
                )
        return self._client

    def _convert_messages_to_ollama_format(self, messages: list) -> list:
        """
        Convert messages to Ollama API format.

        Ollama uses 'role' and 'content' fields.
        """
        ollama_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Ollama doesn't have a separate system role,
                # we can prepend to first user message or use a system prefix
                ollama_messages.append({
                    "role": "system",
                    "content": msg.content
                })
            else:
                role = "user" if msg.role == MessageRole.USER else "assistant"
                ollama_messages.append({
                    "role": role,
                    "content": msg.content
                })

        return ollama_messages

    @with_retry(max_retries=2, delay=1.0)
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response using Ollama API."""
        client = self._get_client()

        # Prepare request payload
        messages = self._convert_messages_to_ollama_format(request.messages)

        payload = {
            "model": request.model or self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
                "top_p": request.top_p,
            }
        }

        # Add stop sequences if provided
        if request.stop_sequences:
            payload["options"]["stop"] = request.stop_sequences

        # Make request
        response = client.post(self.api_url, json=payload)

        # Handle errors
        if response.status_code != 200:
            error_msg = f"Ollama API error: {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f" - {error_data.get('error', 'Unknown error')}"
            except:
                error_msg += f" - {response.text}"
            raise Exception(error_msg)

        data = response.json()

        # Parse response
        text = data.get("message", {}).get("content", "")

        return LLMResponse(
            content=text,
            model=data.get("model", self.model),
            finish_reason=data.get("done", True) and "stop" or "length",
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            }
        )

    async def generate_async(self, request: LLMRequest) -> LLMResponse:
        """Generate a response asynchronously."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, request)

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Stream a response from Ollama API."""
        messages = self._convert_messages_to_ollama_format(request.messages)

        payload = {
            "model": request.model or self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
                "top_p": request.top_p,
            }
        }

        if request.stop_sequences:
            payload["options"]["stop"] = request.stop_sequences

        try:
            import httpx
        except ImportError:
            raise ImportError("httpx is required for streaming")

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={"content-type": "application/json"}
        ) as async_client:
            async with async_client.stream("POST", self.api_url, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"Ollama API error: {response.status_code} - {error_text}")

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        import json
                        data = json.loads(line)

                        # Check if done
                        if data.get("done"):
                            yield LLMStreamChunk(content="", is_final=True)
                            return

                        # Extract content
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield LLMStreamChunk(content=content, is_final=False)

                    except json.JSONDecodeError:
                        continue

    def count_tokens(self, text: str) -> int:
        """
        Count tokens (rough approximation for Ollama models).

        Ollama uses various tokenizers depending on the model.
        This is a rough estimate that works reasonably well.
        """
        # Rough estimate: ~4 chars per token for English
        # For Chinese, ~1.5-2 chars per token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)

    def list_models(self) -> List[str]:
        """
        List available models in Ollama.

        Returns:
            List of model names
        """
        client = self._get_client()

        try:
            response = client.get(self.tags_url)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return [model.get("name", "") for model in models]
        except Exception as e:
            print(f"Failed to list Ollama models: {e}")

        return []

    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama library.

        Args:
            model_name: Name of the model to pull

        Returns:
            True if successful
        """
        client = self._get_client()

        pull_url = f"{self.base_url}/api/pull"
        payload = {"name": model_name, "stream": False}

        try:
            response = client.post(pull_url, json=payload, timeout=600)  # 10 min timeout
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to pull Ollama model: {e}")
            return False


__all__ = ["OllamaLLMProvider"]
