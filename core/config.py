"""Configuration helpers for Tait."""

from __future__ import annotations

import os
from dataclasses import dataclass
from ..config import CONFIG


DEFAULT_TOP_CODE = CONFIG["top_code"]
DEFAULT_TOP_TESTS = CONFIG["top_tests"]
DEFAULT_MAX_WORKERS = CONFIG["workers"]
DEFAULT_MAX_SEMANTIC_ROUNDS = CONFIG["rounds"]
DEFAULT_TIMEOUT = CONFIG["execution_timeout"]
DEFAULT_TEMPERATURE = CONFIG["temperature"]
DEFAULT_MAX_TOKENS = CONFIG["max_tokens"]
DEFAULT_LLM_PROVIDER = CONFIG["provider"]
DEFAULT_MODEL = CONFIG["model"]
DEFAULT_BASE_URL = CONFIG["base_url"]
DEFAULT_LLM_REQUEST_TIMEOUT = 300
DEFAULT_LLM_MAX_ATTEMPTS = 6
DEFAULT_LLM_BACKOFF_BASE = 15.0
DEFAULT_LLM_RATE_LIMIT_BACKOFF = 30.0


@dataclass
class LLMConfig:
    provider: str = DEFAULT_LLM_PROVIDER
    model: str = DEFAULT_MODEL
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS


def get_env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in ("", None) else default


def load_llm_config(
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> LLMConfig:
    """Load provider-specific OpenAI-compatible settings without logging secrets."""

    resolved_provider = str(
        provider or get_env("BRT_LLM_PROVIDER") or DEFAULT_LLM_PROVIDER
    ).strip().lower()
    if resolved_provider not in {"deepseek", "gpt"}:
        raise ValueError(
            f"unsupported LLM provider {resolved_provider!r}; expected deepseek or gpt"
        )

    if resolved_provider == "gpt":
        resolved_key = (
            api_key
            or get_env("GPT_API_KEY")
            or get_env("OPENAI_API_KEY")
            or get_env("API_KEY")
        )
        resolved_base = (
            base_url
            or get_env("GPT_BASE_URL")
            or get_env("OPENAI_BASE_URL")
            or get_env("OPENAI_API_BASE")
            or DEFAULT_BASE_URL
        )
        resolved_model = model or get_env("GPT_MODEL") or DEFAULT_MODEL
        return LLMConfig(
            provider=resolved_provider,
            model=resolved_model,
            api_key=resolved_key,
            base_url=resolved_base.rstrip("/") if resolved_base else None,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    resolved_key = (
        api_key
        or get_env("DEEPSEEK_API_KEY")
        or get_env("OPENAI_API_KEY")
        or get_env("API_KEY")
    )
    resolved_base = (
        base_url
        or get_env("DEEPSEEK_BASE_URL")
        or get_env("OPENAI_BASE_URL")
        or get_env("OPENAI_API_BASE")
        or DEFAULT_BASE_URL
    )
    resolved_model = model or get_env("DEEPSEEK_MODEL") or DEFAULT_MODEL
    return LLMConfig(
        provider=resolved_provider,
        model=resolved_model,
        api_key=resolved_key,
        base_url=resolved_base.rstrip("/") if resolved_base else None,
        temperature=temperature,
        max_tokens=max_tokens,
    )
