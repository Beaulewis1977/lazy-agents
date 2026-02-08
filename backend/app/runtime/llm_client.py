"""
LLM Client - Unified interface for multiple LLM providers.
Supports OpenAI, Anthropic, and Google's Gemini.
"""

import json
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings


@dataclass
class LLMMessage:
    """A message in a conversation."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM."""

    content: str
    model: str
    tokens_input: int
    tokens_output: int
    finish_reason: str
    raw_response: dict[str, Any]


class BaseLLMClient(ABC):
    """Base class for LLM clients."""

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        """Send a chat completion request."""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Stream a chat completion response."""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"

    async def chat(
        self,
        messages: list[LLMMessage],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        async with httpx.AsyncClient() as client:
            payload = {
                "model": model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"

            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            usage = data.get("usage", {})

            return LLMResponse(
                content=choice["message"]["content"] or "",
                model=data["model"],
                tokens_input=usage.get("prompt_tokens", 0),
                tokens_output=usage.get("completion_tokens", 0),
                finish_reason=choice.get("finish_reason", "unknown"),
                raw_response=data,
            )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        async with (
            httpx.AsyncClient() as client,
            client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
                timeout=120.0,
            ) as response,
        ):
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.base_url = "https://api.anthropic.com/v1"

    async def chat(
        self,
        messages: list[LLMMessage],
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")

        # Separate system message
        system = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        async with httpx.AsyncClient() as client:
            payload = {
                "model": model,
                "messages": chat_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            if system:
                payload["system"] = system

            if tools:
                # Convert OpenAI tool format to Anthropic format
                payload["tools"] = [
                    {
                        "name": t["function"]["name"],
                        "description": t["function"].get("description", ""),
                        "input_schema": t["function"].get("parameters", {}),
                    }
                    for t in tools
                ]

            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()

            content = ""
            for block in data.get("content", []):
                if block["type"] == "text":
                    content += block["text"]

            return LLMResponse(
                content=content,
                model=data["model"],
                tokens_input=data.get("usage", {}).get("input_tokens", 0),
                tokens_output=data.get("usage", {}).get("output_tokens", 0),
                finish_reason=data.get("stop_reason", "unknown"),
                raw_response=data,
            )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")

        system = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        async with httpx.AsyncClient() as client:
            payload = {
                "model": model,
                "messages": chat_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            }

            if system:
                payload["system"] = system

            async with client.stream(
                "POST",
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=120.0,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data["type"] == "content_block_delta":
                                yield data["delta"].get("text", "")
                        except json.JSONDecodeError:
                            continue


class GoogleClient(BaseLLMClient):
    """Google Gemini API client."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def chat(
        self,
        messages: list[LLMMessage],
        model: str = "gemini-1.5-pro",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Google API key not configured")

        # Convert messages to Gemini format
        contents = []
        system_instruction = None

        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append(
                    {
                        "role": role,
                        "parts": [{"text": m.content}],
                    }
                )

        async with httpx.AsyncClient() as client:
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            }

            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            response = await client.post(
                f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()

            content = ""
            for candidate in data.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    content += part.get("text", "")

            usage = data.get("usageMetadata", {})

            return LLMResponse(
                content=content,
                model=model,
                tokens_input=usage.get("promptTokenCount", 0),
                tokens_output=usage.get("candidatesTokenCount", 0),
                finish_reason=data.get("candidates", [{}])[0].get("finishReason", "unknown"),
                raw_response=data,
            )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        model: str = "gemini-1.5-pro",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        # Google's streaming is more complex, implement as non-streaming for now
        response = await self.chat(messages, model, temperature, max_tokens)
        yield response.content


def get_llm_client(model: str, api_key: str | None = None) -> BaseLLMClient:
    """Get the appropriate LLM client based on model name."""
    if model.startswith("gpt-") or model.startswith("o1") or model.startswith("o3"):
        return OpenAIClient(api_key)
    elif model.startswith("claude-"):
        return AnthropicClient(api_key)
    elif model.startswith("gemini-"):
        return GoogleClient(api_key)
    else:
        # Default to OpenAI
        return OpenAIClient(api_key)
