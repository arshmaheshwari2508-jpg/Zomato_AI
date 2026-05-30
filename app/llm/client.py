"""LLM provider abstraction (Phase 3) — Groq API."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when LLM inference fails."""


class LLMClient(ABC):
    @abstractmethod
    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Return raw text completion from the model."""


class GroqClient(LLMClient):
    """Groq chat completions API (https://console.groq.com)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        import os
        raw_key = (
            api_key 
            or os.environ.get("LLM_API_KEY") 
            or os.environ.get("GROQ_API_KEY") 
            or settings.llm_api_key 
            or settings.groq_api_key
        )
        
        # Sanitize API key (strip quotes, whitespace, newlines)
        self._api_key = None
        if raw_key:
            self._api_key = str(raw_key).strip().strip("'").strip('"').strip()
            masked = self._api_key[:8] + "..." + self._api_key[-4:] if len(self._api_key) > 12 else "short"
            logger.info("Initializing GroqClient. API Key: %s | Length: %d", masked, len(self._api_key))

        self._model = model or settings.llm_model
        self._timeout = timeout or settings.llm_timeout_seconds
        if not self._api_key:
            raise LLMError("LLM_API_KEY or GROQ_API_KEY is not set")

    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        try:
            from groq import Groq
        except ImportError as exc:
            raise LLMError("groq package is not installed. Run: pip install groq") from exc

        client = Groq(api_key=self._api_key, timeout=self._timeout)
        temp = temperature if temperature is not None else settings.llm_temperature
        tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens

        try:
            response = client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
            )
        except Exception as exc:
            raise LLMError(str(exc)) from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMError("Empty response from Groq")
        return content.strip()


class MockLLMClient(LLMClient):
    """Deterministic client for tests and offline demos."""

    def __init__(self, response_text: Optional[str] = None) -> None:
        self._response_text = response_text

    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        if self._response_text is not None:
            return self._response_text

        user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return _build_mock_response_from_user_message(user_msg)


def _build_mock_response_from_user_message(user_content: str) -> str:
    """Generate valid JSON from candidate list embedded in the user prompt."""
    marker = '"restaurant_id":'
    if marker not in user_content:
        return json.dumps({"summary": "No candidates found.", "recommendations": []})

    start = user_content.find("[", user_content.find("Candidate restaurants"))
    if start < 0:
        return json.dumps({"summary": "No candidates.", "recommendations": []})

    depth = 0
    end = start
    for i, ch in enumerate(user_content[start:], start=start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    try:
        candidates = json.loads(user_content[start:end])
    except json.JSONDecodeError:
        candidates = []

    recommendations = []
    for rank, item in enumerate(candidates[:3], start=1):
        rid = item.get("restaurant_id", "")
        name = item.get("name", "Restaurant")
        recommendations.append(
            {
                "restaurant_id": rid,
                "rank": rank,
                "explanation": f"{name} matches your preferences with rating {item.get('rating', 'N/A')}.",
            }
        )

    summary = f"Top {len(recommendations)} picks based on your preferences."
    return json.dumps({"summary": summary, "recommendations": recommendations})


class RetryingLLMClient(LLMClient):
    """Wraps a client with one retry and exponential backoff on rate limits."""

    def __init__(self, client: LLMClient, max_retries: int = 1) -> None:
        self._client = client
        self._max_retries = max_retries

    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        last_error: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            try:
                return self._client.complete(messages, temperature, max_tokens)
            except LLMError as exc:
                last_error = exc
                msg = str(exc).lower()
                if attempt < self._max_retries and ("rate" in msg or "429" in msg or "timeout" in msg):
                    wait = 2**attempt
                    logger.warning("LLM retry in %ss after: %s", wait, exc)
                    time.sleep(wait)
                    continue
                raise
        raise LLMError(str(last_error))


def get_llm_client(provider: Optional[str] = None, use_mock: bool = False) -> LLMClient:
    """Factory: groq | mock."""
    if use_mock:
        return MockLLMClient()

    name = (provider or settings.llm_provider).lower().strip()
    if name == "mock":
        return MockLLMClient()
    if name == "groq":
        return RetryingLLMClient(GroqClient())
    raise LLMError(f"Unsupported LLM provider: {name}. Use 'groq' or 'mock'.")
