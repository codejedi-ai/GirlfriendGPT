"""LiteLLM adapter for GirlfriendGPT."""

from __future__ import annotations

from typing import Any, Dict, List, AsyncIterator, Optional

from .base import BaseProvider, ProviderConfig, ChatMessage, ChatResponse


class LiteLLMAdapter(BaseProvider):
    """Adapter for LLM providers via LiteLLM.

    This adapter uses LiteLLM to provide a unified interface
    to multiple LLM providers (OpenAI, Anthropic, Cohere, etc.).

    Requires: pip install litellm
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the LiteLLM adapter.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._client = None

    def _get_client(self):
        """Get or create the LiteLLM client."""
        if self._client is None:
            try:
                import litellm

                litellm.api_key = self.config.api_key
                if self.config.endpoint:
                    litellm.api_base = self.config.endpoint
                self._client = litellm
            except ImportError:
                raise ImportError(
                    "LiteLLM not installed. Run: pip install litellm"
                )
        return self._client

    @property
    def name(self) -> str:
        """Get the provider name."""
        # Extract provider from model name (e.g., "openai/gpt-4" -> "openai")
        model = self.config.model
        if "/" in model:
            return model.split("/")[0]
        return "unknown"

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponse:
        """Get a chat completion.

        Args:
            messages: List of chat messages
            **kwargs: Additional options

        Returns:
            Chat response
        """
        client = self._get_client()

        # Convert messages to dict format
        message_dicts = [
            {"role": m.role, "content": m.content, "name": m.name}
            for m in messages
            if m.content
        ]

        # Set defaults
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        temperature = kwargs.get("temperature", self.config.temperature)

        # Call LiteLLM
        response = await client.acompletion(
            model=self.config.model,
            messages=message_dicts,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        # Extract response
        content = response.choices[0].message.content or ""
        usage = (
            {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            if hasattr(response, "usage")
            else {}
        )

        return ChatResponse(
            content=content,
            model=self.config.model,
            usage=usage,
            finish_reason=response.choices[0].finish_reason,
        )

    async def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a chat completion.

        Args:
            messages: List of chat messages
            **kwargs: Additional options

        Yields:
            Chunks of response content
        """
        client = self._get_client()

        # Convert messages to dict format
        message_dicts = [
            {"role": m.role, "content": m.content, "name": m.name}
            for m in messages
            if m.content
        ]

        # Set defaults
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        temperature = kwargs.get("temperature", self.config.temperature)

        # Stream with LiteLLM
        stream = await client.acompletion(
            model=self.config.model,
            messages=message_dicts,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            **kwargs,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def validate_connection(self) -> bool:
        """Validate the provider connection.

        Returns:
            True if connection is valid
        """
        try:
            # Simple test with minimal tokens
            response = await self.chat_completion(
                [ChatMessage(role="user", content="Hi")],
                max_tokens=5,
            )
            return bool(response.content)
        except Exception:
            return False
