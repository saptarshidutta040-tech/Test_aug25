"""
engine/llm_client.py
─────────────────────
Provider-agnostic LLM client with retry + exponential backoff.

Supported providers:
  - grok   → xAI Grok via OpenAI-compatible API (https://api.x.ai/v1)
  - openai → OpenAI GPT models
  - gemini → Google Gemini models

Usage:
    client = get_llm_client()
    response = call_llm_with_retry(client, prompt)
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from config.settings import (
    LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    OPENAI_API_KEY, GEMINI_API_KEY, GROK_API_KEY, GROQ_API_KEY,
)

# xAI Grok OpenAI-compatible base URL (kept for future use)
GROK_BASE_URL = "https://api.x.ai/v1"


# ── Abstract base ─────────────────────────────────────────────────────────────

class BaseLLMClient(ABC):
    """All LLM providers implement this interface."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Send a prompt and return the model's text response."""


# ── Groq client (groq.com — fast open-source LLM inference) ──────────────────

class GroqClient(BaseLLMClient):
    """
    Groq client using the official groq Python SDK.
    Endpoint: https://api.groq.com/openai/v1
    Docs:     https://console.groq.com/docs
    Supported models: llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768
    """

    def __init__(self) -> None:
        from groq import Groq
        self.client = Groq(api_key=GROQ_API_KEY)

    def complete(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful and knowledgeable restaurant "
                        "recommendation assistant. Always base recommendations "
                        "strictly on the data provided."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()


# ── Grok client (xAI) ───────────────────────────────────────────────────────────────

class GrokClient(BaseLLMClient):
    """
    Grok client using xAI's OpenAI-compatible REST API.
    Endpoint: https://api.x.ai/v1
    Docs:     https://docs.x.ai/api
    """

    def __init__(self) -> None:
        from openai import OpenAI  # reuse openai SDK with custom base_url
        self.client = OpenAI(
            api_key=GROK_API_KEY,
            base_url=GROK_BASE_URL,
        )

    def complete(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful and knowledgeable restaurant "
                        "recommendation assistant. Always base recommendations "
                        "strictly on the data provided."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()


# ── OpenAI client ─────────────────────────────────────────────────────────────

class OpenAIClient(BaseLLMClient):
    """OpenAI GPT client."""

    def __init__(self) -> None:
        from openai import OpenAI
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def complete(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful restaurant recommendation assistant. "
                        "Always base recommendations strictly on the data provided."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()


# ── Gemini client ─────────────────────────────────────────────────────────────

class GeminiClient(BaseLLMClient):
    """Google Gemini client."""

    def __init__(self) -> None:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(LLM_MODEL)

    def complete(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text.strip()


# ── Factory ───────────────────────────────────────────────────────────────────

_PROVIDERS: dict[str, type[BaseLLMClient]] = {
    "groq":   GroqClient,
    "grok":   GrokClient,
    "openai": OpenAIClient,
    "gemini": GeminiClient,
}


def get_llm_client() -> BaseLLMClient:
    """
    Factory — returns the configured LLM client based on LLM_PROVIDER env var.

    Raises:
        ValueError: If LLM_PROVIDER is not one of the supported providers.
    """
    provider = LLM_PROVIDER.lower()
    cls = _PROVIDERS.get(provider)
    if not cls:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. "
            f"Choose from: {', '.join(_PROVIDERS)}"
        )
    return cls()


# ── Retry wrapper ─────────────────────────────────────────────────────────────

def call_llm_with_retry(
    client: BaseLLMClient,
    prompt: str,
    retries: int = 3,
) -> str:
    """
    Call the LLM with exponential backoff retry on failure.

    Args:
        client:  An instantiated BaseLLMClient.
        prompt:  The full prompt string to send.
        retries: Maximum number of attempts (default 3).

    Returns:
        LLM response text.

    Raises:
        Exception: Re-raises the last exception if all retries fail.
    """
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            response = client.complete(prompt)
            if not response.strip():
                raise ValueError("LLM returned an empty response.")
            return response

        except Exception as e:
            last_error = e
            wait = 2 ** (attempt - 1)  # 1s, 2s, 4s
            print(f"⚠️  LLM attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                print(f"   Retrying in {wait}s...")
                time.sleep(wait)

    raise last_error  # type: ignore[misc]
